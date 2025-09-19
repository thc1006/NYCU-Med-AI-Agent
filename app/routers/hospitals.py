"""
就近醫療院所 API 端點
整合 geocoding（IP/地址）→ places →（可選）健保名冊比對
提供完整的醫院搜尋與資訊服務
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Request
from pydantic import BaseModel, validator
from app.services.geocoding import ip_geolocate, geocode_address, GeocodeResult
from app.services.places import nearby_hospitals, format_hospital_results
from app.services.nhia_registry import enhance_places_with_nhia_info
from app.config import get_settings

router = APIRouter(prefix="/v1/hospitals", tags=["醫院搜尋"])


class HospitalSearchRequest(BaseModel):
    """醫院搜尋請求模型"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    use_ip: bool = False
    radius: int = 3000
    max_results: int = 20

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('radius')
    def validate_radius(cls, v):
        if not (100 <= v <= 50000):
            raise ValueError('Radius must be between 100 and 50000 meters')
        return v

    @validator('max_results')
    def validate_max_results(cls, v):
        if not (1 <= v <= 50):
            raise ValueError('Max results must be between 1 and 50')
        return v


class HospitalSearchResponse(BaseModel):
    """醫院搜尋回應模型"""
    results: List[Dict[str, Any]]
    search_center: Dict[str, float]
    search_radius: int
    total_count: int
    locale: str = "zh-TW"
    emergency_numbers: List[str]
    emergency_reminder: str
    search_method: str  # "coordinates", "address", "ip"


def get_client_ip(request: Request) -> str:
    """取得客戶端 IP 地址"""
    # 檢查代理標頭
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 使用直接連線的 IP
    if hasattr(request.client, 'host'):
        return request.client.host

    return "127.0.0.1"  # 預設值


@router.get("/nearby",
           summary="搜尋就近醫療院所",
           description="根據座標、地址或IP位置搜尋附近的醫院，包含健保特約資訊",
           response_model=HospitalSearchResponse,
           tags=["醫院搜尋"])
async def search_nearby_hospitals(
    request: Request,
    latitude: Optional[float] = Query(None, description="緯度 (優先級最高)"),
    longitude: Optional[float] = Query(None, description="經度 (與緯度一起使用)"),
    address: Optional[str] = Query(None, description="地址字串 (需要geocoding)"),
    use_ip: bool = Query(False, description="使用IP定位 (最低優先級)"),
    radius: int = Query(3000, description="搜尋半徑 (公尺)", ge=100, le=50000),
    max_results: int = Query(20, description="最大結果數量", ge=1, le=50),
    include_nhia: bool = Query(True, description="是否包含健保特約資訊")
) -> HospitalSearchResponse:
    """
    搜尋就近醫療院所

    優先級順序：
    1. latitude + longitude (直接座標)
    2. address (需要geocoding)
    3. use_ip=true (IP定位，誤差較大)

    Returns:
        HospitalSearchResponse: 包含醫院列表與搜尋資訊
    """
    settings = get_settings()
    search_method = ""
    search_center = {}

    # 第一優先：直接座標
    if latitude is not None and longitude is not None:
        # 驗證座標
        if not (-90 <= latitude <= 90):
            raise HTTPException(status_code=400, detail="Invalid latitude. Must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise HTTPException(status_code=400, detail="Invalid longitude. Must be between -180 and 180.")

        search_center = {"latitude": latitude, "longitude": longitude}
        search_method = "coordinates"

    # 第二優先：地址geocoding
    elif address:
        try:
            geocode_result = geocode_address(address)
            if geocode_result:
                search_center = {
                    "latitude": geocode_result.latitude,
                    "longitude": geocode_result.longitude
                }
                search_method = "address"
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unable to geocode address: '{address}'. Please provide a valid Taiwan address."
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Geocoding error: {str(e)}"
            )

    # 第三優先：IP定位
    elif use_ip:
        client_ip = get_client_ip(request)
        try:
            ip_result = ip_geolocate(client_ip)
            if ip_result:
                search_center = {
                    "latitude": ip_result.latitude,
                    "longitude": ip_result.longitude
                }
                search_method = "ip"
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to determine location from IP address. Please provide coordinates or address."
                )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"IP geolocation error: {str(e)}"
            )

    else:
        raise HTTPException(
            status_code=400,
            detail="Must provide either (latitude+longitude), address, or set use_ip=true"
        )

    # 搜尋附近醫院
    try:
        places_results = nearby_hospitals(
            lat=search_center["latitude"],
            lng=search_center["longitude"],
            radius=radius,
            max_results=max_results
        )

        # 增強健保資訊（可選）
        if include_nhia:
            enhanced_results = enhance_places_with_nhia_info(places_results)
        else:
            # 基本格式化
            enhanced_results = []
            for place in places_results:
                result = {
                    "id": place.id,
                    "name": place.name,
                    "address": place.address,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "distance_meters": place.distance_meters
                }

                # 可選欄位
                if place.phone:
                    result["phone"] = place.phone
                if place.rating is not None:
                    result["rating"] = place.rating
                if place.is_open_now is not None:
                    result["is_open_now"] = place.is_open_now
                if place.opening_hours:
                    result["opening_hours"] = place.opening_hours
                if place.business_status != "UNKNOWN":
                    result["business_status"] = place.business_status

                enhanced_results.append(result)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Hospital search error: {str(e)}"
        )

    # 建構回應
    response = HospitalSearchResponse(
        results=enhanced_results,
        search_center=search_center,
        search_radius=radius,
        total_count=len(enhanced_results),
        locale="zh-TW",
        emergency_numbers=settings.emergency_numbers,
        emergency_reminder=(
            "緊急情況請立即撥打 119（消防救護）或 110（警察）。"
            "本搜尋結果僅供參考，不可取代專業醫療判斷。"
        ),
        search_method=search_method
    )

    return response


