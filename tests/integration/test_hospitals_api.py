"""
醫院搜尋API整合測試
測試附近醫院搜尋功能，包含經緯度/地址兩種模式
"""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from app.main import app


class TestHospitalsAPI:
    """醫院搜尋API測試"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @respx.mock
    async def test_nearby_hospitals_with_coordinates(self, client):
        """測試使用座標搜尋附近醫院"""
        # Mock Google Places API response
        mock_places_response = {
            "results": [
                {
                    "place_id": "ChIJ1234567890AB",
                    "name": "台大醫院",
                    "vicinity": "台北市中正區中山南路7號",
                    "geometry": {
                        "location": {"lat": 25.0408, "lng": 121.5198}
                    },
                    "rating": 4.2,
                    "user_ratings_total": 2345,
                    "types": ["hospital", "health", "point_of_interest"],
                    "opening_hours": {"open_now": True},
                    "plus_code": {
                        "compound_code": "2GR9+8Q 台北市中正區",
                        "global_code": "7QQ32GR9+8Q"
                    }
                },
                {
                    "place_id": "ChIJ0987654321DC",
                    "name": "台北榮總",
                    "vicinity": "台北市北投區石牌路二段201號",
                    "geometry": {
                        "location": {"lat": 25.1208, "lng": 121.5198}
                    },
                    "rating": 4.1,
                    "user_ratings_total": 1876,
                    "types": ["hospital", "health"],
                    "opening_hours": {"open_now": True}
                },
                {
                    "place_id": "ChIJabc123def456",
                    "name": "馬偕紀念醫院",
                    "vicinity": "台北市中山區中山北路二段92號",
                    "geometry": {
                        "location": {"lat": 25.0578, "lng": 121.5229}
                    },
                    "rating": 4.0,
                    "user_ratings_total": 1543,
                    "types": ["hospital", "health"]
                }
            ],
            "status": "OK",
            "html_attributions": []
        }

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=mock_places_response)
        )

        # 測試請求
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0339,
                "longitude": 121.5645,
                "radius": 3000
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證基本結構
        assert "hospitals" in data
        assert "total" in data
        assert "search_location" in data
        assert "disclaimer" in data
        assert "emergency_contacts" in data

        # 驗證醫院資料
        assert len(data["hospitals"]) > 0
        hospital = data["hospitals"][0]
        assert "name" in hospital
        assert "address" in hospital
        assert "distance_meters" in hospital
        assert "location" in hospital
        assert "rating" in hospital
        assert "is_open_now" in hospital

        # 驗證繁體中文輸出
        assert "台" in hospital["name"] or "醫院" in hospital["name"]
        assert "區" in hospital["address"] or "路" in hospital["address"]

        # 驗證免責聲明
        assert "僅供參考" in data["disclaimer"]
        assert "不可取代專業醫療" in data["disclaimer"]

        # 驗證緊急聯絡資訊
        assert "119" in data["emergency_contacts"]
        assert "112" in data["emergency_contacts"]
        assert "110" in data["emergency_contacts"]

    @respx.mock
    async def test_nearby_hospitals_with_address(self, client):
        """測試使用地址搜尋附近醫院"""
        # Mock Geocoding API response
        mock_geocoding_response = {
            "results": [{
                "formatted_address": "台北市信義區市府路1號",
                "geometry": {
                    "location": {"lat": 25.0375, "lng": 121.5637}
                }
            }],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_geocoding_response)
        )

        # Mock Places API response
        mock_places_response = {
            "results": [
                {
                    "place_id": "ChIJ111222333444",
                    "name": "台北市立聯合醫院仁愛院區",
                    "vicinity": "台北市大安區仁愛路四段10號",
                    "geometry": {
                        "location": {"lat": 25.0377, "lng": 121.5455}
                    },
                    "rating": 3.9,
                    "types": ["hospital", "health"]
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=mock_places_response)
        )

        # 測試請求
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "address": "台北市信義區市府路1號",
                "radius": 2000
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "hospitals" in data
        assert data["search_location"]["address"] == "台北市信義區市府路1號"
        assert len(data["hospitals"]) > 0

    @respx.mock
    async def test_rate_limit_retry_mechanism(self, client):
        """測試429錯誤的重試機制"""
        # 第一次返回429錯誤
        rate_limit_response = httpx.Response(
            429,
            json={"error_message": "OVER_QUERY_LIMIT", "status": "OVER_QUERY_LIMIT"}
        )

        # 第二次返回成功
        success_response = {
            "results": [{
                "name": "測試醫院",
                "vicinity": "測試地址",
                "geometry": {"location": {"lat": 25.0, "lng": 121.5}},
                "types": ["hospital"]
            }],
            "status": "OK"
        }

        # 設定mock順序
        route = respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json")
        route.side_effect = [
            rate_limit_response,
            httpx.Response(200, json=success_response)
        ]

        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5}
        )

        # 應該成功（在重試後）
        assert response.status_code == 200
        data = response.json()
        assert len(data["hospitals"]) > 0

    @respx.mock
    async def test_timeout_fallback(self, client):
        """測試超時回退機制"""
        # 模擬超時
        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            side_effect=httpx.TimeoutException("Connection timeout")
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5}
        )

        # 應該回退到預設醫院列表
        assert response.status_code == 200
        data = response.json()

        assert data["service_status"] == "fallback"
        assert "hospitals" in data
        assert len(data["hospitals"]) > 0

        # 預設醫院應該包含主要醫學中心
        hospital_names = [h["name"] for h in data["hospitals"]]
        assert any("台大" in name for name in hospital_names)
        assert any("榮總" in name for name in hospital_names)

    @respx.mock
    async def test_invalid_coordinates(self, client):
        """測試無效座標處理"""
        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 999, "longitude": 999}
        )

        assert response.status_code == 422
        error = response.json()
        assert "detail" in error

    @respx.mock
    async def test_invalid_address(self, client):
        """測試無效地址處理"""
        # Mock Geocoding API 返回無結果
        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json={
                "results": [],
                "status": "ZERO_RESULTS"
            })
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={"address": "不存在的地址xyz123"}
        )

        assert response.status_code == 404
        error = response.json()
        assert "無法定位該地址" in error["detail"]

    @respx.mock
    async def test_filter_by_emergency_level(self, client):
        """測試按緊急等級過濾醫院"""
        mock_response = {
            "results": [
                {
                    "name": "台大醫院急診部",
                    "vicinity": "台北市中正區",
                    "geometry": {"location": {"lat": 25.04, "lng": 121.52}},
                    "types": ["hospital", "health"],
                    "business_status": "OPERATIONAL"
                },
                {
                    "name": "診所",
                    "vicinity": "台北市大安區",
                    "geometry": {"location": {"lat": 25.03, "lng": 121.53}},
                    "types": ["doctor", "health"],
                }
            ],
            "status": "OK"
        }

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0339,
                "longitude": 121.5645,
                "emergency_only": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 只應返回醫院，不含診所
        for hospital in data["hospitals"]:
            assert "hospital" in hospital.get("types", [])

    @respx.mock
    async def test_language_setting_zh_tw(self, client):
        """測試強制使用繁體中文(zh-TW)"""
        # 捕獲實際請求以驗證參數
        captured_request = None

        def capture_request(request):
            nonlocal captured_request
            captured_request = request
            return httpx.Response(200, json={
                "results": [{
                    "name": "測試醫院",
                    "vicinity": "測試地址",
                    "geometry": {"location": {"lat": 25.0, "lng": 121.5}},
                    "types": ["hospital"]
                }],
                "status": "OK"
            })

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            side_effect=capture_request
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5}
        )

        assert response.status_code == 200
        # 驗證請求包含正確的語言參數
        assert captured_request is not None
        assert "language=zh-TW" in str(captured_request.url)

    @respx.mock
    async def test_max_results_limit(self, client):
        """測試結果數量限制"""
        # Mock返回大量結果
        many_hospitals = [
            {
                "name": f"醫院{i}",
                "vicinity": f"地址{i}",
                "geometry": {"location": {"lat": 25.0 + i*0.01, "lng": 121.5}},
                "types": ["hospital"]
            }
            for i in range(50)
        ]

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json={
                "results": many_hospitals,
                "status": "OK"
            })
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0,
                "longitude": 121.5,
                "max_results": 10
            }
        )

        assert response.status_code == 200
        data = response.json()

        # 應該限制在請求的數量
        assert len(data["hospitals"]) <= 10

    @respx.mock
    async def test_cors_headers(self, client):
        """測試CORS標頭設置"""
        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json={
                "results": [],
                "status": "OK"
            })
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5}
        )

        # 驗證CORS標頭
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"