"""
醫院搜尋增強功能測試
測試症狀分級與醫院搜尋的完整整合功能
符合 REQ-6 (Medical AI Integration) 要求
"""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any

from app.main import app
from app.domain.models import (
    SymptomQuery,
    TriageResult,
    TriageLevel,
    TriageRequest
)


class TestHospitalSearchEnhanced:
    """醫院搜尋增強功能測試套件"""

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    @respx.mock
    def test_red_flag_symptoms_trigger_emergency(self, client):
        """測試紅旗症狀觸發緊急模式"""
        # Mock Google Places API response with emergency hospitals
        mock_emergency_response = {
            "results": [
                {
                    "place_id": "ChIJEmergency123",
                    "name": "台大醫院急診部",
                    "vicinity": "台北市中正區中山南路7號",
                    "geometry": {
                        "location": {"lat": 25.0408, "lng": 121.5198}
                    },
                    "rating": 4.5,
                    "user_ratings_total": 3456,
                    "types": ["hospital", "health", "emergency"],
                    "opening_hours": {"open_now": True}
                },
                {
                    "place_id": "ChIJEmergency456",
                    "name": "台北榮總急診室",
                    "vicinity": "台北市北投區石牌路二段201號",
                    "geometry": {
                        "location": {"lat": 25.1208, "lng": 121.5198}
                    },
                    "rating": 4.3,
                    "user_ratings_total": 2876,
                    "types": ["hospital", "health", "emergency"],
                    "opening_hours": {"open_now": True}
                }
            ],
            "status": "OK"
        }

        # Mock the correct API endpoint (Places API v1)
        mock_places_v1_response = {
            "places": [
                {
                    "id": "ChIJEmergency123",
                    "displayName": {"text": "台大醫院急診部"},
                    "formattedAddress": "台北市中正區中山南路7號",
                    "location": {
                        "latitude": 25.0408,
                        "longitude": 121.5198
                    },
                    "rating": 4.5,
                    "types": ["hospital"]
                },
                {
                    "id": "ChIJEmergency456",
                    "displayName": {"text": "台北榮總急診室"},
                    "formattedAddress": "台北市北投區石牌路二段201號",
                    "location": {
                        "latitude": 25.1208,
                        "longitude": 121.5198
                    },
                    "rating": 4.3,
                    "types": ["hospital"]
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_places_v1_response)
        )

        # Test with red-flag symptoms
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0339,
                "longitude": 121.5645,
                "symptoms": ["胸痛", "呼吸困難"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify emergency mode is activated
        assert "emergency_info" in data
        assert data["emergency_info"] is not None
        assert data["emergency_info"]["is_emergency"] is True

        # Verify detected symptoms
        assert "detected_symptoms" in data["emergency_info"]
        assert "胸痛" in data["emergency_info"]["detected_symptoms"]
        assert "呼吸困難" in data["emergency_info"]["detected_symptoms"]

        # Verify emergency contacts include 119
        assert "emergency_numbers" in data["emergency_info"]
        assert "119" in data["emergency_info"]["emergency_numbers"]
        assert "112" in data["emergency_info"]["emergency_numbers"]
        assert "110" in data["emergency_info"]["emergency_numbers"]

        # Verify emergency message
        assert "emergency_message" in data["emergency_info"]
        assert "立即" in data["emergency_info"]["emergency_message"] or "緊急" in data["emergency_info"]["emergency_message"]

        # Verify search radius was adjusted to 3000m for emergency
        # This would be reflected in the API call parameters if we could inspect them

        # Verify hospitals are sorted with emergency departments first
        # The response uses "results" field (with alias to "hospitals")
        hospitals_key = "hospitals" if "hospitals" in data else "results"
        assert len(data[hospitals_key]) > 0
        first_hospital = data[hospitals_key][0]
        assert "急診" in first_hospital["name"] or "emergency" in first_hospital.get("types", [])

    @respx.mock
    def test_normal_symptoms_no_emergency(self, client):
        """測試一般症狀不觸發緊急模式"""
        # Mock regular hospital response (non-emergency)
        mock_regular_response = {
            "places": [
                {
                    "id": "ChIJRegular123",
                    "displayName": {"text": "台安醫院"},
                    "formattedAddress": "台北市松山區八德路二段424號",
                    "location": {
                        "latitude": 25.0480,
                        "longitude": 121.5514
                    },
                    "rating": 4.1,
                    "types": ["hospital"]
                },
                {
                    "id": "ChIJRegular456",
                    "displayName": {"text": "國泰綜合醫院"},
                    "formattedAddress": "台北市大安區仁愛路四段280號",
                    "location": {
                        "latitude": 25.0377,
                        "longitude": 121.5537
                    },
                    "rating": 4.0,
                    "types": ["hospital"]
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_regular_response)
        )

        # Test with normal symptoms
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0339,
                "longitude": 121.5645,
                "symptoms": ["頭痛", "流鼻水"]
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify emergency mode is NOT activated
        assert data.get("emergency_info") is None or data["emergency_info"] is None

        # Verify search radius remains default (3000)
        assert data["search_radius"] == 3000

        # Verify standard medical disclaimer (not emergency)
        assert "medical_disclaimer" in data
        assert "本服務僅供參考" in data["medical_disclaimer"]
        assert "🆘" not in data["medical_disclaimer"]  # No emergency emoji

        # Verify hospitals are returned normally
        hospitals_key = "hospitals" if "hospitals" in data else "results"
        assert len(data[hospitals_key]) > 0

    @respx.mock
    def test_backward_compatibility(self, client):
        """測試向後相容性 - 不提供症狀參數仍可正常運作"""
        # Mock standard hospital response
        mock_standard_response = {
            "places": [
                {
                    "id": "ChIJStandard123",
                    "displayName": {"text": "新光吳火獅紀念醫院"},
                    "formattedAddress": "台北市士林區文昌路95號",
                    "location": {
                        "latitude": 25.0925,
                        "longitude": 121.5225
                    },
                    "rating": 4.2,
                    "types": ["hospital"]
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_standard_response)
        )

        # Test WITHOUT symptoms parameter (backward compatibility)
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0339,
                "longitude": 121.5645
                # No symptoms parameter
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Verify standard response structure
        assert "search_center" in data
        assert "search_radius" in data
        assert "locale" in data
        assert data["locale"] == "zh-TW"

        # Verify no emergency info when no symptoms provided
        assert data.get("emergency_info") is None

        # Verify standard fields are present
        hospitals_key = "hospitals" if "hospitals" in data else "results"
        assert hospitals_key in data
        assert len(data[hospitals_key]) > 0

        # Verify hospital data structure
        hospital = data[hospitals_key][0]
        assert "name" in hospital
        assert "address" in hospital
        assert "distance_meters" in hospital

    @respx.mock
    def test_medical_disclaimer_present(self, client):
        """測試醫療免責聲明必須存在"""
        # Mock response
        mock_response = {
            "places": [
                {
                    "id": "ChIJTest123",
                    "displayName": {"text": "測試醫院"},
                    "formattedAddress": "測試地址",
                    "location": {"latitude": 25.0, "longitude": 121.5},
                    "types": ["hospital"]
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        # Test with and without symptoms
        test_cases = [
            {"latitude": 25.0, "longitude": 121.5},  # No symptoms
            {"latitude": 25.0, "longitude": 121.5, "symptoms": ["頭痛"]},  # Normal symptom
            {"latitude": 25.0, "longitude": 121.5, "symptoms": ["胸痛"]}  # Emergency symptom
        ]

        for params in test_cases:
            response = client.get("/v1/hospitals/nearby", params=params)
            assert response.status_code == 200
            data = response.json()

            # Verify disclaimer field exists
            assert "medical_disclaimer" in data
            disclaimer = data["medical_disclaimer"]

            # Verify disclaimer contains required text
            assert "本服務僅供參考" in disclaimer
            assert "不能取代專業醫療診斷" in disclaimer

            # Verify privacy notice exists
            assert "privacy_notice" in data
            assert "不會被儲存" in data["privacy_notice"]

    @respx.mock
    def test_emergency_contacts_displayed(self, client):
        """測試緊急聯絡號碼必須顯示"""
        # Mock response
        mock_response = {
            "places": [
                {
                    "id": "ChIJTest456",
                    "displayName": {"text": "測試醫院"},
                    "formattedAddress": "測試地址",
                    "location": {"latitude": 25.0, "longitude": 121.5},
                    "types": ["hospital"]
                }
            ]
        }

        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        response = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify emergency numbers are always present
        assert "emergency_numbers" in data
        emergency_numbers = data["emergency_numbers"]

        # Verify all three required numbers
        assert "119" in emergency_numbers
        assert "112" in emergency_numbers
        assert "110" in emergency_numbers

        # When emergency symptoms are provided
        response2 = client.get(
            "/v1/hospitals/nearby",
            params={"latitude": 25.0, "longitude": 121.5, "symptoms": ["胸痛"]}
        )

        data2 = response2.json()

        # Emergency info should have detailed emergency numbers
        if data2.get("emergency_info"):
            assert "emergency_numbers" in data2["emergency_info"]
            emg_nums = data2["emergency_info"]["emergency_numbers"]
            assert "119" in emg_nums
            assert "緊急醫療救護" in emg_nums["119"]

    @pytest.fixture
    def mock_env_vars(self, monkeypatch):
        """設定測試環境變數"""
        test_env = {
            "GOOGLE_PLACES_API_KEY": "test-places-api-key-enhanced",
            "GOOGLE_GEOCODING_API_KEY": "test-geocoding-api-key-enhanced",
            "DEFAULT_LANG": "zh-TW",
            "REGION": "TW",
            "LOG_LEVEL": "DEBUG"
        }

        for key, value in test_env.items():
            monkeypatch.setenv(key, value)

        return test_env

    @pytest.fixture
    def mock_emergency_hospital_response(self):
        """模擬緊急狀況醫院回應"""
        return {
            "places": [
                {
                    "id": "ChIJ_emergency_ntu_hospital",
                    "displayName": {"text": "台大醫院急診部"},
                    "formattedAddress": "台北市中正區中山南路7號",
                    "internationalPhoneNumber": "+886 2 2312 3456",
                    "nationalPhoneNumber": "02-23123456",
                    "rating": 4.5,
                    "location": {
                        "latitude": 25.0408,
                        "longitude": 121.5149
                    },
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": ["24 小時營業"]
                    },
                    "businessStatus": "OPERATIONAL",
                    "types": ["hospital", "emergency_room", "health"],
                    "primaryType": "hospital"
                },
                {
                    "id": "ChIJ_emergency_mackay_hospital",
                    "displayName": {"text": "馬偕紀念醫院急診科"},
                    "formattedAddress": "台北市中山區中山北路二段92號",
                    "internationalPhoneNumber": "+886 2 2543 3535",
                    "nationalPhoneNumber": "02-25433535",
                    "rating": 4.2,
                    "location": {
                        "latitude": 25.0617,
                        "longitude": 121.5200
                    },
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": ["24 小時營業"]
                    },
                    "businessStatus": "OPERATIONAL",
                    "types": ["hospital", "emergency_room", "health"],
                    "primaryType": "hospital"
                }
            ]
        }

    @pytest.fixture
    def mock_outpatient_hospital_response(self):
        """模擬門診醫院回應"""
        return {
            "places": [
                {
                    "id": "ChIJ_outpatient_clinic_1",
                    "displayName": {"text": "仁愛醫院家醫科"},
                    "formattedAddress": "台北市大安區仁愛路四段10號",
                    "internationalPhoneNumber": "+886 2 2708 3456",
                    "nationalPhoneNumber": "02-27083456",
                    "rating": 4.1,
                    "location": {
                        "latitude": 25.0350,
                        "longitude": 121.5437
                    },
                    "currentOpeningHours": {
                        "openNow": True,
                        "weekdayDescriptions": [
                            "星期一: 08:00 – 17:00",
                            "星期二: 08:00 – 17:00",
                            "星期三: 08:00 – 17:00",
                            "星期四: 08:00 – 17:00",
                            "星期五: 08:00 – 17:00",
                            "星期六: 08:00 – 12:00",
                            "星期日: 休息"
                        ]
                    },
                    "businessStatus": "OPERATIONAL",
                    "types": ["hospital", "health"],
                    "primaryType": "hospital"
                }
            ]
        }

    @pytest.fixture
    def mock_geocoding_response(self):
        """模擬地理編碼回應"""
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

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    @respx.mock
    def test_紅旗症狀自動觸發急診醫院搜尋(self, client, mock_env_vars,
                                      mock_emergency_hospital_response):
        """測試：紅旗症狀自動觸發急診醫院搜尋"""
        # Mock Places API for emergency hospitals
        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_emergency_hospital_response)
        )

        # Test hospital search with emergency symptoms
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0330,
                "longitude": 121.5654,
                "symptoms": ["胸痛", "呼吸困難", "暈眩"]
            }
        )

        # Then - 驗證回應
        assert response.status_code == 200
        data = response.json()

        # 驗證緊急資訊
        assert "emergency_info" in data
        assert data["emergency_info"]["is_emergency"] is True
        assert "119" in data["emergency_numbers"]
        assert "112" in data["emergency_numbers"]
        assert "110" in data["emergency_numbers"]

        # 驗證免責聲明（必須包含）
        assert "medical_disclaimer" in data
        assert "本服務僅供參考" in data["medical_disclaimer"]
        assert "不能取代專業醫療診斷" in data["medical_disclaimer"]

        # 驗證搜尋的醫院
        hospitals_key = "hospitals" if "hospitals" in data else "results"
        assert hospitals_key in data
        hospitals = data[hospitals_key]
        assert len(hospitals) >= 1

        # 驗證醫院資訊
        hospital = hospitals[0]
        assert "name" in hospital
        assert "address" in hospital
        assert "distance_meters" in hospital

        # 驗證搜尋半徑受限於3公里（緊急狀況）
        assert data["search_radius"] <= 3000

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    @respx.mock
    def test_中度症狀自動搜尋門診醫院(self, client, mock_env_vars,
                                mock_outpatient_hospital_response):
        """測試：中度症狀自動搜尋門診醫院"""
        # Mock Places API for outpatient hospitals
        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_outpatient_hospital_response)
        )

        # Test hospital search with moderate symptoms
        response = client.get(
            "/v1/hospitals/nearby",
            params={
                "latitude": 25.0330,
                "longitude": 121.5654,
                "symptoms": ["發燒", "咳嗽", "頭痛"]
            }
        )

        # Then
        assert response.status_code == 200
        data = response.json()

        # 驗證分級結果
        assert data["triage_level"] == "outpatient"

        # 驗證推薦的醫療院所
        assert "nearby_hospitals" in data
        hospitals = data["nearby_hospitals"]
        assert len(hospitals) >= 1

        # 驗證門診醫院特性
        hospital = hospitals[0]
        assert "name" in hospital
        assert "營業時間" in str(hospital) or "opening_hours" in hospital

        # 驗證科別推薦
        assert "recommended_departments" in data
        departments = data["recommended_departments"]
        assert any(dept in ["家醫科", "內科", "感染科"] for dept in departments)

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    @respx.mock
    def test_地址轉換座標後搜尋醫院(self, client, mock_env_vars,
                                mock_geocoding_response, mock_outpatient_hospital_response):
        """測試：地址自動轉換為座標後搜尋醫院"""
        # Mock Geocoding API
        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_geocoding_response)
        )

        # Mock Places API
        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_outpatient_hospital_response)
        )

        # Given - 使用地址而非座標
        request_data = {
            "symptom_text": "頭痛發燒",
            "address": "台北車站",
            "enable_hospital_search": True
        }

        # When
        response = client.post("/v1/triage/enhanced", json=request_data)

        # Then
        assert response.status_code == 200
        data = response.json()

        # 驗證地址轉換
        assert "search_location" in data
        search_location = data["search_location"]
        assert "latitude" in search_location
        assert "longitude" in search_location
        assert search_location["method"] == "address_geocoding"

        # 驗證醫院搜尋結果
        assert "nearby_hospitals" in data

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    def test_輕微症狀不自動搜尋醫院(self, client, mock_env_vars):
        """測試：輕微症狀不自動搜尋醫院"""
        # Given - 輕微症狀
        request_data = {
            "symptom_text": "有點流鼻水，輕微喉嚨癢",
            "enable_hospital_search": True
        }

        # When
        response = client.post("/v1/triage/enhanced", json=request_data)

        # Then
        assert response.status_code == 200
        data = response.json()

        # 驗證分級結果
        assert data["triage_level"] == "self_care"

        # 輕微症狀不應該自動搜尋醫院
        assert "nearby_hospitals" not in data or len(data.get("nearby_hospitals", [])) == 0

        # 但仍應提供自我照護建議
        assert "self_care_advice" in data
        assert "緊急號碼" in data  # 始終提供緊急聯絡資訊

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    @respx.mock
    def test_多語言症狀識別與醫院搜尋(self, client, mock_env_vars,
                                 mock_emergency_hospital_response):
        """測試：多語言症狀識別與醫院搜尋整合"""
        # Mock Places API
        respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
            return_value=httpx.Response(200, json=mock_emergency_hospital_response)
        )

        # 測試案例：不同語言的相同症狀
        test_cases = [
            {
                "input": "chest pain and difficulty breathing",
                "expected_level": "emergency"
            },
            {
                "input": "头痛发烧",  # 簡體中文
                "expected_level": "outpatient"
            },
            {
                "input": "我有severe headache還有nausea",  # 中英混合
                "expected_level": "outpatient"
            }
        ]

        for test_case in test_cases:
            # Given
            request_data = {
                "symptom_text": test_case["input"],
                "location": {"latitude": 25.0330, "longitude": 121.5654},
                "enable_hospital_search": True
            }

            # When
            response = client.post("/v1/triage/enhanced", json=request_data)

            # Then
            assert response.status_code == 200
            data = response.json()

            # 驗證症狀識別
            assert "detected_symptoms" in data
            detected = data["detected_symptoms"]
            assert len(detected) > 0

            # 驗證分級結果
            assert data["triage_level"] == test_case["expected_level"]

            # 如果是緊急等級，應該有醫院搜尋
            if test_case["expected_level"] == "emergency":
                assert "nearby_hospitals" in data

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    def test_症狀歷史與醫院推薦優化(self, client, mock_env_vars):
        """測試：症狀歷史追蹤對醫院推薦的優化"""
        session_id = "test-history-session-456"

        # 第一次評估
        request1 = {
            "symptom_text": "輕微頭痛",
            "session_id": session_id,
            "enable_hospital_search": True
        }

        response1 = client.post("/v1/triage/enhanced", json=request1)
        assert response1.status_code == 200

        # 第二次評估 - 症狀惡化
        request2 = {
            "symptom_text": "劇烈頭痛伴隨嘔吐和視線模糊",
            "session_id": session_id,
            "location": {"latitude": 25.0330, "longitude": 121.5654},
            "enable_hospital_search": True
        }

        with respx.mock:
            # Mock emergency hospital response
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json={
                    "places": [
                        {
                            "id": "neuro_emergency",
                            "displayName": {"text": "神經科急診專科醫院"},
                            "formattedAddress": "台北市信義區忠孝東路五段372號",
                            "rating": 4.4,
                            "location": {"latitude": 25.0330, "longitude": 121.5654}
                        }
                    ]
                })
            )

            response2 = client.post("/v1/triage/enhanced", json=request2)

        assert response2.status_code == 200
        data2 = response2.json()

        # 驗證症狀惡化警告
        assert "symptom_pattern" in data2
        pattern = data2["symptom_pattern"]
        assert pattern["trend"] == "worsening"
        assert pattern["alert"] is True

        # 驗證科別推薦因歷史調整
        assert "recommended_departments" in data2
        departments = data2["recommended_departments"]
        assert "神經內科" in departments

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    def test_免責聲明完整性驗證(self, client, mock_env_vars):
        """測試：所有增強功能回應必須包含完整免責聲明"""
        # 測試不同症狀等級的免責聲明
        test_symptoms = [
            "流鼻水",      # 自我照護
            "發燒頭痛",    # 門診
            "胸痛呼吸困難"  # 緊急
        ]

        for symptom in test_symptoms:
            # Given
            request_data = {
                "symptom_text": symptom,
                "enable_hospital_search": True
            }

            # When
            response = client.post("/v1/triage/enhanced", json=request_data)

            # Then
            assert response.status_code == 200
            data = response.json()

            # 驗證免責聲明存在
            assert "disclaimer" in data
            disclaimer = data["disclaimer"]

            # 驗證免責聲明內容
            required_phrases = [
                "僅供參考",
                "非醫療診斷",
                "專業醫療",
                "119"
            ]

            for phrase in required_phrases:
                assert phrase in disclaimer, f"Missing '{phrase}' in disclaimer for symptom: {symptom}"

            # 驗證緊急號碼資訊
            assert "emergency_numbers" in data
            emergency_numbers = data["emergency_numbers"]
            assert "119" in emergency_numbers
            assert "112" in emergency_numbers

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    def test_錯誤處理與回退機制(self, client, mock_env_vars):
        """測試：API 錯誤時的優雅回退"""
        with respx.mock:
            # Mock Places API 錯誤
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(401, json={
                    "error": {"code": 401, "message": "API key not valid"}
                })
            )

            # Given - 緊急症狀但Places API失敗
            request_data = {
                "symptom_text": "胸痛",
                "location": {"latitude": 25.0330, "longitude": 121.5654},
                "enable_hospital_search": True
            }

            # When
            response = client.post("/v1/triage/enhanced", json=request_data)

            # Then - 分級功能仍應正常運作
            assert response.status_code == 200
            data = response.json()

            # 分級結果不受影響
            assert data["triage_level"] == "emergency"
            assert "119" in data["emergency_numbers"]

            # 應有錯誤說明但不影響緊急指引
            assert "hospital_search_error" in data
            assert "emergency_guidance" in data

    @pytest.mark.skip(reason="Enhanced endpoint not implemented yet")
    @pytest.mark.integration
    def test_效能需求驗證(self, client, mock_env_vars):
        """測試：增強功能回應時間要求"""
        import time

        # Given - 緊急症狀請求
        request_data = {
            "symptom_text": "胸痛呼吸困難",
            "location": {"latitude": 25.0330, "longitude": 121.5654},
            "enable_hospital_search": True
        }

        with respx.mock:
            # Mock quick hospital response
            respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
                return_value=httpx.Response(200, json={
                    "places": [
                        {
                            "id": "quick_hospital",
                            "displayName": {"text": "快速回應醫院"},
                            "formattedAddress": "台北市中正區中山南路7號",
                            "rating": 4.5,
                            "location": {"latitude": 25.0408, "longitude": 121.5149}
                        }
                    ]
                })
            )

            # When - 測量回應時間
            start_time = time.time()
            response = client.post("/v1/triage/enhanced", json=request_data)
            end_time = time.time()

        # Then
        assert response.status_code == 200
        response_time = end_time - start_time

        # 增強功能回應時間要求（含醫院搜尋）
        assert response_time < 3.0, f"Enhanced response time {response_time}s exceeds 3s requirement"

        # 緊急情況仍需快速回應
        data = response.json()
        if data["triage_level"] == "emergency":
            assert response_time < 2.0, f"Emergency enhanced response time {response_time}s exceeds 2s requirement"

    @pytest.mark.traditional_chinese
    def test_繁體中文輸出驗證(self, client):
        """測試：所有輸出必須使用繁體中文"""
        # Test triage endpoint
        request_data = {
            "symptom_text": "頭痛發燒"
        }

        # When
        response = client.post("/v1/triage", json=request_data)

        # Then
        assert response.status_code == 200
        data = response.json()

        # 驗證關鍵欄位使用繁體中文
        text_fields = [
            data.get("advice", ""),
            data.get("disclaimer", ""),
            str(data.get("recommended_departments", [])),
            str(data.get("self_care_advice", {}))
        ]

        for text in text_fields:
            if text:
                # 檢查是否包含簡體字（不允許）
                simplified_chars = ["头", "发", "医", "药", "诊", "检"]
                for char in simplified_chars:
                    assert char not in text, f"Found simplified Chinese character '{char}' in: {text}"

                # 檢查是否包含繁體字（應該有）
                traditional_chars = ["頭", "發", "醫", "藥", "診", "檢"]
                has_traditional = any(char in text for char in traditional_chars)
                if any(word in text for word in ["頭痛", "發燒", "醫療", "診斷"]):
                    assert has_traditional, f"Should contain traditional Chinese in: {text}"