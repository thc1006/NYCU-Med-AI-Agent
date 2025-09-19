"""
地理編碼與 IP 定位服務
功能：
- IP 地址 → 地理座標 (使用 ipinfo.io 與 ipapi.co 作為備援)
- 地址/地名 → 座標 (Google Geocoding API, zh-TW)
- 台灣在地化處理與精度警告
"""

import re
import warnings
import httpx
from typing import Optional, Union, Dict, Any, List
from dataclasses import dataclass
import logging
from app.config import get_settings
from app.utils.resilience import exponential_backoff_retry

logger = logging.getLogger(__name__)


@dataclass
class IPLocationResult:
    """IP 定位結果"""
    latitude: float
    longitude: float
    city: str
    country: str
    accuracy_radius_km: int = 50  # IP 定位預設精度半徑
    source: str = "ip"  # "ip" 或 "manual"


@dataclass
class GeocodeResult:
    """地理編碼結果"""
    latitude: float
    longitude: float
    formatted_address: str
    country: str
    city: str = ""
    district: str = ""
    street: str = ""
    street_number: str = ""
    postal_code: str = ""
    confidence: str = "UNKNOWN"  # ROOFTOP, RANGE_INTERPOLATED, GEOMETRIC_CENTER, APPROXIMATE
    place_id: str = ""


@dataclass
class GeocodeError:
    """地理編碼錯誤"""
    status: str
    error_message: str = ""


def _validate_ip_accuracy() -> None:
    """驗證並警告 IP 定位精度限制"""
    warnings.warn(
        "IP 定位精度有限，通常僅能提供城市級別的大致位置。"
        "建議使用者手動確認或提供更精確的地址。",
        UserWarning
    )


def _is_private_ip(ip_address: str) -> bool:
    """檢查是否為私有 IP 地址"""
    if not ip_address:
        return True

    # 私有 IP 範圍 patterns
    private_patterns = [
        r'^192\.168\.',      # 192.168.0.0/16
        r'^10\.',            # 10.0.0.0/8
        r'^172\.(1[6-9]|2[0-9]|3[01])\.',  # 172.16.0.0/12
        r'^127\.',           # 127.0.0.0/8 (localhost)
        r'^169\.254\.',      # 169.254.0.0/16 (link-local)
    ]

    return any(re.match(pattern, ip_address) for pattern in private_patterns)


def _try_ipinfo_api(ip_address: str, client: httpx.Client) -> Optional[IPLocationResult]:
    """嘗試使用 ipinfo.io API"""
    try:
        url = f"https://ipinfo.io/{ip_address}/json" if ip_address else "https://ipinfo.io/json"
        response = client.get(url, timeout=5.0)

        if response.status_code == 200:
            data = response.json()

            # 檢查是否有錯誤
            if "error" in data:
                return None

            # 解析座標
            loc = data.get("loc", "")
            if "," not in loc:
                return None

            try:
                lat_str, lng_str = loc.split(",", 1)
                latitude = float(lat_str.strip())
                longitude = float(lng_str.strip())
            except (ValueError, IndexError):
                return None

            return IPLocationResult(
                latitude=latitude,
                longitude=longitude,
                city=data.get("city", "Unknown"),
                country=data.get("country", "Unknown"),
                accuracy_radius_km=30,  # ipinfo.io 通常較準確
                source="ip"
            )

    except (httpx.RequestError, httpx.TimeoutException, ValueError, KeyError) as e:
        logger.debug(f"ipinfo.io API failed: {e}")

    return None


def _try_ipapi_api(ip_address: str, client: httpx.Client) -> Optional[IPLocationResult]:
    """嘗試使用 ipapi.co API (備援)"""
    try:
        url = f"https://ipapi.co/{ip_address}/json/" if ip_address else "https://ipapi.co/json/"
        response = client.get(url, timeout=5.0)

        if response.status_code == 200:
            data = response.json()

            # 檢查是否有錯誤
            if "error" in data:
                return None

            latitude = data.get("latitude")
            longitude = data.get("longitude")

            if latitude is None or longitude is None:
                return None

            return IPLocationResult(
                latitude=float(latitude),
                longitude=float(longitude),
                city=data.get("city", "Unknown"),
                country=data.get("country", "Unknown"),
                accuracy_radius_km=50,  # ipapi.co 精度較低
                source="ip"
            )

    except (httpx.RequestError, httpx.TimeoutException, ValueError, KeyError) as e:
        logger.debug(f"ipapi.co API failed: {e}")

    return None


