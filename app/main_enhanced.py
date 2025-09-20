"""
台灣醫療 AI 助理 - FastAPI 主應用程式（增強版）
包含完整監控、審計與度量功能以及進階 OpenAPI 文件的醫療 AI 助理系統
"""

import uuid
import asyncio
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from app.config import get_settings
from app.middlewares.privacy import PrivacyMiddleware
from app.middlewares.rate_limit import RateLimitMiddleware
from app.middlewares.structured_logging import StructuredLoggingMiddleware, MetricsMiddleware
from app.routers import meta_router, hospitals_router, triage_router, healthinfo_router
from app.routers.monitoring import router as monitoring_router
from app.monitoring.structured_logging import configure_logging, structured_logger
from app.monitoring.health import health_checker
from app.monitoring.metrics import metrics_collector
from app.api_docs import enhance_fastapi_docs, get_taiwan_medical_openapi_config


# RequestIdMiddleware 已整合到 PrivacyMiddleware 中
# 不需要單獨的 RequestIdMiddleware


# 獲取設定實例（僅在需要時載入）
def get_app_config():
    """取得應用程式設定"""
    try:
        return get_settings()
    except Exception:
        # 在測試環境中可能沒有完整設定
        return None

settings = get_app_config()

# 初始化監控系統
def initialize_monitoring():
    """初始化監控、日誌與度量系統"""
    # 配置結構化日誌
    configure_logging(level="INFO")

    # 初始化健康檢查器
    monitoring_config = {}
    if settings:
        monitoring_config = {
            "google_places_api_key": getattr(settings, "google_places_api_key", None),
            "google_geocoding_api_key": getattr(settings, "google_geocoding_api_key", None),
            "database": getattr(settings, "database_config", None)
        }

    health_checker.initialize(monitoring_config)

    structured_logger.info("Monitoring system initialized", config_keys=list(monitoring_config.keys()))

# 使用 lifespan context manager 取代 on_event (FastAPI 0.95+)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Application lifespan management"""
    # Startup
    initialize_monitoring()
    structured_logger.info("Taiwan Medical AI Assistant started")
    yield
    # Shutdown
    structured_logger.info("Taiwan Medical AI Assistant shutting down")

# 創建 FastAPI 應用程式實例（使用增強的 OpenAPI 配置）
openapi_config = get_taiwan_medical_openapi_config()
app = FastAPI(
    title=openapi_config["title"],
    description=openapi_config["description"],
    version=openapi_config["version"],
    docs_url=openapi_config["docs_url"],
    redoc_url=openapi_config["redoc_url"],
    openapi_url=openapi_config["openapi_url"],
    contact=openapi_config["contact"],
    license_info=openapi_config["license_info"],
    terms_of_service=openapi_config["terms_of_service"],
    lifespan=lifespan
)

# 增強 API 文件功能
enhance_fastapi_docs(app)

# 添加監控中介層（按照執行順序）
app.add_middleware(StructuredLoggingMiddleware)  # 最外層：結構化日誌
app.add_middleware(MetricsMiddleware)            # 度量收集
app.add_middleware(RateLimitMiddleware)          # 速率限制
app.add_middleware(PrivacyMiddleware)            # 隱私與審計（最內層）

# 添加路由
app.include_router(monitoring_router)  # 監控 API 路由
app.include_router(meta_router)
app.include_router(hospitals_router)
app.include_router(triage_router)
app.include_router(healthinfo_router)


@app.get("/healthz",
         summary="健康檢查端點",
         description="檢查 API 服務是否正常運行",
         response_description="服務狀態資訊",
         tags=["系統監控"])
async def health_check():
    """
    健康檢查端點

    回應格式:
    - status: 服務狀態 ("ok" 表示正常)

    回應 headers:
    - X-Request-Id: 請求唯一識別碼
    """
    return {"status": "ok"}


# 根路由 - 重定向到文件
@app.get("/", include_in_schema=False)
async def root():
    """根路由重定向到 API 文件"""
    return JSONResponse(
        content={
            "message": "台灣醫療 AI 助理 API",
            "description": "具備完整監控、審計與合規功能的醫療 AI 助理系統",
            "docs": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json",
            "health": "/healthz",
            "monitoring": {
                "health": "/v1/monitoring/health",
                "metrics": "/v1/monitoring/metrics",
                "dashboard": "/v1/monitoring/dashboard"
            },
            "features": [
                "症狀分析與分流",
                "就近醫療院所搜尋",
                "緊急狀況辨識",
                "PDPA 合規審計",
                "即時健康監控",
                "效能度量分析"
            ],
            "api_features": {
                "documentation": {
                    "openapi_version": "3.0.0",
                    "taiwan_localized": True,
                    "medical_disclaimers": True,
                    "emergency_warnings": True,
                    "pdpa_compliance": True
                },
                "safety": {
                    "red_flag_detection": True,
                    "emergency_routing": True,
                    "rate_limiting": True,
                    "audit_trail": True
                },
                "taiwan_specific": {
                    "traditional_chinese": True,
                    "taiwan_addresses": True,
                    "emergency_numbers": ["119", "110", "112", "113"],
                    "nhia_integration": True
                }
            }
        }
    )


# 新增 OpenAPI 結構描述端點（供外部工具使用）
@app.get("/openapi.yaml",
         summary="OpenAPI YAML 結構描述",
         description="取得 YAML 格式的 OpenAPI 3.0 結構描述",
         response_class=Response,
         tags=["系統監控"])
async def get_openapi_yaml():
    """
    取得 YAML 格式的 OpenAPI 結構描述

    提供標準的 OpenAPI 3.0 YAML 格式結構描述，
    可用於 API 測試工具、程式碼生成器等外部工具。
    """
    import yaml
    from fastapi.openapi.utils import get_openapi

    openapi_schema = app.openapi()
    yaml_content = yaml.dump(openapi_schema, default_flow_style=False, allow_unicode=True)

    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": "attachment; filename=taiwan-medical-ai-openapi.yaml",
            "X-API-Version": "1.0.0",
            "X-Generated-At": "runtime"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)