@router.get("/nearby/simple",
           summary="簡化版就近醫院搜尋",
           description="僅返回基本醫院資訊，不包含健保比對",
           tags=["醫院搜尋"])
async def search_nearby_hospitals_simple(
    request: Request,
    latitude: Optional[float] = Query(None, description="緯度"),
    longitude: Optional[float] = Query(None, description="經度"),
    address: Optional[str] = Query(None, description="地址"),
    use_ip: bool = Query(False, description="使用IP定位"),
    radius: int = Query(3000, description="搜尋半徑", ge=100, le=50000),
    max_results: int = Query(10, description="最大結果數量", ge=1, le=20)
) -> Dict[str, Any]:
    """
    簡化版醫院搜尋，適用於快速查詢場景

    Returns:
        Dict: 簡化的醫院列表
    """
    # 重用主要搜尋邏輯，但不包含健保資訊
    full_response = await search_nearby_hospitals(
        request=request,
        latitude=latitude,
        longitude=longitude,
        address=address,
        use_ip=use_ip,
        radius=radius,
        max_results=max_results,
        include_nhia=False
    )

    # 簡化回應格式
    simplified_results = []
    for hospital in full_response.results:
        simplified = {
            "name": hospital["name"],
            "address": hospital["address"],
            "distance_meters": hospital["distance_meters"]
        }
        if "phone" in hospital:
            simplified["phone"] = hospital["phone"]
        if "rating" in hospital:
            simplified["rating"] = hospital["rating"]

        simplified_results.append(simplified)

    return {
        "hospitals": simplified_results,
        "count": len(simplified_results),
        "search_radius": radius,
        "emergency_numbers": full_response.emergency_numbers,
        "locale": "zh-TW"
    }


@router.get("/emergency-info",
           summary="取得緊急醫療指引",
           description="提供台灣緊急醫療聯絡資訊與就醫指引",
           tags=["緊急資訊"])
async def get_emergency_medical_info() -> Dict[str, Any]:
    """
    取得緊急醫療指引與聯絡資訊

    Returns:
        Dict: 緊急醫療資訊
    """
    settings = get_settings()

    return {
        "emergency_numbers": [
            {
                "number": "119",
                "description": "消防救護專線",
                "usage": "火災、救護車、緊急救助"
            },
            {
                "number": "110",
                "description": "警察報案專線",
                "usage": "治安、交通事故、刑案報案"
            },
            {
                "number": "112",
                "description": "手機緊急撥號",
                "usage": "無卡、無訊號時的緊急號碼"
            },
            {
                "number": "113",
                "description": "婦幼保護專線",
                "usage": "家暴、性侵、兒少保護"
            }
        ],
        "emergency_guidelines": [
            "保持冷靜，清楚說明現場狀況",
            "提供精確的地點資訊",
            "說明傷者數量與傷勢",
            "配合指示進行初步急救",
            "確保現場安全，等待救援"
        ],
        "when_to_call_119": [
            "呼吸困難或停止",
            "胸痛或心臟病發作徵象",
            "嚴重外傷或大量出血",
            "意識不清或昏迷",
            "嚴重燒燙傷",
            "中毒或過敏反應",
            "骨折或脊椎受傷"
        ],
        "hospital_levels": {
            "醫學中心": "重症與複雜疾病治療",
            "區域醫院": "一般急症與專科治療",
            "地區醫院": "常見疾病與基本急診",
            "診所": "輕症與預防保健"
        },
        "locale": "zh-TW"
    }