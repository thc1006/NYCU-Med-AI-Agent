"""
醫院搜尋 API 端到端測試
測試重點：
- 整合 geocoding（IP/地址）→ places →（可選）健保名冊
- 測試不同搜尋方式：座標、地址、IP
- 錯誤處理與邊界情況
- 回傳結構驗證
"""

import pytest
import httpx
import respx
import json
import tempfile
import os
from fastapi.testclient import TestClient
from app.main import app


class TestHospitalsAPI:
    """醫院搜尋 API 測試類別"""

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """設定測試環境"""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_hospitals_api_key_12345")

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @pytest.fixture
    def mock_places_response(self):
        """模擬 Places API 回應"""
        return {
            "places": [
                {
                    "id": "ChIJK_taipei_hospital",
                    "displayName": {"text": "台大醫院"},
                    "formattedAddress": "台北市中正區中山南路7號",
                    "internationalPhoneNumber": "+886 2 2312 3456",
                    "rating": 4.3,
                    "location": {
                        "latitude": 25.0408,
                        "longitude": 121.5149
                    },
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": ["24 小時營業"]
                    },
                    "businessStatus": "OPERATIONAL"
                },
                {
                    "id": "ChIJL_veterans_hospital",
                    "displayName": {"text": "榮民總醫院"},
                    "formattedAddress": "台北市北投區石牌路二段201號",
                    "internationalPhoneNumber": "+886 2 2875 7808",
                    "rating": 4.1,
                    "location": {
                        "latitude": 25.1172,
                        "longitude": 121.5240
                    },
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": ["24 小時營業"]
                    },
                    "businessStatus": "OPERATIONAL"
                }
            ]
        }

    @pytest.fixture
    def mock_geocoding_response(self):
        """模擬 Geocoding API 回應"""
        return {
            "results": [
                {
                    "formatted_address": "台北市中正區中山南路7號",
                    "geometry": {
                        "location": {
                            "lat": 25.0408,
                            "lng": 121.5149
                        }
                    },
                    "address_components": [
                        {"long_name": "台北市", "types": ["administrative_area_level_1"]},
                        {"long_name": "台灣", "types": ["country"]},
                        {"long_name": "中正區", "types": ["administrative_area_level_2"]}
                    ]
                }
            ],
            "status": "OK"
        }

    @pytest.fixture
    def mock_ip_response(self):
        """模擬 IP 定位回應"""
        return {
            "ip": "203.69.113.0",
            "city": "Taipei",
            "region": "Taiwan",
            "country": "TW",
            "loc": "25.0478,121.5170",
            "timezone": "Asia/Taipei"
        }

    def test_search_nearby_hospitals_with_coordinates(self, client, mock_places_response):
        """測試直接座標搜尋醫院"""
        with respx.mock:
            # 模擬 Places API
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 測試請求
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "radius": 3000,
                    "max_results": 10
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 驗證回應結構
            assert "results" in data
            assert "search_center" in data
            assert "search_radius" in data
            assert "total_count" in data
            assert "locale" in data
            assert "emergency_numbers" in data
            assert "search_method" in data

            # 驗證搜尋中心
            assert data["search_center"]["latitude"] == 25.0478
            assert data["search_center"]["longitude"] == 121.5170
            assert data["search_method"] == "coordinates"

            # 驗證結果
            assert len(data["results"]) == 2
            assert data["total_count"] == 2
            assert data["locale"] == "zh-TW"

            # 驗證第一個醫院資訊
            hospital = data["results"][0]
            assert hospital["name"] == "台大醫院"
            assert hospital["address"] == "台北市中正區中山南路7號"
            assert hospital["phone"] == "+886 2 2312 3456"
            assert hospital["rating"] == 4.3
            assert "distance_meters" in hospital

            # 驗證急救資訊
            assert "119" in data["emergency_numbers"]
            assert "emergency_reminder" in data

    def test_search_nearby_hospitals_with_address(self, client, mock_places_response, mock_geocoding_response):
        """測試地址搜尋醫院"""
        with respx.mock:
            # 模擬 Geocoding API
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(200, json=mock_geocoding_response)
            )

            # 模擬 Places API
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 測試請求
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "address": "台北車站",
                    "radius": 5000
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 驗證地址geocoding結果
            assert data["search_method"] == "address"
            assert data["search_center"]["latitude"] == 25.0408
            assert data["search_center"]["longitude"] == 121.5149

            # 驗證搜尋結果
            assert len(data["results"]) == 2

    def test_search_nearby_hospitals_with_ip(self, client, mock_places_response, mock_ip_response):
        """測試 IP 定位搜尋醫院"""
        with respx.mock:
            # 模擬 IP 定位 API (TestClient 會用 testclient 作為 IP)
            respx.get("https://ipinfo.io/testclient/json").mock(
                return_value=httpx.Response(200, json=mock_ip_response)
            )

            # 模擬 Places API
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 測試請求
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "use_ip": True,
                    "radius": 3000
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 驗證 IP 定位結果
            assert data["search_method"] == "ip"
            assert "latitude" in data["search_center"]
            assert "longitude" in data["search_center"]

    def test_search_nearby_hospitals_without_nhia(self, client, mock_places_response):
        """測試不包含健保資訊的搜尋"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "include_nhia": False
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 驗證沒有健保特約資訊
            for hospital in data["results"]:
                assert "is_contracted" not in hospital
                assert "hospital_code" not in hospital

    def test_search_nearby_hospitals_validation_errors(self, client):
        """測試參數驗證錯誤"""
        # 無效緯度
        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 95.0, "longitude": 121.5170}
        )
        assert response.status_code == 400
        assert "latitude" in response.json()["detail"].lower()

        # 無效經度
        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0478, "longitude": 185.0}
        )
        assert response.status_code == 400
        assert "longitude" in response.json()["detail"].lower()

        # 無效半徑
        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0478, "longitude": 121.5170, "radius": 99}
        )
        assert response.status_code == 422  # Pydantic validation error

        # 無任何位置參數
        response = client.get("/v1/hospitals/nearby")
        assert response.status_code == 400
        assert "Must provide" in response.json()["detail"]

    def test_search_nearby_hospitals_geocoding_failure(self, client):
        """測試地址geocoding失敗"""
        with respx.mock:
            # 模擬 Geocoding 失敗
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(200, json={"results": [], "status": "ZERO_RESULTS"})
            )

            response = client.get(
                "/v1/hospitals/nearby",
                params={"address": "不存在的地址12345"}
            )

            assert response.status_code == 400
            assert "Unable to geocode" in response.json()["detail"]

    def test_search_nearby_hospitals_places_api_error(self, client):
        """測試 Places API 錯誤"""
        with respx.mock:
            # 模擬 Places API 401 錯誤
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(401, json={
                    "error": {"code": 401, "message": "API key not valid"}
                })
            )

            response = client.get(
                "/v1/hospitals/nearby",
                params={"latitude": 25.0478, "longitude": 121.5170}
            )

            assert response.status_code == 500
            assert "Hospital search error" in response.json()["detail"]

    def test_search_nearby_hospitals_simple(self, client, mock_places_response):
        """測試簡化版搜尋"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            response = client.get(
                "/v1/hospitals/nearby/simple",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "max_results": 5
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 驗證簡化格式
            assert "hospitals" in data
            assert "count" in data
            assert "emergency_numbers" in data
            assert "locale" in data

            # 驗證醫院資訊簡化
            hospital = data["hospitals"][0]
            expected_fields = {"name", "address", "distance_meters"}
            assert expected_fields.issubset(hospital.keys())

            # 不應該包含複雜欄位
            assert "id" not in hospital
            assert "is_contracted" not in hospital

    def test_get_emergency_medical_info(self, client):
        """測試緊急醫療資訊端點"""
        response = client.get("/v1/hospitals/emergency-info")

        assert response.status_code == 200
        data = response.json()

        # 驗證緊急號碼資訊
        assert "emergency_numbers" in data
        emergency_numbers = data["emergency_numbers"]
        assert len(emergency_numbers) >= 4

        # 驗證119資訊
        number_119 = next((n for n in emergency_numbers if n["number"] == "119"), None)
        assert number_119 is not None
        assert "消防救護" in number_119["description"]
        assert "火災" in number_119["usage"] or "救護車" in number_119["usage"]

        # 驗證其他必要資訊
        assert "emergency_guidelines" in data
        assert "when_to_call_119" in data
        assert "hospital_levels" in data
        assert data["locale"] == "zh-TW"

        # 驗證醫院等級說明
        hospital_levels = data["hospital_levels"]
        assert "醫學中心" in hospital_levels
        assert "區域醫院" in hospital_levels

    def test_hospital_search_priority_order(self, client, mock_places_response):
        """測試搜尋優先級順序"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 同時提供座標和地址，應該使用座標
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "address": "台北車站",
                    "use_ip": True
                }
            )

            assert response.status_code == 200
            data = response.json()

            # 應該使用座標（優先級最高）
            assert data["search_method"] == "coordinates"
            assert data["search_center"]["latitude"] == 25.0478
            assert data["search_center"]["longitude"] == 121.5170

    def test_hospital_search_with_radius_limits(self, client, mock_places_response):
        """測試搜尋半徑限制"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 測試最小半徑
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "radius": 100
                }
            )
            assert response.status_code == 200

            # 測試最大半徑
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "radius": 50000
                }
            )
            assert response.status_code == 200

    def test_hospital_search_max_results_limit(self, client, mock_places_response):
        """測試最大結果數量限制"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            # 測試正常範圍
            response = client.get(
                "/v1/hospitals/nearby",
                params={
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "max_results": 15
                }
            )
            assert response.status_code == 200

            # 驗證結果不超過請求數量
            data = response.json()
            assert len(data["results"]) <= 15

    def test_hospital_search_response_headers(self, client, mock_places_response):
        """測試回應標頭"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json=mock_places_response)
            )

            response = client.get(
                "/v1/hospitals/nearby",
                params={"latitude": 25.0478, "longitude": 121.5170}
            )

            assert response.status_code == 200

            # 驗證 Content-Type
            assert response.headers["content-type"] == "application/json"

            # 應該有請求ID（由PrivacyMiddleware添加）
            # 具體的標頭名稱依中介層實作而定