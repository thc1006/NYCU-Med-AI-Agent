"""
IP 地理定位服務的單元測試
測試重點：
- 以 RESpx 模擬 ipinfo/ipapi 回傳台北市中心近似座標與城市名稱
- 失敗/逾時：回傳 None，不得 raise
- 加入 "使用者手動座標優先於IP" 的測試
- 不得直連真實 API
"""

import pytest
import httpx
import respx
from unittest.mock import patch
from app.services.geocoding import ip_geolocate, IPLocationResult


class TestIPGeolocation:
    """IP 地理定位測試類別"""

    @respx.mock
    def test_successful_ip_geolocation_taipei(self):
        """測試成功取得台北市中心座標"""
        # 模擬 ipinfo.io API 回應
        mock_response = {
            "ip": "203.69.113.0",
            "city": "Taipei",
            "region": "Taipei City",
            "country": "TW",
            "loc": "25.0330,121.5654",  # 台北市政府座標
            "timezone": "Asia/Taipei"
        }

        respx.get("https://ipinfo.io/203.69.113.0/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = ip_geolocate("203.69.113.0")

        assert result is not None
        assert isinstance(result, IPLocationResult)
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.city == "Taipei"
        assert result.country == "TW"
        assert result.accuracy_radius_km >= 1  # IP 定位精度通常較低

    @respx.mock
    def test_successful_ip_geolocation_alternative_api(self):
        """測試使用備用 API (ipapi.co) 成功取得座標"""
        # 模擬 ipapi.co API 回應
        mock_response = {
            "ip": "118.163.10.0",
            "city": "Taichung",
            "region": "Taichung City",
            "country": "TW",
            "latitude": 24.1477,
            "longitude": 120.6736,
            "timezone": "Asia/Taipei"
        }

        # 第一個 API 失敗，第二個成功
        respx.get("https://ipinfo.io/118.163.10.0/json").mock(
            return_value=httpx.Response(500, text="Service Unavailable")
        )
        respx.get("https://ipapi.co/118.163.10.0/json/").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = ip_geolocate("118.163.10.0")

        assert result is not None
        assert result.latitude == 24.1477
        assert result.longitude == 120.6736
        assert result.city == "Taichung"
        assert result.country == "TW"

    @respx.mock
    def test_ip_geolocation_timeout_returns_none(self):
        """測試API逾時時回傳 None，不拋出例外"""
        # 使用公開IP進行逾時測試
        respx.get("https://ipinfo.io/8.8.8.8/json").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        respx.get("https://ipapi.co/8.8.8.8/json/").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        result = ip_geolocate("8.8.8.8")

        assert result is None

    @respx.mock
    def test_ip_geolocation_invalid_response_returns_none(self):
        """測試無效回應時回傳 None"""
        # 模擬無效的 JSON 回應
        respx.get("https://ipinfo.io/json").mock(
            return_value=httpx.Response(200, json={"error": "Invalid IP"})
        )
        respx.get("https://ipapi.co/json/").mock(
            return_value=httpx.Response(404, text="Not Found")
        )

        result = ip_geolocate("invalid-ip")

        assert result is None

    @respx.mock
    def test_ip_geolocation_malformed_coordinates_returns_none(self):
        """測試座標格式錯誤時回傳 None"""
        # 模擬錯誤的座標格式
        mock_response = {
            "ip": "203.69.113.0",
            "city": "Taipei",
            "country": "TW",
            "loc": "invalid,coordinates"  # 錯誤格式
        }

        respx.get("https://ipinfo.io/203.69.113.0/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = ip_geolocate("203.69.113.0")

        assert result is None

    def test_manual_coordinates_override_ip_geolocation(self):
        """測試使用者手動座標優先於 IP 定位"""
        # 手動提供的座標
        manual_lat = 25.0478
        manual_lng = 121.5319

        # 當有手動座標時，應直接回傳，不呼叫 IP 定位
        result = ip_geolocate(
            ip_address=None,  # 無 IP
            manual_latitude=manual_lat,
            manual_longitude=manual_lng,
            manual_city="台北市大安區"
        )

        assert result is not None
        assert result.latitude == manual_lat
        assert result.longitude == manual_lng
        assert result.city == "台北市大安區"
        assert result.source == "manual"

    @respx.mock
    def test_manual_coordinates_fallback_to_ip_when_incomplete(self):
        """測試手動座標不完整時回退到 IP 定位"""
        mock_response = {
            "ip": "203.69.113.0",
            "city": "Taipei",
            "country": "TW",
            "loc": "25.0330,121.5654"
        }

        respx.get("https://ipinfo.io/203.69.113.0/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # 只提供 latitude，缺少 longitude
        result = ip_geolocate(
            ip_address="203.69.113.0",
            manual_latitude=25.0478,
            manual_longitude=None  # 缺少經度
        )

        # 應該回退到 IP 定位
        assert result is not None
        assert result.latitude == 25.0330  # 來自 IP 定位
        assert result.longitude == 121.5654
        assert result.source == "ip"

    @respx.mock
    def test_private_ip_address_returns_none(self):
        """測試私有 IP 位址回傳 None"""
        # 私有 IP 不會被外部 API 處理
        result = ip_geolocate("192.168.1.100")

        # 應該直接回傳 None，不嘗試 API 呼叫
        assert result is None

    @respx.mock
    def test_api_rate_limiting_fallback(self):
        """測試 API 限流時的備援機制"""
        # 第一個 API 回傳 429 (Too Many Requests)
        respx.get("https://ipinfo.io/203.69.113.0/json").mock(
            return_value=httpx.Response(429, json={"error": "Rate limited"})
        )

        # 第二個 API 成功
        mock_response = {
            "ip": "203.69.113.0",
            "city": "Taipei",
            "country": "TW",
            "latitude": 25.0330,
            "longitude": 121.5654
        }
        respx.get("https://ipapi.co/203.69.113.0/json/").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = ip_geolocate("203.69.113.0")

        assert result is not None
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654

    def test_ip_geolocation_accuracy_warning(self):
        """測試 IP 定位精度警告"""
        with pytest.warns(UserWarning, match="IP 定位精度有限"):
            # 應該在文檔或日誌中警告精度限制
            from app.services.geocoding import _validate_ip_accuracy
            _validate_ip_accuracy()

    @respx.mock
    def test_taiwan_specific_ip_ranges(self):
        """測試台灣特定IP範圍的定位"""
        # 測試台灣學術網路 IP
        mock_response = {
            "ip": "140.113.17.1",  # 交通大學 IP 範圍
            "city": "Hsinchu",
            "region": "Hsinchu City",
            "country": "TW",
            "loc": "24.7877,120.9976"
        }

        respx.get("https://ipinfo.io/140.113.17.1/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = ip_geolocate("140.113.17.1")

        assert result is not None
        assert result.city == "Hsinchu"
        assert result.country == "TW"
        assert 24.0 <= result.latitude <= 25.5  # 台灣緯度範圍
        assert 120.0 <= result.longitude <= 122.0  # 台灣經度範圍