def ip_geolocate(
    ip_address: Optional[str] = None,
    manual_latitude: Optional[float] = None,
    manual_longitude: Optional[float] = None,
    manual_city: Optional[str] = None
) -> Optional[IPLocationResult]:
    """
    IP 地理定位主函數

    Args:
        ip_address: IP 地址（None 時使用客戶端 IP）
        manual_latitude: 手動提供的緯度
        manual_longitude: 手動提供的經度
        manual_city: 手動提供的城市名稱

    Returns:
        IPLocationResult 或 None（定位失敗）

    Note:
        手動座標優先於 IP 定位
        IP 定位精度有限，建議使用者確認
    """
    # 手動座標優先
    if manual_latitude is not None and manual_longitude is not None:
        return IPLocationResult(
            latitude=manual_latitude,
            longitude=manual_longitude,
            city=manual_city or "User Specified",
            country="Unknown",
            accuracy_radius_km=0,  # 手動座標假設精確
            source="manual"
        )

    # 檢查 IP 地址有效性
    if not ip_address or _is_private_ip(ip_address):
        logger.debug(f"Skipping private or invalid IP: {ip_address}")
        return None

    # 發出精度警告
    _validate_ip_accuracy()

    # 嘗試多個 API（同步版本）
    try:
        with httpx.Client() as client:
            # 首先嘗試 ipinfo.io
            result = _try_ipinfo_api(ip_address, client)
            if result:
                return result

            # 備援：嘗試 ipapi.co
            result = _try_ipapi_api(ip_address, client)
            if result:
                return result

            return None
    except Exception as e:
        logger.warning(f"IP geolocation failed: {e}")
        return None


def geocode_address(address: Optional[str], language: str = "zh-TW") -> Optional[GeocodeResult]:
    """
    地址/地名 → 座標 (Google Geocoding API)

    Args:
        address: 地址或地名
        language: 語言代碼，預設 zh-TW

    Returns:
        GeocodeResult 或 None（編碼失敗）

    Note:
        使用 Google Geocoding API 進行地址編碼
        強制使用 zh-TW 語言以確保台灣在地化
    """
    # 驗證輸入
    if not address or not address.strip():
        logger.debug("Empty address provided")
        return None

    address = address.strip()

    try:
        settings = get_settings()
        api_key = settings.google_places_api_key
    except Exception as e:
        logger.error(f"Failed to get Google API key: {e}")
        return None

    # 構建請求參數
    params = {
        "address": address,
        "language": language,
        "region": "TW",  # 偏向台灣結果
        "key": api_key
    }

    try:
        with httpx.Client() as client:
            response = client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params=params,
                timeout=10.0
            )

            if response.status_code != 200:
                logger.warning(f"Geocoding API returned {response.status_code}")
                return None

            data = response.json()
            status = data.get("status", "UNKNOWN")

            if status != "OK":
                if status == "ZERO_RESULTS":
                    logger.debug(f"No results found for address: {address}")
                else:
                    error_msg = data.get("error_message", f"API status: {status}")
                    logger.warning(f"Geocoding failed: {error_msg}")
                return None

            results = data.get("results", [])
            if not results:
                logger.debug("No results in API response")
                return None

            # 取第一個結果
            result = results[0]
            return _parse_geocoding_result(result)

    except httpx.TimeoutException:
        logger.warning(f"Geocoding request timeout for address: {address}")
        return None
    except httpx.RequestError as e:
        logger.warning(f"Geocoding request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in geocoding: {e}")
        return None


