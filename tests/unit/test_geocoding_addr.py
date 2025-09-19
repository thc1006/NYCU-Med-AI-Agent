"""
Google Geocoding API 地址轉座標服務的單元測試
測試重點：
- language=zh-TW，模擬「臺北市信義區」等台灣地址案例
- 不允許回傳空地址卻有座標
- 中文地址 zh-TW 取得正確座標與標準化地址
- 無效地址返回 404-like 錯誤模型（自定義）
- 使用 RESpx 模擬，不得連接真實 Google API
"""

import pytest
import httpx
import respx
from typing import Optional
from unittest.mock import patch
from app.services.geocoding import geocode_address, GeocodeResult, GeocodeError


class TestGoogleGeocoding:
    """Google Geocoding API 測試類別"""

    @pytest.fixture(autouse=True)
    def mock_api_key(self, monkeypatch):
        """自動為所有測試提供模擬的 API key"""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_api_key_12345")

    @respx.mock
    def test_successful_geocoding_taipei_xinyi_district(self):
        """測試成功地理編碼台北市信義區"""
        # 模擬 Google Geocoding API 回應
        mock_response = {
            "results": [
                {
                    "address_components": [
                        {"long_name": "信義區", "short_name": "信義區", "types": ["administrative_area_level_3"]},
                        {"long_name": "台北市", "short_name": "台北市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "short_name": "TW", "types": ["country"]}
                    ],
                    "formatted_address": "台灣台北市信義區",
                    "geometry": {
                        "location": {
                            "lat": 25.0330,
                            "lng": 121.5654
                        },
                        "location_type": "APPROXIMATE",
                        "viewport": {
                            "northeast": {"lat": 25.0481, "lng": 121.5845},
                            "southwest": {"lat": 25.0179, "lng": 121.5463}
                        }
                    },
                    "place_id": "ChIJXxOqLKupQjQRBN8mLb6yq4g",
                    "types": ["administrative_area_level_3"]
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("臺北市信義區", language="zh-TW")

        assert result is not None
        assert isinstance(result, GeocodeResult)
        assert result.latitude == 25.0330
        assert result.longitude == 121.5654
        assert result.formatted_address == "台灣台北市信義區"
        assert result.country == "台灣"
        assert result.city == "台北市"
        assert result.district == "信義區"
        assert result.confidence == "APPROXIMATE"

    @respx.mock
    def test_successful_geocoding_taichung_address(self):
        """測試成功地理編碼台中市地址"""
        mock_response = {
            "results": [
                {
                    "address_components": [
                        {"long_name": "408", "short_name": "408", "types": ["postal_code"]},
                        {"long_name": "南屯區", "short_name": "南屯區", "types": ["administrative_area_level_3"]},
                        {"long_name": "台中市", "short_name": "台中市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "short_name": "TW", "types": ["country"]}
                    ],
                    "formatted_address": "408台灣台中市南屯區",
                    "geometry": {
                        "location": {"lat": 24.1477, "lng": 120.6736},
                        "location_type": "GEOMETRIC_CENTER"
                    },
                    "place_id": "ChIJQ8gd8kQKaTQR1p9_-kL_WYE",
                    "types": ["postal_code"]
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("台中市南屯區", language="zh-TW")

        assert result is not None
        assert result.latitude == 24.1477
        assert result.longitude == 120.6736
        assert "台中市" in result.formatted_address
        assert "南屯區" in result.formatted_address
        assert result.country == "台灣"

    @respx.mock
    def test_geocoding_specific_address_with_street(self):
        """測試具體街道地址的地理編碼"""
        mock_response = {
            "results": [
                {
                    "address_components": [
                        {"long_name": "100", "short_name": "100", "types": ["street_number"]},
                        {"long_name": "松仁路", "short_name": "松仁路", "types": ["route"]},
                        {"long_name": "信義區", "short_name": "信義區", "types": ["administrative_area_level_3"]},
                        {"long_name": "台北市", "short_name": "台北市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "short_name": "TW", "types": ["country"]}
                    ],
                    "formatted_address": "110台灣台北市信義區松仁路100號",
                    "geometry": {
                        "location": {"lat": 25.0338, "lng": 121.5683},
                        "location_type": "ROOFTOP"
                    },
                    "place_id": "ChIJyb7HbDSpQjQRnUiWaDiGZCg",
                    "types": ["street_address"]
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("台北市信義區松仁路100號", language="zh-TW")

        assert result is not None
        assert result.latitude == 25.0338
        assert result.longitude == 121.5683
        assert "松仁路100號" in result.formatted_address
        assert result.confidence == "ROOFTOP"  # 最高精度

    @respx.mock
    def test_geocoding_invalid_address_returns_error(self):
        """測試無效地址返回錯誤"""
        mock_response = {
            "results": [],
            "status": "ZERO_RESULTS"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("無效的地址測試12345", language="zh-TW")

        assert result is None

    @respx.mock
    def test_geocoding_api_error_handling(self):
        """測試 API 錯誤處理"""
        mock_response = {
            "results": [],
            "status": "REQUEST_DENIED",
            "error_message": "The provided API key is invalid."
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("台北市", language="zh-TW")

        assert result is None

    @respx.mock
    def test_geocoding_network_timeout_handling(self):
        """測試網路逾時處理"""
        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            side_effect=httpx.TimeoutException("Request timeout")
        )

        result = geocode_address("台北市", language="zh-TW")

        assert result is None

    @respx.mock
    def test_geocoding_http_error_handling(self):
        """測試 HTTP 錯誤處理"""
        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )

        result = geocode_address("台北市", language="zh-TW")

        assert result is None

    def test_geocoding_requires_language_zh_tw(self):
        """測試確保使用 zh-TW 語言參數"""
        # 這個測試檢查預設語言參數
        with respx.mock:
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(200, json={"results": [], "status": "ZERO_RESULTS"})
            )

            result = geocode_address("測試地址")

            # 檢查請求是否包含正確的語言參數
            assert len(respx.calls) == 1
            request = respx.calls[0].request
            assert "language=zh-TW" in str(request.url)

    @respx.mock
    def test_geocoding_validates_coordinates_exist(self):
        """測試驗證座標存在（不允許空地址卻有座標的情況）"""
        # 模擬有問題的回應：有座標但地址為空
        mock_response = {
            "results": [
                {
                    "address_components": [],
                    "formatted_address": "",  # 空地址
                    "geometry": {
                        "location": {"lat": 25.0338, "lng": 121.5683}
                    }
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("異常測試地址", language="zh-TW")

        # 應該拒絕這種回應
        assert result is None

    @respx.mock
    def test_geocoding_taiwan_address_components_parsing(self):
        """測試台灣地址組件解析"""
        mock_response = {
            "results": [
                {
                    "address_components": [
                        {"long_name": "No. 1", "short_name": "1", "types": ["street_number"]},
                        {"long_name": "中正路", "short_name": "中正路", "types": ["route"]},
                        {"long_name": "中正區", "short_name": "中正區", "types": ["administrative_area_level_3"]},
                        {"long_name": "台北市", "short_name": "台北市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "short_name": "TW", "types": ["country", "political"]}
                    ],
                    "formatted_address": "100台灣台北市中正區中正路1號",
                    "geometry": {
                        "location": {"lat": 25.0425, "lng": 121.5170}
                    }
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("台北市中正區中正路1號", language="zh-TW")

        assert result is not None
        assert result.country == "台灣"
        assert result.city == "台北市"
        assert result.district == "中正區"
        assert result.street == "中正路"
        assert result.street_number == "No. 1"

    @respx.mock
    def test_geocoding_kaohsiung_address(self):
        """測試高雄市地址地理編碼"""
        mock_response = {
            "results": [
                {
                    "address_components": [
                        {"long_name": "前金區", "short_name": "前金區", "types": ["administrative_area_level_3"]},
                        {"long_name": "高雄市", "short_name": "高雄市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "short_name": "TW", "types": ["country"]}
                    ],
                    "formatted_address": "801台灣高雄市前金區",
                    "geometry": {
                        "location": {"lat": 22.6331, "lng": 120.2876}
                    }
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        result = geocode_address("高雄市前金區", language="zh-TW")

        assert result is not None
        assert result.city == "高雄市"
        assert result.district == "前金區"
        assert 22.0 <= result.latitude <= 23.5  # 高雄緯度範圍
        assert 120.0 <= result.longitude <= 121.0  # 高雄經度範圍

    def test_geocoding_empty_address_validation(self):
        """測試空地址驗證"""
        result = geocode_address("", language="zh-TW")
        assert result is None

        result = geocode_address("   ", language="zh-TW")
        assert result is None

        result = geocode_address(None, language="zh-TW")
        assert result is None