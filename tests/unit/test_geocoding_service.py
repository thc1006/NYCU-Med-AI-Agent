"""
測試地理編碼服務
包含IP定位、地址編碼等功能的完整測試
"""

import pytest
import respx
import httpx
from unittest.mock import patch, Mock
from app.services.geocoding import (
    ip_geolocate,
    geocode_address,
    GeocodeResult,
    IPLocationResult,
    geocode_with_fallback,
    validate_taiwan_address
)


class TestGeocodeResult:
    """測試GeocodeResult資料模型"""

    def test_geocode_result_creation(self):
        """測試：創建GeocodeResult物件"""
        # Given
        result = GeocodeResult(
            latitude=25.0330,
            longitude=121.5654,
            formatted_address="台北市中正區",
            country="Taiwan",
            city="台北市",
            district="中正區",
            place_id="test_place_id"
        )

        # Then
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.formatted_address == "台北市中正區"
        assert result.country == "Taiwan"
        assert result.city == "台北市"
        assert result.district == "中正區"
        assert result.place_id == "test_place_id"

    def test_geocode_result_minimal_data(self):
        """測試：最小資料創建GeocodeResult"""
        # Given
        result = GeocodeResult(
            latitude=25.0330,
            longitude=121.5654,
            formatted_address="台北市中正區",
            country="Taiwan"
        )

        # Then
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.formatted_address == "台北市中正區"
        assert result.country == "Taiwan"
        assert result.city == ""
        assert result.district == ""


