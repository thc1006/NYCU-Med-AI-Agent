"""
韌性模式實作
包含指數退避、熔斷器、降級等模式
"""

import time
import random
import logging
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = False,
    retry_condition: Optional[Callable[[Exception], bool]] = None,
    on_retry: Optional[Callable[[int, float, Exception], None]] = None
) -> Any:
    """
    指數退避重試機制

    Args:
        func: 要執行的函數
        max_retries: 最大重試次數
        base_delay: 基礎延遲（秒）
        max_delay: 最大延遲（秒）
        jitter: 是否加入隨機抖動
        retry_condition: 自定義重試條件
        on_retry: 重試回調函數

    Returns:
        函數執行結果

    Raises:
        最後一次執行的例外
    """
    def should_retry(exception: Exception) -> bool:
        if retry_condition:
            return retry_condition(exception)

        # 預設：429 和 5xx 錯誤重試
        if isinstance(exception, httpx.HTTPStatusError):
            return exception.response.status_code in [429, 502, 503, 504]
        elif isinstance(exception, (httpx.ConnectTimeout, httpx.ReadTimeout)):
            return True
        return False

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_exception = e

            if attempt == max_retries:
                # 最後一次嘗試失敗
                raise e

            if not should_retry(e):
                # 不可重試的錯誤
                raise e

            # 計算延遲
            delay = min(base_delay * (2 ** attempt), max_delay)

            if jitter:
                # 加入隨機抖動 [0.5 * delay, 1.5 * delay]
                delay = delay * (0.5 + random.random())

            if on_retry:
                on_retry(attempt + 1, delay, e)

            logger.warning(f"Retry attempt {attempt + 1}/{max_retries} after {delay:.2f}s: {str(e)}")
            time.sleep(delay)

    raise last_exception


class CircuitBreakerState(Enum):
    """熔斷器狀態"""
    CLOSED = "closed"       # 關閉（正常）
    OPEN = "open"          # 開啟（熔斷）
    HALF_OPEN = "half_open"  # 半開（測試恢復）


class CircuitBreakerOpen(Exception):
    """熔斷器開啟例外"""
    pass


