"""
測試熔斷器模式
測試重點：
- 失敗閾值觸發熔斷
- 熔斷狀態拒絕請求
- 半開狀態測試恢復
- 成功重置熔斷器
"""

import pytest
import time
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import httpx
from app.utils.resilience import CircuitBreaker, CircuitBreakerOpen


class TestCircuitBreaker:
    """熔斷器模式測試"""

    def test_closed_state_allows_requests(self):
        """測試關閉狀態允許請求通過"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(return_value={"status": "ok"})

        for _ in range(5):
            result = breaker.call(mock_func)
            assert result == {"status": "ok"}

        assert breaker.state == "closed"
        assert mock_func.call_count == 5

    def test_failures_increment_counter(self):
        """測試失敗計數增加"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))

        # 前兩次失敗，仍然是關閉狀態
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.state == "closed"
        assert breaker.failure_count == 2

    def test_threshold_triggers_open_state(self):
        """測試達到閾值觸發開啟狀態"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))

        # 前三次失敗觸發熔斷
        for i in range(3):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.state == "open"
        assert breaker.failure_count == 3

        # 熔斷後拒絕請求
        with pytest.raises(CircuitBreakerOpen) as exc_info:
            breaker.call(mock_func)

        assert "is open" in str(exc_info.value)
        # 熔斷後不應該調用實際函數
        assert mock_func.call_count == 3

    def test_half_open_state_after_timeout(self):
        """測試超時後進入半開狀態"""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,  # 100ms
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))

        # 觸發熔斷
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.state == "open"

        # 等待恢復超時
        time.sleep(0.15)

        # 應該進入半開狀態並允許一次測試
        mock_func.side_effect = None
        mock_func.return_value = {"status": "ok"}

        result = breaker.call(mock_func)
        assert result == {"status": "ok"}
        assert breaker.state == "closed"  # 成功後回到關閉狀態
        assert breaker.failure_count == 0  # 重置失敗計數

    def test_half_open_failure_returns_to_open(self):
        """測試半開狀態失敗返回開啟狀態"""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))

        # 觸發熔斷
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.state == "open"

        # 等待恢復超時
        time.sleep(0.15)

        # 半開狀態測試失敗
        with pytest.raises(httpx.ConnectTimeout):
            breaker.call(mock_func)

        assert breaker.state == "open"  # 回到開啟狀態

        # 立即再試應該被拒絕
        with pytest.raises(CircuitBreakerOpen):
            breaker.call(mock_func)

    def test_success_resets_failure_counter(self):
        """測試成功調用重置失敗計數"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock()

        # 兩次失敗
        mock_func.side_effect = httpx.ConnectTimeout("Timeout")
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.failure_count == 2

        # 一次成功
        mock_func.side_effect = None
        mock_func.return_value = {"status": "ok"}
        result = breaker.call(mock_func)

        assert result == {"status": "ok"}
        assert breaker.failure_count == 0  # 計數被重置
        assert breaker.state == "closed"

    def test_multiple_circuit_breakers_isolated(self):
        """測試多個熔斷器相互隔離"""
        breaker1 = CircuitBreaker(
            name="service1",
            failure_threshold=2,
            recovery_timeout=1.0
        )

        breaker2 = CircuitBreaker(
            name="service2",
            failure_threshold=2,
            recovery_timeout=1.0
        )

        mock_func1 = Mock(side_effect=httpx.ConnectTimeout("Timeout"))
        mock_func2 = Mock(return_value={"status": "ok"})

        # breaker1 失敗並熔斷
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker1.call(mock_func1)

        assert breaker1.state == "open"

        # breaker2 仍然正常工作
        result = breaker2.call(mock_func2)
        assert result == {"status": "ok"}
        assert breaker2.state == "closed"

    def test_custom_failure_predicate(self):
        """測試自定義失敗判斷"""
        def is_failure(result, exception):
            if exception:
                return True
            # 自定義：status != "ok" 也算失敗
            return result.get("status") != "ok"

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=1.0,
            failure_predicate=is_failure
        )

        mock_func = Mock(return_value={"status": "error"})

        # 返回錯誤狀態應該計為失敗
        for i in range(2):
            result = breaker.call(mock_func)
            assert result == {"status": "error"}

        assert breaker.state == "open"

    def test_statistics_tracking(self):
        """測試統計數據追蹤"""
        breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock()

        # 混合成功和失敗
        mock_func.return_value = {"status": "ok"}
        breaker.call(mock_func)

        mock_func.side_effect = httpx.ConnectTimeout("Timeout")
        with pytest.raises(httpx.ConnectTimeout):
            breaker.call(mock_func)

        mock_func.side_effect = None
        breaker.call(mock_func)

        stats = breaker.get_statistics()
        assert stats["total_calls"] == 3
        assert stats["success_count"] == 2
        assert stats["failure_count"] == 1
        assert stats["success_rate"] == 2/3

    def test_fallback_function(self):
        """測試降級函數"""
        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=5.0,
            expected_exception=httpx.HTTPError
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))
        fallback_func = Mock(return_value={"status": "fallback"})

        # 觸發熔斷
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert breaker.state == "open"

        # 熔斷後使用降級函數
        result = breaker.call(mock_func, fallback=fallback_func)
        assert result == {"status": "fallback"}
        assert fallback_func.call_count == 1

    def test_state_change_callbacks(self):
        """測試狀態變更回調"""
        state_changes = []

        def on_state_change(old_state, new_state):
            state_changes.append((old_state, new_state))

        breaker = CircuitBreaker(
            failure_threshold=2,
            recovery_timeout=0.1,
            expected_exception=httpx.HTTPError,
            on_state_change=on_state_change
        )

        mock_func = Mock(side_effect=httpx.ConnectTimeout("Timeout"))

        # 觸發熔斷：closed -> open
        for i in range(2):
            with pytest.raises(httpx.ConnectTimeout):
                breaker.call(mock_func)

        assert ("closed", "open") in state_changes

        # 等待並測試恢復：open -> half_open -> closed
        time.sleep(0.15)
        mock_func.side_effect = None
        mock_func.return_value = {"status": "ok"}
        breaker.call(mock_func)

        assert ("open", "half_open") in state_changes
        assert ("half_open", "closed") in state_changes