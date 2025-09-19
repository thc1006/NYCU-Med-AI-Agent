"""
Structured logging middleware for Taiwan Medical AI Assistant.
Integrates structured logging with correlation IDs and request tracking.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.monitoring.structured_logging import structured_logger
from app.monitoring.metrics import metrics_collector
from app.monitoring.audit import business_logger, hash_pii


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured logging with correlation ID and metrics."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with structured logging."""
        # Generate or extract correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID") or
            request.headers.get("x-correlation-id") or
            str(uuid.uuid4())
        )

        # Set correlation ID in thread-local context
        with structured_logger.correlation_context(correlation_id):
            start_time = time.time()

            # Log request start
            structured_logger.info(
                "Request started",
                method=request.method,
                url=str(request.url),
                user_agent_hash=hash_pii(request.headers.get("user-agent", "")),
                ip_address_hash=hash_pii(self._get_client_ip(request))
            )

            # Track request with performance metrics
            with metrics_collector.performance_tracker.track_request(
                endpoint=self._normalize_endpoint(request.url.path),
                method=request.method
            ):
                try:
                    # Process request
                    response = await call_next(request)

                    # Calculate response time
                    response_time = time.time() - start_time
                    response_time_ms = int(response_time * 1000)

                    # Add correlation ID to response headers
                    response.headers["X-Correlation-ID"] = correlation_id

                    # Track API metrics
                    metrics_collector.api_metrics.track_request(
                        endpoint=self._normalize_endpoint(request.url.path),
                        method=request.method,
                        status_code=response.status_code,
                        duration_seconds=response_time
                    )

                    # Log successful request
                    structured_logger.info(
                        "Request completed",
                        method=request.method,
                        url=str(request.url),
                        status_code=response.status_code,
                        response_time_ms=response_time_ms,
                        content_length=response.headers.get("content-length", 0)
                    )

                    # Log to business audit if relevant endpoint
                    if self._is_business_endpoint(request.url.path):
                        business_logger.log_api_usage(
                            endpoint=self._normalize_endpoint(request.url.path),
                            method=request.method,
                            status_code=response.status_code,
                            response_time_ms=response_time_ms,
                            request_size_bytes=self._get_request_size(request),
                            response_size_bytes=int(response.headers.get("content-length", 0))
                        )

                    return response

                except Exception as e:
                    # Calculate response time for error case
                    response_time = time.time() - start_time
                    response_time_ms = int(response_time * 1000)

                    # Log error
                    structured_logger.error(
                        "Request failed",
                        method=request.method,
                        url=str(request.url),
                        error=str(e),
                        response_time_ms=response_time_ms
                    )

                    # Re-raise the exception
                    raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        if hasattr(request.client, "host"):
            return request.client.host

        return "unknown"

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        # Replace dynamic segments with placeholders
        import re

        # Replace UUIDs with placeholder
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)

        # Replace numeric IDs with placeholder
        path = re.sub(r'/\d+', '/{id}', path)

        return path

    def _is_business_endpoint(self, path: str) -> bool:
        """Check if endpoint is a business-critical endpoint."""
        business_paths = ['/v1/triage', '/v1/hospitals', '/v1/health-info']
        return any(path.startswith(bp) for bp in business_paths)

    def _get_request_size(self, request: Request) -> int:
        """Estimate request size."""
        content_length = request.headers.get("content-length")
        if content_length:
            return int(content_length)

        # Fallback estimation
        return len(str(request.url)) + sum(len(k) + len(v) for k, v in request.headers.items())


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware specifically for metrics collection."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Collect metrics for request processing."""
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Track response size
        content_length = response.headers.get("content-length")
        if content_length:
            metrics_collector.api_metrics.track_response_size(
                endpoint=self._normalize_endpoint(request.url.path),
                size_bytes=int(content_length)
            )

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint path for metrics."""
        import re
        path = re.sub(r'/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '/{id}', path)
        path = re.sub(r'/\d+', '/{id}', path)
        return path