class CircuitBreaker:
    """
    熔斷器模式實作
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
        failure_predicate: Optional[Callable[[Any, Optional[Exception]], bool]] = None,
        on_state_change: Optional[Callable[[str, str], None]] = None
    ):
        """
        初始化熔斷器

        Args:
            name: 熔斷器名稱
            failure_threshold: 失敗閾值
            recovery_timeout: 恢復超時（秒）
            expected_exception: 預期的例外類型
            failure_predicate: 自定義失敗判斷
            on_state_change: 狀態變更回調
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_predicate = failure_predicate
        self.on_state_change = on_state_change

        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._success_count = 0
        self._total_calls = 0
        self._total_failures = 0  # Track total failures for statistics

    @property
    def state(self) -> str:
        """獲取當前狀態"""
        self._check_state()
        return self._state.value

    @property
    def failure_count(self) -> int:
        """獲取失敗計數"""
        return self._failure_count

    def _check_state(self):
        """檢查並更新狀態"""
        if self._state == CircuitBreakerState.OPEN:
            if self._last_failure_time:
                time_since_failure = time.time() - self._last_failure_time
                if time_since_failure >= self.recovery_timeout:
                    self._transition_to(CircuitBreakerState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitBreakerState):
        """狀態轉換"""
        old_state = self._state.value
        self._state = new_state

        if self.on_state_change and old_state != new_state.value:
            self.on_state_change(old_state, new_state.value)

        logger.info(f"Circuit breaker '{self.name}' transitioned from {old_state} to {new_state.value}")

    def _is_failure(self, result: Any, exception: Optional[Exception]) -> bool:
        """判斷是否為失敗"""
        if self.failure_predicate:
            return self.failure_predicate(result, exception)
        return exception is not None

    def _record_success(self):
        """記錄成功"""
        self._success_count += 1
        self._failure_count = 0

        if self._state == CircuitBreakerState.HALF_OPEN:
            self._transition_to(CircuitBreakerState.CLOSED)

    def _record_failure(self):
        """記錄失敗"""
        self._failure_count += 1
        self._total_failures += 1  # Track total failures
        self._last_failure_time = time.time()

        if self._failure_count >= self.failure_threshold:
            self._transition_to(CircuitBreakerState.OPEN)
        elif self._state == CircuitBreakerState.HALF_OPEN:
            self._transition_to(CircuitBreakerState.OPEN)

    def call(self, func: Callable, fallback: Optional[Callable] = None) -> Any:
        """
        通過熔斷器調用函數

        Args:
            func: 要執行的函數
            fallback: 降級函數

        Returns:
            函數執行結果

        Raises:
            CircuitBreakerOpen: 熔斷器開啟時
        """
        self._check_state()
        self._total_calls += 1

        if self._state == CircuitBreakerState.OPEN:
            if fallback:
                return fallback()
            raise CircuitBreakerOpen(f"Circuit breaker '{self.name}' is open")

        exception = None
        result = None

        try:
            result = func()
        except self.expected_exception as e:
            exception = e

        # 使用自定義判斷或預設判斷
        if self._is_failure(result, exception):
            self._record_failure()
            if exception:
                if fallback and self._state == CircuitBreakerState.OPEN:
                    return fallback()
                raise exception
            # 沒有異常但被判定為失敗
            if fallback and self._state == CircuitBreakerState.OPEN:
                return fallback()
        else:
            self._record_success()

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資訊"""
        success_rate = self._success_count / self._total_calls if self._total_calls > 0 else 0

        return {
            "name": self.name,
            "state": self.state,
            "total_calls": self._total_calls,
            "success_count": self._success_count,
            "failure_count": self._total_failures,  # Use total failures
            "success_rate": success_rate,
            "last_failure_time": self._last_failure_time
        }


class RateLimiter:
    """
    速率限制器
    """

    def __init__(
        self,
        max_requests: int = 60,
        window_seconds: int = 60,
        sliding_window: bool = False,
        burst_size: Optional[int] = None,
        burst_window: Optional[int] = None,
        whitelist: Optional[List[str]] = None,
        endpoint_limits: Optional[Dict[str, Dict]] = None,
        default_max_requests: Optional[int] = None,
        tier_limits: Optional[Dict[str, Dict]] = None,
        key_func: Optional[Callable] = None,
        cleanup_interval: int = 300
    ):
        """
        初始化速率限制器

        Args:
            max_requests: 時間窗口內最大請求數
            window_seconds: 時間窗口（秒）
            sliding_window: 是否使用滑動窗口
            burst_size: 突發大小限制
            burst_window: 突發窗口（秒）
            whitelist: 白名單列表
            endpoint_limits: 端點特定限制
            default_max_requests: 預設最大請求數
            tier_limits: 用戶層級限制
            key_func: 自定義鍵函數
            cleanup_interval: 清理間隔（秒）
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.sliding_window = sliding_window
        self.burst_size = burst_size
        self.burst_window = burst_window
        self.whitelist = whitelist or []
        self.endpoint_limits = endpoint_limits or {}
        self.default_max_requests = default_max_requests or max_requests
        self.tier_limits = tier_limits or {}
        self.key_func = key_func
        self.cleanup_interval = cleanup_interval

        self._request_history = {}
        self._last_cleanup = time.time()

    def _get_key(self, client_id: str, endpoint: Optional[str] = None) -> str:
        """生成限流鍵"""
        if endpoint:
            return f"{client_id}:{endpoint}"
        return client_id

    def check_rate_limit(self, client_id: str, endpoint: Optional[str] = None) -> bool:
        """
        檢查速率限制

        Args:
            client_id: 客戶端ID（通常是IP）
            endpoint: 端點路徑

        Returns:
            是否允許請求
        """
        # 白名單檢查
        if client_id in self.whitelist:
            return True

        # 清理過期記錄
        self._cleanup_if_needed()

        # 獲取限制設定
        if endpoint and endpoint in self.endpoint_limits:
            limit_config = self.endpoint_limits[endpoint]
            max_req = limit_config.get("max_requests", self.max_requests)
            window = limit_config.get("window", self.window_seconds)
        else:
            max_req = self.max_requests
            window = self.window_seconds

        key = self._get_key(client_id, endpoint)
        current_time = time.time()

        if key not in self._request_history:
            self._request_history[key] = []

        # 清理過期請求
        if self.sliding_window:
            self._request_history[key] = [
                t for t in self._request_history[key]
                if current_time - t < window
            ]
        else:
            # 固定窗口
            if self._request_history[key] and current_time - self._request_history[key][0] >= window:
                self._request_history[key] = []

        # 檢查突發限制
        if self.burst_size and self.burst_window:
            recent_requests = [
                t for t in self._request_history[key]
                if current_time - t < self.burst_window
            ]
            if len(recent_requests) >= self.burst_size:
                return False

        # 檢查總限制
        if len(self._request_history[key]) >= max_req:
            return False

        # 記錄請求
        self._request_history[key].append(current_time)
        return True

    def check_rate_limit_request(self, request) -> bool:
        """檢查請求物件的速率限制"""
        if self.key_func:
            key = self.key_func(request)
        else:
            key = request.client_ip

        return self.check_rate_limit(key)

    def check_rate_limit_user(self, user) -> bool:
        """檢查用戶層級速率限制"""
        tier = getattr(user, 'tier', 'free')

        if tier in self.tier_limits:
            config = self.tier_limits[tier]
            max_req = config.get("max_requests", self.max_requests)
            window = config.get("window", self.window_seconds)

            # 臨時設定限制
            old_max = self.max_requests
            old_window = self.window_seconds
            self.max_requests = max_req
            self.window_seconds = window

            result = self.check_rate_limit(user.id)

            # 恢復設定
            self.max_requests = old_max
            self.window_seconds = old_window

            return result

        return self.check_rate_limit(user.id)

    def get_retry_after(self, client_id: str, endpoint: Optional[str] = None) -> int:
        """獲取重試時間（秒）"""
        key = self._get_key(client_id, endpoint)

        if key not in self._request_history or not self._request_history[key]:
            return 0

        oldest_request = min(self._request_history[key])
        time_elapsed = time.time() - oldest_request

        if endpoint and endpoint in self.endpoint_limits:
            window = self.endpoint_limits[endpoint].get("window", self.window_seconds)
        else:
            window = self.window_seconds

        retry_after = max(0, int(window - time_elapsed))
        return retry_after

    def cleanup_expired(self):
        """清理過期記錄"""
        current_time = time.time()
        keys_to_delete = []

        for key, timestamps in self._request_history.items():
            # 保留最近的記錄
            self._request_history[key] = [
                t for t in timestamps
                if current_time - t < self.window_seconds * 2  # 保留2倍窗口時間
            ]

            if not self._request_history[key]:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._request_history[key]

        self._last_cleanup = current_time

    def _cleanup_if_needed(self):
        """按需清理"""
        if time.time() - self._last_cleanup > self.cleanup_interval:
            self.cleanup_expired()