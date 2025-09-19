"""
元數據相關的 API 端點
包含急救熱線、系統資訊等元數據
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Response
from pydantic import BaseModel
from app.config import get_settings

router = APIRouter(prefix="/v1/meta", tags=["元數據"])


class EmergencyNumber(BaseModel):
    """急救號碼模型"""
    code: str
    description: str
    category: str
    available: str = "24小時"
    coverage: str = "全台灣"


class EmergencyResponse(BaseModel):
    """急救熱線回應模型"""
    numbers: List[EmergencyNumber]
    updated_at: str
    locale: str = "zh-TW"
    source: str
    disclaimer: str
    usage_notes: List[str]


@router.get("/emergency",
           summary="取得台灣急救熱線資訊",
           description="取得台灣地區的急救、報案、諮詢熱線號碼與使用說明",
           response_model=EmergencyResponse,
           response_description="台灣急救熱線完整資訊",
           tags=["急救熱線"])
async def get_emergency_numbers(response: Response) -> EmergencyResponse:
    """
    取得台灣急救熱線資訊

    提供台灣地區官方認可的急救與緊急聯絡電話號碼，
    包含使用說明、適用範圍和注意事項。

    Returns:
        EmergencyResponse: 包含完整急救熱線資訊的回應

    Note:
        - 資料來源：台北市政府、NCC、內政部警政署
        - 所有號碼均為24小時服務
        - 緊急情況請優先撥打 119 或 110
    """
    settings = get_settings()

    # 設定快取標頭（急救號碼資訊相對穩定）
    response.headers["Cache-Control"] = "public, max-age=3600"  # 1小時快取

    # 取得急救號碼詳細資訊
    emergency_numbers = [
        EmergencyNumber(**detail) for detail in settings.emergency_numbers_detail
    ]

    # 建構回應
    emergency_response = EmergencyResponse(
        numbers=emergency_numbers,
        updated_at=datetime.now(timezone.utc).isoformat(),
        locale="zh-TW",
        source="台北市政府英文網頁、NCC公告、內政部警政署",
        disclaimer="本資訊僅供參考，緊急情況請立即撥打相關號碼求助。醫療緊急請撥119，治安問題請撥110。",
        usage_notes=[
            "緊急狀況請保持冷靜，清楚說明地點和狀況",
            "119：火災、救護車、緊急救助",
            "110：報案、治安、交通事故",
            "112：手機無卡或無訊號時的緊急號碼",
            "113：家暴、性侵、兒少保護求助",
            "165：詐騙諮詢、通報可疑詐騙",
            "撥打前請確認您的位置，以便救援人員快速到達"
        ]
    )

    return emergency_response


@router.get("/emergency/simple",
           summary="取得簡化急救號碼列表",
           description="取得僅包含號碼代碼的簡化急救熱線列表",
           tags=["急救熱線"])
async def get_emergency_numbers_simple() -> Dict[str, Any]:
    """
    取得簡化的急救號碼列表

    Returns:
        包含急救號碼代碼陣列的字典

    Note:
        適用於需要快速取得急救號碼列表的場景
    """
    settings = get_settings()

    return {
        "emergency_numbers": settings.emergency_numbers,
        "locale": "zh-TW",
        "count": len(settings.emergency_numbers)
    }