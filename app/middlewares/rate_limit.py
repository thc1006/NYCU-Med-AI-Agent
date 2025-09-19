"""
API 速率限制中介層
提供請求速率控制與防濫用保護
"""

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.resilience import RateLimiter
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中介層"""

    # 類別屬性，所有實例共享
    rate_limiter = None

    def __init__(self, app):
        super().__init__(app)

        # 初始化速率限制器（只初始化一次）
        if RateLimitMiddleware.rate_limiter is None:
            settings = get_settings()
            RateLimitMiddleware.rate_limiter = RateLimiter(
                max_requests=getattr(settings, 'rate_limit_requests', 60),
                window_seconds=getattr(settings, 'rate_limit_window', 60),
                endpoint_limits={
                    "/v1/triage": {"max_requests": 30, "window": 60},
                    "/v1/hospitals/nearby": {"max_requests": 10, "window": 60},
                    "/v1/triage/quick": {"max_requests": 60, "window": 60}
                },
                whitelist=getattr(settings, 'rate_limit_whitelist', ["127.0.0.1", "::1"])
            )

    async def dispatch(self, request: Request, call_next):
        """處理請求"""
        # 獲取客戶端 IP
        client_ip = request.client.host if request.client else "unknown"

        # 獲取端點路徑
        endpoint = request.url.path

        # 檢查速率限制
        if not self.rate_limiter.check_rate_limit(client_ip, endpoint):
            # 計算重試時間
            retry_after = self.rate_limiter.get_retry_after(client_ip, endpoint)

            logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "請求過於頻繁，請稍後再試",
                    "error": "rate_limit_exceeded",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

        # 處理請求
        response = await call_next(request)

        # 添加速率限制標頭
        remaining = self._calculate_remaining(client_ip, endpoint)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.rate_limiter.window_seconds)

        return response

    def _calculate_remaining(self, client_ip: str, endpoint: str) -> int:
        """計算剩餘請求數"""
        key = self.rate_limiter._get_key(client_ip, endpoint)

        if endpoint and endpoint in self.rate_limiter.endpoint_limits:
            max_req = self.rate_limiter.endpoint_limits[endpoint]["max_requests"]
        else:
            max_req = self.rate_limiter.max_requests

        if key in self.rate_limiter._request_history:
            used = len(self.rate_limiter._request_history[key])
            return max(0, max_req - used)

        return max_req