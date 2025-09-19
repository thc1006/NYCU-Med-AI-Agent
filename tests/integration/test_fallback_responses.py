"""
測試服務降級與備援回應
測試重點：
- Places API 失敗時返回空結果
- Geocoding 失敗時返回預設座標
- 症狀分級 API 降級為純規則判斷
- 錯誤訊息清晰且包含建議
"""

import pytest
import httpx
import respx
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app
from app.services.places import nearby_hospitals_with_fallback
from app.services.geocoding import geocode_with_fallback
from app.domain.triage import triage_with_fallback


class TestFallbackResponses:
    """服務降級測試"""

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    def test_places_api_fallback_on_429(self):
        """測試 Places API 限流時的降級回應"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(429, json={
                    "error": {
                        "code": 429,
                        "message": "Resource exhausted"
                    }
                })
            )

            result = nearby_hospitals_with_fallback(
                lat=25.04,
                lng=121.56,
                radius=3000
            )

            # 應該返回降級結果而非失敗
            assert result["status"] == "degraded"
            assert result["results"] == []
            assert "請稍後再試" in result["message"]
            assert result["emergency_guidance"] is not None
            assert "119" in result["emergency_numbers"]

    def test_places_api_fallback_on_timeout(self):
        """測試 Places API 逾時的降級回應"""
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                side_effect=httpx.ConnectTimeout("Connection timeout")
            )

            result = nearby_hospitals_with_fallback(
                lat=25.04,
                lng=121.56,
                radius=3000
            )

            assert result["status"] == "degraded"
            assert result["results"] == []
            assert "連線逾時" in result["message"]
            # 提供離線指引
            assert "offline_guidance" in result
            assert "急診" in result["offline_guidance"]

    def test_geocoding_fallback_on_failure(self):
        """測試 Geocoding 失敗時的降級回應"""
        with respx.mock:
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(500, json={
                    "error_message": "Internal server error"
                })
            )

            result = geocode_with_fallback(
                address="台北市信義區",
                use_ip_fallback=True
            )

            # 應該嘗試 IP 定位作為備援
            assert result["source"] == "ip_fallback"
            assert result["accuracy"] == "approximate"
            assert "location" in result
            # 提醒用戶精度限制
            assert "approximate_warning" in result

    def test_geocoding_complete_failure_fallback(self):
        """測試 Geocoding 完全失敗的處理"""
        with respx.mock:
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(500)
            )
            respx.get("https://ipapi.co/json/").mock(
                side_effect=httpx.ConnectTimeout()
            )

            result = geocode_with_fallback(
                address="台北市信義區",
                use_ip_fallback=True
            )

            # 返回台灣中心點作為最終備援
            assert result["source"] == "default"
            assert result["location"]["lat"] == 23.69781  # 台灣中心點
            assert result["location"]["lng"] == 120.960515
            assert result["accuracy"] == "country_center"

    def test_triage_api_fallback_to_rules(self, client):
        """測試症狀分級 API 降級為規則判斷"""
        # 模擬 LLM 服務失敗
        with patch('app.services.llm.AnthropicProvider.analyze') as mock_llm:
            mock_llm.side_effect = httpx.ConnectTimeout("LLM timeout")

            response = client.post("/v1/triage", json={
                "symptom_text": "胸痛、呼吸困難",
                "use_llm_enhancement": True  # 請求使用 LLM 增強
            })

            assert response.status_code == 200
            data = response.json()

            # 應該降級為規則判斷
            assert data["triage_level"] == "emergency"  # 規則仍能識別緊急
            assert data["analysis_mode"] == "rules_only"
            assert "服務降級" in data.get("service_notice", "")
            assert "119" in data["advice"]

    def test_cascading_fallback_chain(self):
        """測試級聯降級鏈"""
        # 第一選擇：Google Places
        # 第二選擇：健保署資料
        # 第三選擇：靜態緊急醫院列表

        with respx.mock:
            # Google Places 失敗
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(503)
            )

            # 健保署 API 也失敗
            respx.get("https://data.nhi.gov.tw/resource/api").mock(
                side_effect=httpx.ConnectTimeout()
            )

            result = nearby_hospitals_with_fallback(
                lat=25.04,
                lng=121.56,
                radius=3000,
                enable_cascade=True
            )

            # 應該返回靜態緊急醫院列表
            assert result["status"] == "static_fallback"
            assert len(result["results"]) > 0
            assert result["results"][0]["name"] == "臺大醫院"
            assert result["results"][0]["emergency"] == True
            assert result["data_source"] == "static_emergency_list"

    def test_partial_service_degradation(self, client):
        """測試部分服務降級"""
        with respx.mock:
            # Places 失敗但 Geocoding 正常
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(429)
            )
            respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
                return_value=httpx.Response(200, json={
                    "results": [{
                        "geometry": {
                            "location": {"lat": 25.04, "lng": 121.56}
                        },
                        "formatted_address": "台北市信義區"
                    }],
                    "status": "OK"
                })
            )

            response = client.get("/v1/hospitals/nearby", params={
                "address": "台北市信義區"
            })

            assert response.status_code == 200
            data = response.json()

            # Geocoding 成功但醫院搜尋降級
            assert "location_resolved" in data
            assert data["location_resolved"] == True
            assert data["hospitals_status"] == "degraded"
            assert len(data["results"]) == 0
            assert "service_notice" in data

    def test_fallback_with_cached_data(self):
        """測試使用快取資料作為降級"""
        from app.services.cache import ResponseCache

        cache = ResponseCache(ttl=300)  # 5分鐘快取

        # 第一次成功並快取
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json={
                    "places": [{
                        "displayName": {"text": "臺大醫院"},
                        "formattedAddress": "台北市中正區",
                        "location": {"latitude": 25.04, "longitude": 121.52}
                    }]
                })
            )

            result1 = nearby_hospitals_with_fallback(
                lat=25.04,
                lng=121.56,
                radius=3000,
                cache=cache
            )
            assert len(result1["results"]) == 1

        # 第二次失敗但使用快取
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(503)
            )

            result2 = nearby_hospitals_with_fallback(
                lat=25.04,
                lng=121.56,
                radius=3000,
                cache=cache
            )

            assert result2["status"] == "cached"
            assert len(result2["results"]) == 1
            assert result2["results"][0]["name"] == "臺大醫院"
            assert "cache_age" in result2

    def test_fallback_response_format_consistency(self, client):
        """測試降級回應格式一致性"""
        # 正常回應
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json={
                    "places": [{
                        "displayName": {"text": "醫院A"},
                        "formattedAddress": "地址A",
                        "location": {"latitude": 25.04, "longitude": 121.52}
                    }]
                })
            )

            response_normal = client.get("/v1/hospitals/nearby", params={
                "lat": 25.04, "lng": 121.56
            })

        # 降級回應
        with respx.mock:
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(429)
            )

            response_degraded = client.get("/v1/hospitals/nearby", params={
                "lat": 25.04, "lng": 121.56
            })

        # 驗證回應結構一致
        normal_data = response_normal.json()
        degraded_data = response_degraded.json()

        # 相同的頂層欄位
        assert set(normal_data.keys()) == set(degraded_data.keys())
        assert "results" in normal_data and "results" in degraded_data
        assert "emergencyNumbers" in normal_data and "emergencyNumbers" in degraded_data
        assert "locale" in normal_data and "locale" in degraded_data

    def test_user_friendly_error_messages(self, client):
        """測試用戶友好的錯誤訊息"""
        error_scenarios = [
            (429, "系統繁忙，請稍後再試"),
            (500, "服務暫時無法使用"),
            (503, "服務維護中"),
            ("timeout", "連線逾時，請檢查網路")
        ]

        for scenario in error_scenarios:
            with respx.mock:
                if isinstance(scenario[0], int):
                    respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                        return_value=httpx.Response(scenario[0])
                    )
                else:
                    respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                        side_effect=httpx.ConnectTimeout()
                    )

                response = client.get("/v1/hospitals/nearby", params={
                    "lat": 25.04, "lng": 121.56
                })

                assert response.status_code == 200  # 降級但不失敗
                data = response.json()
                assert scenario[1] in data.get("user_message", "")
                assert "建議" in data.get("suggestions", "")