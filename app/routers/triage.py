"""
症狀分級 API 端點
提供症狀評估與就醫建議服務
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import uuid
from fastapi import APIRouter, HTTPException, Request, Query
from app.domain.models import (
    SymptomQuery,
    TriageRequest,
    TriageResponse,
    TriageLevel
)
from app.domain.triage import rule_triage
from app.services.places import nearby_hospitals
from app.config import get_settings

router = APIRouter(prefix="/v1/triage", tags=["症狀分級"])


@router.post("",
            summary="症狀評估與分級",
            description="根據症狀描述提供分級建議、就醫指引與急救提醒",
            response_model=TriageResponse,
            tags=["症狀分級"])
async def assess_symptoms(
    request: Request,
    triage_request: TriageRequest
) -> TriageResponse:
    """
    症狀評估與分級

    根據使用者提供的症狀描述，分析並提供：
    - 緊急程度分級 (emergency/outpatient/self-care)
    - 就醫建議
    - 下一步行動指引
    - 推薦就診科別
    - 醫療免責聲明

    Args:
        triage_request: 症狀評估請求

    Returns:
        TriageResponse: 包含分級結果與建議
    """
    settings = get_settings()

    # 建立症狀查詢物件
    try:
        symptom_query = SymptomQuery(
            symptom_text=triage_request.symptom_text,
            age=triage_request.age,
            gender=triage_request.gender,
            duration_hours=triage_request.duration_hours,
            has_chronic_disease=triage_request.has_chronic_disease,
            medications=triage_request.medications
        )
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=str(e)
        )

    # 執行規則基礎的症狀分級
    try:
        triage_result = rule_triage(symptom_query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Triage assessment error: {str(e)}"
        )

    # 如果需要附近醫院資訊
    nearby_hospitals_data = None
    if triage_request.include_nearby_hospitals and triage_request.location:
        try:
            hospitals = nearby_hospitals(
                lat=triage_request.location["latitude"],
                lng=triage_request.location["longitude"],
                radius=5000,
                max_results=5
            )
            # 格式化醫院資訊
            nearby_hospitals_data = [
                {
                    "name": h.name,
                    "address": h.address,
                    "phone": h.phone,
                    "distance_meters": h.distance_meters,
                    "rating": h.rating
                }
                for h in hospitals
            ]
        except Exception:
            # 醫院搜尋失敗不影響主要功能
            nearby_hospitals_data = []

    # 生成請求ID和時間戳
    request_id = f"triage_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    # 建構回應
    response = TriageResponse(
        triage_level=triage_result.level.value,
        advice=triage_result.advice,
        detected_symptoms=triage_result.detected_symptoms,
        next_steps=triage_result.next_steps,
        disclaimer=triage_result.disclaimer,
        emergency_numbers=triage_result.emergency_numbers or settings.emergency_numbers,
        recommended_departments=triage_result.recommended_departments,
        estimated_wait_time=triage_result.estimated_wait_time,
        confidence_score=triage_result.confidence_score,
        nearby_hospitals=nearby_hospitals_data,
        request_id=request_id,
        timestamp=timestamp,
        locale="zh-TW"
    )

    return response


@router.post("/quick",
            summary="快速症狀評估",
            description="僅提供症狀文字的快速評估",
            tags=["症狀分級"])
async def quick_assessment(
    symptom_text: str = Query(..., description="症狀描述", min_length=1, max_length=500)
) -> Dict[str, Any]:
    """
    快速症狀評估

    簡化版評估，只需要症狀描述文字

    Args:
        symptom_text: 症狀描述

    Returns:
        Dict: 簡化的評估結果
    """
    settings = get_settings()

    # 建立簡單查詢
    symptom_query = SymptomQuery(symptom_text=symptom_text)

    try:
        triage_result = rule_triage(symptom_query)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quick assessment error: {str(e)}"
        )

    return {
        "level": triage_result.level.value,
        "advice": triage_result.advice,
        "next_steps": triage_result.next_steps[:3],  # 只顯示前3個步驟
        "emergency_numbers": settings.emergency_numbers if triage_result.level == TriageLevel.EMERGENCY else [],
        "disclaimer": "本評估僅供參考，緊急狀況請撥打119。",
        "locale": "zh-TW"
    }


@router.get("/symptoms/emergency",
           summary="取得緊急症狀列表",
           description="返回系統識別的緊急症狀關鍵字",
           tags=["症狀資訊"])
async def get_emergency_symptoms() -> Dict[str, Any]:
    """
    取得緊急症狀列表

    Returns:
        Dict: 緊急症狀資訊
    """
    from app.domain.rules_tw import get_emergency_keywords

    keywords = get_emergency_keywords()

    return {
        "emergency_symptoms": keywords,
        "total_count": len(keywords),
        "description": "出現這些症狀時應立即撥打119或前往急診",
        "emergency_numbers": ["119", "112"],
        "locale": "zh-TW"
    }


@router.get("/symptoms/mild",
           summary="取得輕微症狀列表",
           description="返回可自我照護的輕微症狀",
           tags=["症狀資訊"])
async def get_mild_symptoms() -> Dict[str, Any]:
    """
    取得輕微症狀列表

    Returns:
        Dict: 輕微症狀資訊
    """
    from app.domain.rules_tw import get_mild_keywords

    keywords = get_mild_keywords()

    return {
        "mild_symptoms": keywords,
        "total_count": len(keywords),
        "description": "這些症狀通常可透過休息和自我照護改善",
        "self_care_tips": [
            "充分休息",
            "多喝水",
            "清淡飲食",
            "觀察症狀變化",
            "如症狀持續或惡化請就醫"
        ],
        "locale": "zh-TW"
    }


@router.get("/departments",
           summary="取得推薦科別對照表",
           description="症狀與建議就診科別的對照資訊",
           tags=["症狀資訊"])
async def get_department_mapping() -> Dict[str, Any]:
    """
    取得症狀與科別對照表

    Returns:
        Dict: 科別對照資訊
    """
    department_info = {
        "心臟內科": {
            "symptoms": ["胸痛", "胸悶", "心悸", "心跳異常"],
            "description": "心血管相關疾病"
        },
        "胸腔內科": {
            "symptoms": ["呼吸困難", "咳嗽", "氣喘", "胸部不適"],
            "description": "呼吸系統疾病"
        },
        "神經內科": {
            "symptoms": ["頭痛", "頭暈", "麻痺", "手腳無力"],
            "description": "神經系統疾病"
        },
        "腸胃內科": {
            "symptoms": ["腹痛", "嘔吐", "腹瀉", "便秘"],
            "description": "消化系統疾病"
        },
        "耳鼻喉科": {
            "symptoms": ["喉嚨痛", "流鼻水", "鼻塞", "耳痛"],
            "description": "耳鼻喉相關疾病"
        },
        "家醫科": {
            "symptoms": ["發燒", "感冒", "疲倦", "一般不適"],
            "description": "一般內科疾病、健康檢查"
        },
        "急診": {
            "symptoms": ["意識不清", "大量出血", "嚴重創傷", "中毒"],
            "description": "緊急醫療狀況"
        }
    }

    return {
        "departments": department_info,
        "total_departments": len(department_info),
        "note": "建議科別僅供參考，實際就診請依醫師專業判斷",
        "locale": "zh-TW"
    }