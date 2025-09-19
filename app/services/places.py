"""
Google Places API 服務模組
提供就近醫療院所搜尋功能，使用 Places API (New) Nearby Search
包含台灣在地化設定與錯誤處理
"""

import json
import math
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import httpx
from app.config import get_settings
from app.utils.resilience import exponential_backoff_retry, CircuitBreaker
from app.services.cache import ResponseCache


@dataclass
class PlaceResult:
    """醫療院所搜尋結果模型"""
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    rating: Optional[float] = None
    is_open_now: Optional[bool] = None
    opening_hours: List[str] = None
    business_status: str = "UNKNOWN"
    distance_meters: Optional[int] = None

    def __post_init__(self):
        """後處理初始化"""
        if self.opening_hours is None:
            self.opening_hours = []


class PlacesAPIError(Exception):
    """Places API 相關錯誤"""
    def __init__(self, message: str, status_code: int = None, error_type: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_type = error_type


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> int:
    """
    計算兩點間的直線距離（公尺）
    使用 Haversine 公式
    """
    # 轉換為弧度
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # Haversine 公式
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = (math.sin(dlat/2)**2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2)
    c = 2 * math.asin(math.sqrt(a))

    # 地球半徑（公尺）
    earth_radius = 6371000
    distance = earth_radius * c

    return int(distance)


def validate_coordinates(lat: float, lng: float) -> None:
    """驗證座標有效性"""
    if not (-90 <= lat <= 90):
        raise ValueError(f"Invalid latitude: {lat}. Must be between -90 and 90.")

    if not (-180 <= lng <= 180):
        raise ValueError(f"Invalid longitude: {lng}. Must be between -180 and 180.")


def parse_opening_hours(opening_hours_data: Dict[str, Any]) -> tuple[Optional[bool], List[str]]:
    """
    解析營業時間資料

    Returns:
        tuple: (is_open_now, weekday_descriptions)
    """
    if not opening_hours_data:
        return None, []

    is_open_now = opening_hours_data.get("openNow")
    weekday_descriptions = opening_hours_data.get("weekdayDescriptions", [])

    return is_open_now, weekday_descriptions


def nearby_hospitals(lat: float, lng: float, radius: int = 3000, max_results: int = 20) -> List[PlaceResult]:
    """
    搜尋指定座標附近的醫院

    Args:
        lat: 緯度
        lng: 經度
        radius: 搜尋半徑（公尺），預設 3000
        max_results: 最大結果數量，預設 20

    Returns:
        List[PlaceResult]: 醫院搜尋結果列表，按距離排序

    Raises:
        ValueError: 座標無效
        PlacesAPIError: API 請求錯誤
    """
    # 驗證輸入參數
    validate_coordinates(lat, lng)

    if radius <= 0 or radius > 50000:
        raise ValueError(f"Invalid radius: {radius}. Must be between 1 and 50000 meters.")

    settings = get_settings()
    api_key = settings.google_places_api_key

    # 構建請求 URL
    url = "https://places.googleapis.com/v1/places:searchNearby"

    # 構建請求資料
    request_data = {
        "includedTypes": ["hospital"],
        "maxResultCount": min(max_results, 20),  # API 限制最多 20 個結果
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lng
                },
                "radius": radius
            }
        },
        "languageCode": "zh-TW",
        "regionCode": "TW"
    }

    # 請求標頭
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.id,places.displayName,places.formattedAddress,"
            "places.internationalPhoneNumber,places.rating,places.location,"
            "places.currentOpeningHours,places.businessStatus"
        )
    }

    try:
        # 發送請求
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url,
                headers=headers,
                content=json.dumps(request_data)
            )

        # 處理 HTTP 錯誤
        if response.status_code == 401:
            raise PlacesAPIError(
                "API key not valid. Please pass a valid API key.",
                status_code=401,
                error_type="UNAUTHENTICATED"
            )
        elif response.status_code == 429:
            raise PlacesAPIError(
                "Quota exceeded. Please check your API usage limits.",
                status_code=429,
                error_type="RESOURCE_EXHAUSTED"
            )
        elif response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            raise PlacesAPIError(
                f"Places API error: {error_message}",
                status_code=response.status_code
            )

        # 解析回應
        data = response.json()
        places_data = data.get("places", [])

        # 轉換為 PlaceResult 物件
        results = []
        for place_data in places_data:
            try:
                # 取得基本資訊
                place_id = place_data.get("id", "")
                display_name = place_data.get("displayName", {})
                name = display_name.get("text", "未知醫院")
                address = place_data.get("formattedAddress", "")
                phone = place_data.get("internationalPhoneNumber")
                rating = place_data.get("rating")
                business_status = place_data.get("businessStatus", "UNKNOWN")

                # 取得位置資訊
                location = place_data.get("location", {})
                place_lat = location.get("latitude")
                place_lng = location.get("longitude")

                if place_lat is None or place_lng is None:
                    continue  # 跳過沒有座標的結果

                # 計算距離
                distance = calculate_distance(lat, lng, place_lat, place_lng)

                # 解析營業時間
                opening_hours_data = place_data.get("currentOpeningHours", {})
                is_open_now, weekday_descriptions = parse_opening_hours(opening_hours_data)

                # 建立結果物件
                result = PlaceResult(
                    id=place_id,
                    name=name,
                    address=address,
                    latitude=place_lat,
                    longitude=place_lng,
                    phone=phone,
                    rating=rating,
                    is_open_now=is_open_now,
                    opening_hours=weekday_descriptions,
                    business_status=business_status,
                    distance_meters=distance
                )

                results.append(result)

            except (KeyError, TypeError, ValueError) as e:
                # 跳過有問題的資料項目，記錄但不中斷
                continue

        # 按距離排序
        results.sort(key=lambda x: x.distance_meters if x.distance_meters is not None else float('inf'))

        # 限制結果數量
        return results[:max_results]

    except httpx.TimeoutException:
        raise PlacesAPIError(
            "Request timeout while connecting to Places API",
            error_type="TIMEOUT"
        )
    except httpx.RequestError as e:
        raise PlacesAPIError(
            f"Network error while connecting to Places API: {str(e)}",
            error_type="NETWORK_ERROR"
        )
    except json.JSONDecodeError:
        raise PlacesAPIError(
            "Invalid JSON response from Places API",
            error_type="INVALID_RESPONSE"
        )


