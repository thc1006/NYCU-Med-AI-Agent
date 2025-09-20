"""
速率限制中介軟體單元測試
測試範圍：
- 基本速率限制功能
- 端點特定限制
- IP白名單功能
- 429錯誤回應
- 速率限制標頭
- 重試時間計算
- 客戶端IP處理
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.testclient import TestClient
from fastapi.applications import FastAPI
from starlette.responses import JSONResponse
import time

from app.middlewares.rate_limit import RateLimitMiddleware
from app.utils.resilience import RateLimiter


class TestRateLimitMiddleware:
    """速率限制中介軟體測試類別"""

    @pytest.fixture
    def app(self):
        """FastAPI應用程式"""
        return FastAPI()

    @pytest.fixture
    def mock_rate_limiter(self):
        """模擬速率限制器"""
        limiter = Mock(spec=RateLimiter)
        limiter.max_requests = 60
        limiter.window_seconds = 60
        limiter.endpoint_limits = {
            "/v1/triage": {"max_requests": 30, "window": 60},
            "/v1/hospitals/nearby": {"max_requests": 10, "window": 60},
            "/v1/triage/quick": {"max_requests": 60, "window": 60}
        }
        limiter._request_history = {}
        return limiter

    @pytest.fixture
    def rate_limit_middleware(self, app, mock_rate_limiter):
        """速率限制中介軟體實例"""
        with patch('app.middlewares.rate_limit.RateLimiter', return_value=mock_rate_limiter):
            middleware = RateLimitMiddleware(app)
            middleware.rate_limiter = mock_rate_limiter
            return middleware

    @pytest.fixture
    def mock_request(self):
        """模擬HTTP請求"""
        request = Mock(spec=Request)
        request.url.path = "/v1/triage"
        request.client.host = "192.168.1.100"
        return request

    @pytest.fixture
    def mock_response(self):
        """模擬HTTP回應"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response

    @pytest.mark.asyncio
    async def test_rate_limit_allowed(self, rate_limit_middleware, mock_request, mock_response):
        """測試速率限制允許的請求"""
        # 設定速率限制器允許請求
        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = True

        async def mock_call_next(request):
            return mock_response

        # 執行中介軟體
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        # 驗證請求被允許
        assert response == mock_response

        # 驗證速率限制檢查被調用
        rate_limit_middleware.rate_limiter.check_rate_limit.assert_called_once_with(
            "192.168.1.100", "/v1/triage"
        )

        # 驗證速率限制標頭被添加
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, rate_limit_middleware, mock_request):
        """測試速率限制超出"""
        # 設定速率限制器拒絕請求
        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = False
        rate_limit_middleware.rate_limiter.get_retry_after.return_value = 30

        async def mock_call_next(request):
            return Mock(spec=Response)

        # 執行中介軟體
        response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        # 驗證返回429錯誤
        assert isinstance(response, JSONResponse)

        # 驗證錯誤內容
        content = response.body.decode()
        assert "請求過於頻繁" in content
        assert "rate_limit_exceeded" in content

        # 驗證重試標頭
        assert response.headers["Retry-After"] == "30"
        assert "X-RateLimit-Limit" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert response.headers["X-RateLimit-Reset"] == "30"

    @pytest.mark.asyncio
    async def test_different_endpoints_different_limits(self, rate_limit_middleware, mock_response):
        """測試不同端點的不同限制"""
        # 測試 /v1/triage 端點
        triage_request = Mock(spec=Request)
        triage_request.url.path = "/v1/triage"
        triage_request.client.host = "192.168.1.100"

        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = True

        async def mock_call_next(request):
            return mock_response

        await rate_limit_middleware.dispatch(triage_request, mock_call_next)

        # 驗證使用正確的端點路徑
        rate_limit_middleware.rate_limiter.check_rate_limit.assert_called_with(
            "192.168.1.100", "/v1/triage"
        )

        # 測試 /v1/hospitals/nearby 端點
        hospitals_request = Mock(spec=Request)
        hospitals_request.url.path = "/v1/hospitals/nearby"
        hospitals_request.client.host = "192.168.1.100"

        rate_limit_middleware.rate_limiter.check_rate_limit.reset_mock()
        await rate_limit_middleware.dispatch(hospitals_request, mock_call_next)

        rate_limit_middleware.rate_limiter.check_rate_limit.assert_called_with(
            "192.168.1.100", "/v1/hospitals/nearby"
        )

    @pytest.mark.asyncio
    async def test_client_ip_extraction(self, rate_limit_middleware, mock_response):
        """測試客戶端IP提取"""
        # 正常情況
        request_with_client = Mock(spec=Request)
        request_with_client.url.path = "/v1/test"
        request_with_client.client.host = "203.75.15.20"

        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = True

        async def mock_call_next(request):
            return mock_response

        await rate_limit_middleware.dispatch(request_with_client, mock_call_next)

        rate_limit_middleware.rate_limiter.check_rate_limit.assert_called_with(
            "203.75.15.20", "/v1/test"
        )

        # 無client資訊情況
        request_no_client = Mock(spec=Request)
        request_no_client.url.path = "/v1/test"
        request_no_client.client = None

        rate_limit_middleware.rate_limiter.check_rate_limit.reset_mock()
        await rate_limit_middleware.dispatch(request_no_client, mock_call_next)

        rate_limit_middleware.rate_limiter.check_rate_limit.assert_called_with(
            "unknown", "/v1/test"
        )

    def test_calculate_remaining_with_endpoint_limit(self, rate_limit_middleware):
        """測試有端點特定限制的剩餘計算"""
        client_ip = "192.168.1.100"
        endpoint = "/v1/triage"

        # 模擬_get_key方法
        rate_limit_middleware.rate_limiter._get_key.return_value = f"{client_ip}:{endpoint}"

        # 模擬請求歷史（已使用5個請求）
        rate_limit_middleware.rate_limiter._request_history = {
            f"{client_ip}:{endpoint}": [time.time()] * 5
        }

        remaining = rate_limit_middleware._calculate_remaining(client_ip, endpoint)

        # /v1/triage 的限制是30，已使用5個，剩餘25個
        assert remaining == 25

    def test_calculate_remaining_with_default_limit(self, rate_limit_middleware):
        """測試使用預設限制的剩餘計算"""
        client_ip = "192.168.1.100"
        endpoint = "/v1/unknown"  # 不在endpoint_limits中的端點

        rate_limit_middleware.rate_limiter._get_key.return_value = f"{client_ip}:{endpoint}"

        # 模擬請求歷史（已使用10個請求）
        rate_limit_middleware.rate_limiter._request_history = {
            f"{client_ip}:{endpoint}": [time.time()] * 10
        }

        remaining = rate_limit_middleware._calculate_remaining(client_ip, endpoint)

        # 預設限制是60，已使用10個，剩餘50個
        assert remaining == 50

    def test_calculate_remaining_no_history(self, rate_limit_middleware):
        """測試無請求歷史的剩餘計算"""
        client_ip = "192.168.1.100"
        endpoint = "/v1/triage"

        rate_limit_middleware.rate_limiter._get_key.return_value = f"{client_ip}:{endpoint}"
        rate_limit_middleware.rate_limiter._request_history = {}

        remaining = rate_limit_middleware._calculate_remaining(client_ip, endpoint)

        # 無歷史記錄，返回最大限制
        assert remaining == 30  # /v1/triage的限制

    def test_calculate_remaining_zero_remaining(self, rate_limit_middleware):
        """測試剩餘數量為零的情況"""
        client_ip = "192.168.1.100"
        endpoint = "/v1/hospitals/nearby"  # 限制為10

        rate_limit_middleware.rate_limiter._get_key.return_value = f"{client_ip}:{endpoint}"

        # 模擬已使用15個請求（超過限制）
        rate_limit_middleware.rate_limiter._request_history = {
            f"{client_ip}:{endpoint}": [time.time()] * 15
        }

        remaining = rate_limit_middleware._calculate_remaining(client_ip, endpoint)

        # 超過限制時返回0
        assert remaining == 0

    @patch('app.middlewares.rate_limit.logger')
    @pytest.mark.asyncio
    async def test_rate_limit_logging(self, mock_logger, rate_limit_middleware, mock_request):
        """測試速率限制日誌記錄"""
        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = False
        rate_limit_middleware.rate_limiter.get_retry_after.return_value = 60

        async def mock_call_next(request):
            return Mock(spec=Response)

        await rate_limit_middleware.dispatch(mock_request, mock_call_next)

        # 驗證警告日誌被記錄
        mock_logger.warning.assert_called_once()
        log_message = mock_logger.warning.call_args[0][0]
        assert "Rate limit exceeded" in log_message
        assert "192.168.1.100" in log_message
        assert "/v1/triage" in log_message

    @pytest.mark.asyncio
    async def test_response_headers_content(self, rate_limit_middleware, mock_request, mock_response):
        """測試回應標頭內容"""
        rate_limit_middleware.rate_limiter.check_rate_limit.return_value = True

        # 模擬計算剩餘數量
        with patch.object(rate_limit_middleware, '_calculate_remaining', return_value=25):
            async def mock_call_next(request):
                return mock_response

            response = await rate_limit_middleware.dispatch(mock_request, mock_call_next)

            # 驗證標頭值
            assert response.headers["X-RateLimit-Limit"] == "60"
            assert response.headers["X-RateLimit-Remaining"] == "25"
            assert response.headers["X-RateLimit-Reset"] == "60"

    @patch('app.middlewares.rate_limit.get_settings')
    def test_middleware_initialization(self, mock_get_settings, app):
        """測試中介軟體初始化"""
        # 模擬設定
        mock_settings = Mock()
        mock_settings.rate_limit_requests = 100
        mock_settings.rate_limit_window = 120
        mock_settings.rate_limit_whitelist = ["127.0.0.1", "10.0.0.1"]
        mock_get_settings.return_value = mock_settings

        with patch('app.middlewares.rate_limit.RateLimiter') as mock_rate_limiter_class:
            # 重置類別屬性以測試初始化
            RateLimitMiddleware.rate_limiter = None

            middleware = RateLimitMiddleware(app)

            # 驗證RateLimiter被正確初始化
            mock_rate_limiter_class.assert_called_once_with(
                max_requests=100,
                window_seconds=120,
                endpoint_limits={
                    "/v1/triage": {"max_requests": 30, "window": 60},
                    "/v1/hospitals/nearby": {"max_requests": 10, "window": 60},
                    "/v1/triage/quick": {"max_requests": 60, "window": 60}
                },
                whitelist=["127.0.0.1", "10.0.0.1"]
            )

    @patch('app.middlewares.rate_limit.get_settings')
    def test_middleware_initialization_with_defaults(self, mock_get_settings, app):
        """測試使用預設值的中介軟體初始化"""
        # 模擬沒有速率限制設定的情況
        mock_settings = Mock()
        # 不設定rate_limit相關屬性，測試預設值
        del mock_settings.rate_limit_requests
        del mock_settings.rate_limit_window
        del mock_settings.rate_limit_whitelist
        mock_get_settings.return_value = mock_settings

        with patch('app.middlewares.rate_limit.RateLimiter') as mock_rate_limiter_class:
            RateLimitMiddleware.rate_limiter = None

            middleware = RateLimitMiddleware(app)

            # 驗證使用預設值
            mock_rate_limiter_class.assert_called_once_with(
                max_requests=60,  # 預設值
                window_seconds=60,  # 預設值
                endpoint_limits={
                    "/v1/triage": {"max_requests": 30, "window": 60},
                    "/v1/hospitals/nearby": {"max_requests": 10, "window": 60},
                    "/v1/triage/quick": {"max_requests": 60, "window": 60}
                },
                whitelist=["127.0.0.1", "::1"]  # 預設值
            )

    def test_singleton_rate_limiter(self, app):
        """測試速率限制器單例模式"""
        with patch('app.middlewares.rate_limit.RateLimiter') as mock_rate_limiter_class:
            mock_limiter = Mock()
            mock_rate_limiter_class.return_value = mock_limiter

            # 重置類別屬性
            RateLimitMiddleware.rate_limiter = None

            # 創建第一個中介軟體實例
            middleware1 = RateLimitMiddleware(app)
            assert RateLimitMiddleware.rate_limiter == mock_limiter

            # 創建第二個中介軟體實例
            middleware2 = RateLimitMiddleware(app)

            # 驗證RateLimiter只被初始化一次
            mock_rate_limiter_class.assert_called_once()

            # 驗證兩個實例使用同一個rate_limiter
            assert middleware1.rate_limiter == middleware2.rate_limiter