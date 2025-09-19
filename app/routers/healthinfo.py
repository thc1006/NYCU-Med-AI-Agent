"""
健康資訊相關的 API 端點
包含健康主題、資源、疫苗接種、健保資訊等靜態資料
"""

import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse

from app.services.health_data import HealthDataService, get_health_data_service
from app.domain.models_extended import (
    HealthTopicsResponse, HealthResourcesResponse,
    VaccinationsResponse, InsuranceResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/health-info", tags=["健康資訊"])


@router.get(
    "/topics",
    response_model=HealthTopicsResponse,
    summary="取得健康教育主題清單",
    description="提供台灣健康教育主題資訊，包含就醫流程、急診指引等主題",
    response_description="健康主題清單，包含標題、摘要、連結等資訊"
)
async def get_health_topics(
    health_service: HealthDataService = Depends(get_health_data_service)
) -> HealthTopicsResponse:
    """
    取得健康教育主題清單

    提供完整的台灣健康教育主題資訊：
    - 就醫流程指引
    - 急診就醫指引
    - 健保查詢服務
    - 預防保健服務
    - 心理健康資源

    所有內容均以繁體中文提供，並連結至官方權威資源。
    """
    try:
        logger.info("Fetching health topics")
        topics_response = health_service.get_health_topics()

        if not topics_response.topics:
            logger.warning("No health topics found")

        return topics_response

    except Exception as e:
        logger.error(f"Error fetching health topics: {e}")
        raise HTTPException(
            status_code=500,
            detail="無法取得健康主題資料，請稍後再試"
        )


@router.get(
    "/resources",
    response_model=HealthResourcesResponse,
    summary="取得官方健康資源清單",
    description="提供台灣官方健康資源連結，包含政府機關、醫療機構等",
    response_description="健康資源清單，包含官方網站、聯絡資訊等"
)
async def get_health_resources(
    health_service: HealthDataService = Depends(get_health_data_service)
) -> HealthResourcesResponse:
    """
    取得官方健康資源清單

    提供台灣官方健康資源資訊：
    - 衛生福利部
    - 全民健康保險署
    - 疾病管制署
    - 國民健康署
    - 其他醫療相關機構

    所有資源均為政府官方網站，確保資訊權威性與可靠性。
    """
    try:
        logger.info("Fetching health resources")
        resources_response = health_service.get_health_resources()

        if not resources_response.resources:
            logger.warning("No health resources found")

        return resources_response

    except Exception as e:
        logger.error(f"Error fetching health resources: {e}")
        raise HTTPException(
            status_code=500,
            detail="無法取得健康資源資料，請稍後再試"
        )


@router.get(
    "/vaccinations",
    response_model=VaccinationsResponse,
    summary="取得疫苗接種時程資訊",
    description="提供兒童及成人疫苗接種時程表與建議",
    response_description="疫苗接種資訊，包含時程表、建議事項等"
)
async def get_vaccination_info(
    health_service: HealthDataService = Depends(get_health_data_service)
) -> VaccinationsResponse:
    """
    取得疫苗接種時程資訊

    提供完整的疫苗接種資訊：

    **兒童疫苗接種時程：**
    - 出生至學齡前各階段疫苗
    - 接種時間與注意事項
    - 疫苗種類與劑次

    **成人疫苗接種建議：**
    - 流感疫苗接種建議
    - COVID-19疫苗資訊
    - 其他成人疫苗建議

    資料來源為疾病管制署官方公布之疫苗接種時程。
    """
    try:
        logger.info("Fetching vaccination information")
        vaccination_response = health_service.get_vaccinations()

        if not vaccination_response.vaccinations:
            logger.warning("No vaccination information found")

        return vaccination_response

    except Exception as e:
        logger.error(f"Error fetching vaccination information: {e}")
        raise HTTPException(
            status_code=500,
            detail="無法取得疫苗接種資料，請稍後再試"
        )


@router.get(
    "/insurance",
    response_model=InsuranceResponse,
    summary="取得全民健保資訊",
    description="提供全民健康保險制度基本資訊與相關服務",
    response_description="健保資訊，包含給付項目、服務內容、聯絡方式等"
)
async def get_insurance_info(
    health_service: HealthDataService = Depends(get_health_data_service)
) -> InsuranceResponse:
    """
    取得全民健保資訊

    提供完整的全民健康保險資訊：

    **基本資訊：**
    - 健保制度說明
    - 給付範圍與項目
    - 部分負擔規定

    **服務項目：**
    - 健保卡申請與換發
    - 保險費查詢與繳費
    - 醫療費用核退
    - 醫療院所查詢

    **聯絡資訊：**
    - 健保諮詢專線
    - 緊急聯絡電話
    - 線上服務平台

    所有資訊均來自全民健康保險署官方資料。
    """
    try:
        logger.info("Fetching insurance information")
        insurance_response = health_service.get_insurance_info()

        return insurance_response

    except Exception as e:
        logger.error(f"Error fetching insurance information: {e}")
        raise HTTPException(
            status_code=500,
            detail="無法取得健保資料，請稍後再試"
        )


# Health check endpoint specifically for health info service
@router.get(
    "/status",
    summary="健康資訊服務狀態檢查",
    description="檢查健康資訊服務及資料檔案是否正常",
    response_description="服務狀態資訊",
    include_in_schema=False  # Hidden from OpenAPI docs
)
async def health_info_status(
    health_service: HealthDataService = Depends(get_health_data_service)
) -> Dict[str, Any]:
    """
    健康資訊服務狀態檢查

    檢查所有健康資訊資料檔案是否可正常載入
    """
    try:
        status = {
            "service": "health_info",
            "status": "ok",
            "data_sources": {},
            "locale": "zh-TW"
        }

        # Test each data source
        try:
            topics = health_service.get_health_topics()
            status["data_sources"]["topics"] = {
                "status": "ok",
                "count": topics.total
            }
        except Exception as e:
            status["data_sources"]["topics"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"

        try:
            resources = health_service.get_health_resources()
            status["data_sources"]["resources"] = {
                "status": "ok",
                "count": resources.total
            }
        except Exception as e:
            status["data_sources"]["resources"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"

        try:
            vaccinations = health_service.get_vaccinations()
            status["data_sources"]["vaccinations"] = {
                "status": "ok",
                "count": len(vaccinations.vaccinations)
            }
        except Exception as e:
            status["data_sources"]["vaccinations"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"

        try:
            insurance = health_service.get_insurance_info()
            status["data_sources"]["insurance"] = {
                "status": "ok",
                "services_count": len(insurance.insurance.services)
            }
        except Exception as e:
            status["data_sources"]["insurance"] = {
                "status": "error",
                "error": str(e)
            }
            status["status"] = "degraded"

        return status

    except Exception as e:
        logger.error(f"Health info status check failed: {e}")
        return {
            "service": "health_info",
            "status": "error",
            "error": str(e),
            "locale": "zh-TW"
        }