def format_hospital_results(results: List[PlaceResult], include_emergency_info: bool = True) -> Dict[str, Any]:
    """
    格式化醫院搜尋結果為 API 回應格式

    Args:
        results: 醫院搜尋結果
        include_emergency_info: 是否包含急救資訊

    Returns:
        Dict: 格式化的 API 回應
    """
    settings = get_settings()

    formatted_results = []
    for result in results:
        formatted_result = {
            "id": result.id,
            "name": result.name,
            "address": result.address,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "distance_meters": result.distance_meters
        }

        # 可選欄位
        if result.phone:
            formatted_result["phone"] = result.phone
        if result.rating is not None:
            formatted_result["rating"] = result.rating
        if result.is_open_now is not None:
            formatted_result["is_open_now"] = result.is_open_now
        if result.opening_hours:
            formatted_result["opening_hours"] = result.opening_hours
        if result.business_status != "UNKNOWN":
            formatted_result["business_status"] = result.business_status

        formatted_results.append(formatted_result)

    response_data = {
        "results": formatted_results,
        "count": len(formatted_results),
        "locale": "zh-TW"
    }

    # 包含急救資訊
    if include_emergency_info:
        response_data["emergency_numbers"] = settings.emergency_numbers
        response_data["emergency_reminder"] = (
            "緊急情況請立即撥打 119（消防救護）或 110（警察）。"
            "本搜尋結果僅供參考，不可取代專業醫療判斷。"
        )

    return response_data


