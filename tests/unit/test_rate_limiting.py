"""
測試 API 速率限制中介層
測試重點：
- 請求速率限制（每分鐘/每小時）
- IP 基礎限流
- 端點差異化限流
- 429 回應與 Retry-After 標頭
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.middlewares.rate_limit import RateLimitMiddleware, RateLimiter


class TestRateLimiting:
    """API 速率限制測試"""

    def test_rate_limiter_basic_functionality(self):
        """測試基本速率限制功能"""
        limiter = RateLimiter(
            max_requests=3,
            window_seconds=1
        )

        client_id = "test_client"

        # 前三次應該通過
        for i in range(3):
            allowed = limiter.check_rate_limit(client_id)
            assert allowed == True

        # 第四次應該被拒絕
        allowed = limiter.check_rate_limit(client_id)
        assert allowed == False

        # 等待時間窗口過期
        time.sleep(1.1)

        # 應該可以再次請求
        allowed = limiter.check_rate_limit(client_id)
        assert allowed == True

    def test_sliding_window_rate_limit(self):
        """測試滑動窗口速率限制"""
        limiter = RateLimiter(
            max_requests=5,
            window_seconds=2,
            sliding_window=True
        )

        client_id = "test_client"

        # 快速發送5個請求
        for i in range(5):
            assert limiter.check_rate_limit(client_id) == True
            time.sleep(0.1)

        # 第6個應該被拒絕
        assert limiter.check_rate_limit(client_id) == False

        # 等待部分請求過期
        time.sleep(1.0)

        # 應該允許一些新請求（舊請求開始過期）
        allowed_count = 0
        for i in range(3):
            if limiter.check_rate_limit(client_id):
                allowed_count += 1
            time.sleep(0.1)

        assert allowed_count > 0

    def test_per_ip_rate_limiting(self):
        """測試基於 IP 的速率限制"""
        limiter = RateLimiter(
            max_requests=2,
            window_seconds=1
        )

        # 不同 IP 有獨立限制
        assert limiter.check_rate_limit("192.168.1.1") == True
        assert limiter.check_rate_limit("192.168.1.1") == True
        assert limiter.check_rate_limit("192.168.1.1") == False  # IP1 達到限制

        # IP2 仍可請求
        assert limiter.check_rate_limit("192.168.1.2") == True
        assert limiter.check_rate_limit("192.168.1.2") == True
        assert limiter.check_rate_limit("192.168.1.2") == False  # IP2 達到限制

    def test_endpoint_specific_limits(self):
        """測試端點特定限制"""
        limiter = RateLimiter(
            default_max_requests=10,
            window_seconds=60,
            endpoint_limits={
                "/v1/triage": {"max_requests": 30, "window": 60},  # 症狀分級較寬鬆
                "/v1/hospitals/nearby": {"max_requests": 5, "window": 60},  # 地圖查詢較嚴格
            }
        )

        client_id = "test_client"

        # 測試不同端點的限制
        for i in range(5):
            assert limiter.check_rate_limit(client_id, "/v1/hospitals/nearby") == True

        assert limiter.check_rate_limit(client_id, "/v1/hospitals/nearby") == False

        # 其他端點不受影響
        for i in range(10):
            assert limiter.check_rate_limit(client_id, "/v1/triage") == True

    def test_rate_limit_middleware(self):
        """測試速率限制中介層"""
        client = TestClient(app)

        # 配置測試用限制
        with patch.object(RateLimitMiddleware, 'rate_limiter',
                         RateLimiter(max_requests=3, window_seconds=1)):

            # 前三次請求應該成功
            for i in range(3):
                response = client.get("/healthz")
                assert response.status_code == 200

            # 第四次應該返回 429
            response = client.get("/healthz")
            assert response.status_code == 429
            assert response.json()["detail"] == "請求過於頻繁，請稍後再試"
            assert "Retry-After" in response.headers

    def test_retry_after_header(self):
        """測試 Retry-After 標頭"""
        limiter = RateLimiter(
            max_requests=1,
            window_seconds=5
        )

        client_id = "test_client"

        # 第一次請求
        assert limiter.check_rate_limit(client_id) == True

        # 第二次被拒絕
        assert limiter.check_rate_limit(client_id) == False

        # 獲取重試時間
        retry_after = limiter.get_retry_after(client_id)
        assert 4 <= retry_after <= 5  # 應該接近窗口剩餘時間

    def test_burst_protection(self):
        """測試突發流量保護"""
        limiter = RateLimiter(
            max_requests=10,
            window_seconds=60,
            burst_size=3,  # 突發限制
            burst_window=1  # 1秒內最多3個
        )

        client_id = "test_client"

        # 1秒內快速發送
        start = time.time()
        allowed_in_burst = 0

        while time.time() - start < 0.5:
            if limiter.check_rate_limit(client_id):
                allowed_in_burst += 1

        # 不應超過突發限制
        assert allowed_in_burst <= 3

    def test_whitelist_bypass(self):
        """測試白名單繞過限制"""
        limiter = RateLimiter(
            max_requests=1,
            window_seconds=60,
            whitelist=["127.0.0.1", "::1", "192.168.1.100"]
        )

        # 白名單 IP 不受限制
        for i in range(10):
            assert limiter.check_rate_limit("127.0.0.1") == True

        # 非白名單 IP 受限制
        assert limiter.check_rate_limit("192.168.1.50") == True
        assert limiter.check_rate_limit("192.168.1.50") == False

    @pytest.mark.skip(reason="Redis not installed in test environment")
    def test_distributed_rate_limiting(self):
        """測試分散式速率限制（使用 Redis）"""
        from app.utils.redis_rate_limiter import RedisRateLimiter

        with patch('redis.Redis') as mock_redis:
            mock_redis_instance = Mock()
            mock_redis.return_value = mock_redis_instance

            # 模擬 Redis 操作
            mock_redis_instance.incr.return_value = 1
            mock_redis_instance.expire.return_value = True
            mock_redis_instance.ttl.return_value = 50

            limiter = RedisRateLimiter(
                redis_client=mock_redis_instance,
                max_requests=100,
                window_seconds=60
            )

            client_id = "test_client"

            # 第一次請求
            allowed = limiter.check_rate_limit(client_id)
            assert allowed == True

            # 驗證 Redis 調用
            mock_redis_instance.incr.assert_called()
            mock_redis_instance.expire.assert_called()

    def test_rate_limit_headers_in_response(self):
        """測試回應中的速率限制標頭"""
        client = TestClient(app)

        response = client.get("/healthz")

        # 應該包含速率限制資訊
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])

        assert limit > 0
        assert remaining >= 0
        assert remaining < limit

    def test_custom_rate_limit_key(self):
        """測試自定義速率限制鍵"""
        limiter = RateLimiter(
            max_requests=5,
            window_seconds=60,
            key_func=lambda request: f"{request.client_ip}:{request.user_agent}"
        )

        # 相同 IP 但不同 User-Agent 有獨立限制
        request1 = Mock(client_ip="192.168.1.1", user_agent="Chrome")
        request2 = Mock(client_ip="192.168.1.1", user_agent="Firefox")

        for i in range(5):
            assert limiter.check_rate_limit_request(request1) == True

        assert limiter.check_rate_limit_request(request1) == False  # Chrome 達到限制
        assert limiter.check_rate_limit_request(request2) == True   # Firefox 仍可請求

    def test_rate_limit_with_user_tiers(self):
        """測試用戶層級差異化限流"""
        limiter = RateLimiter(
            default_max_requests=10,
            window_seconds=60,
            tier_limits={
                "free": {"max_requests": 10, "window": 60},
                "premium": {"max_requests": 100, "window": 60},
                "enterprise": {"max_requests": 1000, "window": 60}
            }
        )

        # 免費用戶
        free_user = Mock(tier="free", id="user1")
        for i in range(10):
            assert limiter.check_rate_limit_user(free_user) == True
        assert limiter.check_rate_limit_user(free_user) == False

        # 付費用戶有更高限制
        premium_user = Mock(tier="premium", id="user2")
        for i in range(50):
            assert limiter.check_rate_limit_user(premium_user) == True

    def test_cleanup_expired_records(self):
        """測試過期記錄清理"""
        limiter = RateLimiter(
            max_requests=5,
            window_seconds=1,
            cleanup_interval=2  # 每2秒清理
        )

        # 添加一些請求記錄
        for i in range(3):
            limiter.check_rate_limit(f"client_{i}")

        initial_size = len(limiter._request_history)
        assert initial_size > 0

        # 等待過期並觸發清理
        time.sleep(3)
        limiter.cleanup_expired()

        # 過期記錄應該被清理
        assert len(limiter._request_history) < initial_size