class TestIPGeolocation:
    """測試IP地理定位功能"""

    @respx.mock
    def test_ip_geolocate_success(self):
        """測試：IP定位成功案例"""
        # Given
        test_ip = "203.69.113.0"  # 台灣IP範例
        mock_response = {
            "loc": "25.0330,121.5654",
            "city": "Taipei",
            "country": "TW"
        }

        respx.get("https://ipinfo.io/203.69.113.0/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = ip_geolocate(test_ip)

        # Then
        assert result is not None
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.city == "Taipei"
        assert result.country == "TW"

    @respx.mock
    def test_ip_geolocate_invalid_ip(self):
        """測試：無效IP地址"""
        # Given
        invalid_ip = "invalid_ip"
        respx.get(f"https://ipinfo.io/{invalid_ip}/json").mock(
            return_value=httpx.Response(400, json={"error": "Invalid IP"})
        )

        # When
        result = ip_geolocate(invalid_ip)

        # Then
        assert result is None

    @respx.mock
    def test_ip_geolocate_network_error(self):
        """測試：網路錯誤處理"""
        # Given
        test_ip = "1.1.1.1"
        respx.get(f"https://ipinfo.io/{test_ip}/json").mock(
            side_effect=httpx.RequestError("Network error")
        )

        # When
        result = ip_geolocate(test_ip)

        # Then
        assert result is None

    def test_ip_geolocate_empty_ip(self):
        """測試：空IP地址"""
        # When
        result = ip_geolocate("")

        # Then
        assert result is None

    def test_ip_geolocate_none_ip(self):
        """測試：None IP地址"""
        # When
        result = ip_geolocate(None)

        # Then
        assert result is None


class TestAddressGeocoding:
    """測試地址地理編碼功能"""

    @respx.mock
    def test_geocode_address_success(self):
        """測試：地址編碼成功案例"""
        # Given
        address = "台北101"
        mock_response = {
            "results": [
                {
                    "geometry": {
                        "location": {
                            "lat": 25.0340,
                            "lng": 121.5645
                        }
                    },
                    "formatted_address": "台北市信義區信義路五段7號",
                    "place_id": "test_place_id",
                    "address_components": []
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = geocode_address(address)

        # Then
        assert result is not None
        assert result.latitude == 25.0340
        assert result.longitude == 121.5645
        assert "台北市信義區" in result.formatted_address

    @respx.mock
    def test_geocode_address_not_found(self):
        """測試：地址未找到"""
        # Given
        address = "不存在的地址"
        mock_response = {
            "results": [],
            "status": "ZERO_RESULTS"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = geocode_address(address)

        # Then
        assert result is None

    @respx.mock
    def test_geocode_address_api_error(self):
        """測試：API錯誤處理"""
        # Given
        address = "台北車站"
        mock_response = {
            "status": "REQUEST_DENIED",
            "error_message": "API key error"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = geocode_address(address)

        # Then
        assert result is None

    def test_geocode_address_empty_input(self):
        """測試：空地址輸入"""
        # When
        result = geocode_address("")

        # Then
        assert result is None

    def test_geocode_address_none_input(self):
        """測試：None地址輸入"""
        # When
        result = geocode_address(None)

        # Then
        assert result is None

    @respx.mock
    def test_geocode_address_network_error(self):
        """測試：網路連線錯誤"""
        # Given
        address = "台北車站"
        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            side_effect=httpx.RequestError("Connection failed")
        )

        # When
        result = geocode_address(address)

        # Then
        assert result is None


class TestGeocodeWithFallback:
    """測試地理編碼降級機制功能"""

    @respx.mock
    def test_geocode_with_fallback_success(self):
        """測試：地理編碼成功"""
        # Given
        address = "台北101"
        mock_response = {
            "results": [{
                "geometry": {"location": {"lat": 25.0340, "lng": 121.5645}},
                "formatted_address": "台北市信義區信義路五段7號",
                "place_id": "test_place_id",
                "address_components": []
            }],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # When
        result = geocode_with_fallback(address)

        # Then
        assert result["source"] == "geocoding"
        assert result["accuracy"] == "precise"
        assert result["location"]["lat"] == 25.0340
        assert result["location"]["lng"] == 121.5645

    def test_geocode_with_fallback_to_default(self):
        """測試：降級到預設位置"""
        # Given
        address = "不存在的地址"

        # When
        result = geocode_with_fallback(address, use_ip_fallback=False)

        # Then
        assert result["source"] == "default"
        assert result["accuracy"] == "country_center"
        assert result["location"]["lat"] == 23.69781
        assert result["location"]["lng"] == 120.960515


class TestIPLocationResult:
    """測試IPLocationResult資料模型"""

    def test_ip_location_result_creation(self):
        """測試：創建IPLocationResult物件"""
        # Given
        result = IPLocationResult(
            latitude=25.0330,
            longitude=121.5654,
            city="Taipei",
            country="Taiwan",
            accuracy_radius_km=30,
            source="ip"
        )

        # Then
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.city == "Taipei"
        assert result.country == "Taiwan"
        assert result.accuracy_radius_km == 30
        assert result.source == "ip"

    def test_ip_location_result_manual_source(self):
        """測試：手動來源的IPLocationResult"""
        # Given
        result = IPLocationResult(
            latitude=25.0330,
            longitude=121.5654,
            city="User Specified",
            country="Taiwan",
            accuracy_radius_km=0,
            source="manual"
        )

        # Then
        assert result.source == "manual"
        assert result.accuracy_radius_km == 0


class TestTaiwanAddressValidation:
    """測試台灣地址驗證功能"""


    def test_validate_taiwan_address_not_implemented(self):
        """測試：功能尚未實作"""
        # When & Then
        with pytest.raises(NotImplementedError):
            validate_taiwan_address("台北市中正區中山南路7號")


class TestGeoccodingErrorHandling:
    """測試地理編碼錯誤處理"""

    @patch('app.services.geocoding.httpx.get')
    def test_timeout_handling(self, mock_get):
        """測試：超時處理"""
        # Given
        mock_get.side_effect = httpx.TimeoutException("Request timeout")

        # When
        result = geocode_address("台北車站")

        # Then
        assert result is None

    @patch('app.services.geocoding.httpx.get')
    def test_http_error_handling(self, mock_get):
        """測試：HTTP錯誤處理"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )
        mock_get.return_value = mock_response

        # When
        result = geocode_address("台北車站")

        # Then
        assert result is None

    @patch('app.services.geocoding.httpx.get')
    def test_json_decode_error_handling(self, mock_get):
        """測試：JSON解析錯誤處理"""
        # Given
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_get.return_value = mock_response

        # When
        result = geocode_address("台北車站")

        # Then
        assert result is None