def nearby_hospitals_with_fallback(
    lat: float,
    lng: float,
    radius: int = 3000,
    max_results: int = 10,
    cache: Optional[ResponseCache] = None,
    enable_cascade: bool = False
) -> Dict[str, Any]:
    """
    搜尋附近醫院（含降級機制）

    Args:
        lat: 緯度
        lng: 經度
        radius: 搜尋半徑（公尺）
        max_results: 最大結果數
        cache: 快取實例
        enable_cascade: 啟用級聯降級

    Returns:
        包含醫院列表與狀態的字典
    """
    settings = get_settings()

    # 檢查快取
    if cache:
        cached_result = cache.get(lat=lat, lng=lng, radius=radius)
        if cached_result:
            return {
                **cached_result,
                "status": "cached",
                "message": "使用快取資料"
            }

    # 嘗試 Google Places
    try:
        hospitals = nearby_hospitals(lat, lng, radius, max_results)

        result = {
            "status": "ok",
            "results": hospitals,
            "emergency_numbers": settings.emergency_numbers,
            "locale": "zh-TW"
        }

        # 存入快取
        if cache:
            cache.set(result, lat=lat, lng=lng, radius=radius)

        return result

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            # 速率限制
            return {
                "status": "degraded",
                "results": [],
                "message": "系統繁忙，請稍後再試",
                "emergency_numbers": settings.emergency_numbers,
                "emergency_guidance": "如需緊急就醫，請直接撥打 119 或前往最近的急診室",
                "locale": "zh-TW"
            }
        elif e.response.status_code >= 500:
            # 服務錯誤
            if enable_cascade:
                return _fallback_to_static_hospitals(lat, lng)

    except (httpx.ConnectTimeout, httpx.ReadTimeout):
        # 連線問題
        return {
            "status": "degraded",
            "results": [],
            "message": "連線逾時，請檢查網路",
            "offline_guidance": "請前往最近的醫療院所或急診室",
            "emergency_numbers": settings.emergency_numbers,
            "locale": "zh-TW"
        }

    # 最終降級：返回靜態醫院列表
    if enable_cascade:
        return _fallback_to_static_hospitals(lat, lng)

    return {
        "status": "error",
        "results": [],
        "message": "服務暫時無法使用",
        "emergency_numbers": settings.emergency_numbers,
        "locale": "zh-TW"
    }


def _fallback_to_static_hospitals(lat: float, lng: float) -> Dict[str, Any]:
    """靜態醫院列表降級"""
    # 台灣主要醫學中心列表
    static_hospitals = [
        {"name": "臺大醫院", "address": "台北市中正區中山南路7號", "emergency": True, "phone": "02-23123456"},
        {"name": "台北榮總", "address": "台北市北投區石牌路二段201號", "emergency": True, "phone": "02-28712121"},
        {"name": "三軍總醫院", "address": "台北市內湖區成功路二段325號", "emergency": True, "phone": "02-87923311"},
        {"name": "長庚醫院林口院區", "address": "桃園市龜山區復興街5號", "emergency": True, "phone": "03-3281200"},
        {"name": "中國醫藥大學附設醫院", "address": "台中市北區育德路2號", "emergency": True, "phone": "04-22052121"},
        {"name": "成大醫院", "address": "台南市北區勝利路138號", "emergency": True, "phone": "06-2353535"},
        {"name": "高雄醫學大學附設醫院", "address": "高雄市三民區自由一路100號", "emergency": True, "phone": "07-3121101"},
        {"name": "花蓮慈濟醫院", "address": "花蓮市中央路三段707號", "emergency": True, "phone": "03-8561825"}
    ]

    return {
        "status": "static_fallback",
        "results": static_hospitals[:5],  # 返回前5家
        "data_source": "static_emergency_list",
        "message": "使用預設醫院列表（實際距離可能有差異）",
        "emergency_numbers": ["119", "110", "112"],
        "locale": "zh-TW"
    }