def _parse_geocoding_result(result: Dict[str, Any]) -> Optional[GeocodeResult]:
    """
    解析 Google Geocoding API 結果

    Args:
        result: API 回應中的單個結果

    Returns:
        GeocodeResult 或 None
    """
    try:
        # 取得座標
        geometry = result.get("geometry", {})
        location = geometry.get("location", {})

        latitude = location.get("lat")
        longitude = location.get("lng")

        if latitude is None or longitude is None:
            logger.debug("Missing coordinates in geocoding result")
            return None

        # 取得格式化地址
        formatted_address = result.get("formatted_address", "")
        if not formatted_address.strip():
            logger.debug("Missing formatted address in geocoding result")
            return None

        # 解析地址組件
        components = result.get("address_components", [])
        parsed = _parse_address_components(components)

        # 取得信心度
        location_type = geometry.get("location_type", "UNKNOWN")

        # 取得 place_id
        place_id = result.get("place_id", "")

        return GeocodeResult(
            latitude=float(latitude),
            longitude=float(longitude),
            formatted_address=formatted_address,
            country=parsed.get("country", ""),
            city=parsed.get("city", ""),
            district=parsed.get("district", ""),
            street=parsed.get("street", ""),
            street_number=parsed.get("street_number", ""),
            postal_code=parsed.get("postal_code", ""),
            confidence=location_type,
            place_id=place_id
        )

    except (ValueError, TypeError, KeyError) as e:
        logger.warning(f"Failed to parse geocoding result: {e}")
        return None


def _parse_address_components(components: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    解析 Google Geocoding API 的地址組件

    Args:
        components: address_components 陣列

    Returns:
        解析後的地址組件字典
    """
    parsed = {
        "country": "",
        "city": "",
        "district": "",
        "street": "",
        "street_number": "",
        "postal_code": ""
    }

    for component in components:
        long_name = component.get("long_name", "")
        types = component.get("types", [])

        # 根據類型分類組件
        if "country" in types:
            parsed["country"] = long_name
        elif "administrative_area_level_1" in types:
            # 在台灣，這通常是縣市
            parsed["city"] = long_name
        elif "administrative_area_level_3" in types:
            # 在台灣，這通常是區
            parsed["district"] = long_name
        elif "route" in types:
            # 道路名稱
            parsed["street"] = long_name
        elif "street_number" in types:
            # 門牌號碼
            parsed["street_number"] = long_name
        elif "postal_code" in types:
            # 郵遞區號
            parsed["postal_code"] = long_name

    return parsed


def geocode_with_fallback(
    address: str,
    use_ip_fallback: bool = False
) -> Dict[str, Any]:
    """
    地理編碼（含降級機制）

    Args:
        address: 地址字串
        use_ip_fallback: 是否使用 IP 定位作為備援

    Returns:
        座標資訊與來源
    """
    # 嘗試 Google Geocoding
    try:
        result = geocode_address(address)
        if result:
            return {
                "source": "geocoding",
                "accuracy": "precise",
                "location": {
                    "lat": result.lat,
                    "lng": result.lng
                },
                "formatted_address": result.formatted_address
            }
    except Exception as e:
        logger.warning(f"Geocoding failed: {e}")

    # 嘗試 IP 定位備援
    if use_ip_fallback:
        try:
            ip_result = ip_geolocate()
            if ip_result:
                return {
                    "source": "ip_fallback",
                    "accuracy": "approximate",
                    "location": {
                        "lat": ip_result.lat,
                        "lng": ip_result.lng
                    },
                    "city": ip_result.city,
                    "approximate_warning": "位置為概略估計，可能與實際位置有差異"
                }
        except Exception as e:
            logger.warning(f"IP geolocation failed: {e}")

    # 返回台灣中心點作為最終備援
    return {
        "source": "default",
        "accuracy": "country_center",
        "location": {
            "lat": 23.69781,  # 台灣地理中心
            "lng": 120.960515
        },
        "message": "無法定位，使用台灣中心點"
    }


# TODO: B2 階段實作地址驗證
def validate_taiwan_address(address: str) -> bool:
    """
    驗證台灣地址格式

    Args:
        address: 待驗證的地址

    Returns:
        是否為有效的台灣地址格式

    Note:
        此函數將在 B2 階段實作
    """
    raise NotImplementedError("validate_taiwan_address will be implemented in phase B2")