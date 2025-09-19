"""
路由模組套件
包含各種 API 端點的路由定義
"""

from .meta import router as meta_router
from .hospitals import router as hospitals_router
from .triage import router as triage_router
from .healthinfo import router as healthinfo_router

__all__ = ["meta_router", "hospitals_router", "triage_router", "healthinfo_router"]
