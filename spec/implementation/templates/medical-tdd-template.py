# Medical TDD Template
# Template for Test-Driven Development with medical safety validation

import pytest
import asyncio
import httpx
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import respx
from typing import Dict, Any, List

# Test fixtures for medical AI components
@pytest.fixture
def medical_app():
    """Create test medical app instance"""
    from fastapi_medical_service import create_medical_app
    return create_medical_app()

@pytest.fixture
def test_client(medical_app):
    """Create test client"""
    return TestClient(medical_app)

@pytest.fixture
def taiwan_config():
    """Taiwan configuration fixture"""
    return {
        "language": "zh-TW",
        "region": "TW",
        "emergency_numbers": {
            "119": "消防局救護車",
            "110": "警察局",
            "112": "行動電話國際緊急號碼",
            "113": "保護專線",
            "165": "反詐騙諮詢專線"
        }
    }

@pytest.fixture
def emergency_symptoms():
    """Emergency symptom test data"""
    return [
        "胸痛且冒冷汗",
        "嚴重呼吸困難",
        "突然劇烈頭痛",
        "意識不清楚",
        "大量出血"
    ]

@pytest.fixture
def routine_symptoms():
    """Routine symptom test data"""
    return [
        "輕微喉嚨痛",
        "流鼻水",
        "輕微頭痛",
        "疲倦",
        "輕微咳嗽"
    ]

# Medical safety test utilities
class MedicalSafetyTestUtils:
    """Utilities for testing medical safety compliance"""

    @staticmethod
    def assert_no_medical_diagnosis(response_text: str):
        """Assert response contains no definitive medical diagnosis"""
        dangerous_phrases = [
            "你患有", "診斷為", "確診", "罹患", "病症是",
            "你的疾病", "確定是", "肯定是", "一定是"
        ]

        for phrase in dangerous_phrases:
            assert phrase not in response_text, f"Response contains dangerous medical phrase: {phrase}"

    @staticmethod
    def assert_contains_disclaimer(response: Dict[str, Any]):
        """Assert response contains medical disclaimer"""
        assert "disclaimer" in response
        assert "119" in response["disclaimer"]
        assert "專業醫療" in response["disclaimer"]

    @staticmethod
    def assert_emergency_response(response: Dict[str, Any]):
        """Assert proper emergency response format"""
        assert response["level"] == "emergency"
        assert response["should_call_119"] is True
        assert "119" in response["advice"]

    @staticmethod
    def assert_taiwan_compliance(response: Dict[str, Any]):
        """Assert Taiwan localization compliance"""
        assert response["locale"] == "zh-TW"
        assert "emergency_numbers" in response
        assert "119" in response["emergency_numbers"]
        assert "110" in response["emergency_numbers"]
        assert "112" in response["emergency_numbers"]

# TDD Test Classes

class TestHealthCheck:
    """TDD tests for health check endpoint"""

    def test_health_check_returns_200(self, test_client):
        """Test health check returns 200 OK"""
        response = test_client.get("/healthz")
        assert response.status_code == 200

    def test_health_check_returns_correct_format(self, test_client):
        """Test health check returns correct response format"""
        response = test_client.get("/healthz")
        data = response.json()

        assert data["status"] == "ok"
        assert data["locale"] == "zh-TW"
        assert "request_id" in data
        assert "timestamp" in data

    def test_health_check_includes_taiwan_compliance(self, test_client):
        """Test health check includes Taiwan compliance elements"""
        response = test_client.get("/healthz")
        data = response.json()

        MedicalSafetyTestUtils.assert_taiwan_compliance(data)

class TestEmergencyInfo:
    """TDD tests for emergency information endpoint"""

    def test_emergency_info_returns_taiwan_numbers(self, test_client, taiwan_config):
        """Test emergency info returns Taiwan emergency numbers"""
        response = test_client.get("/v1/meta/emergency")
        assert response.status_code == 200

        data = response.json()
        expected_numbers = taiwan_config["emergency_numbers"]

        for number, description in expected_numbers.items():
            assert number in data["emergency_numbers"]
            assert data["emergency_numbers"][number] == description

    def test_emergency_info_includes_required_fields(self, test_client):
        """Test emergency info includes all required fields"""
        response = test_client.get("/v1/meta/emergency")
        data = response.json()

        assert "emergency_numbers" in data
        assert "disclaimer" in data
        assert "locale" in data
        assert data["locale"] == "zh-TW"

class TestSymptomTriage:
    """TDD tests for symptom triage with medical safety"""

    def test_emergency_symptoms_trigger_emergency_response(self, test_client, emergency_symptoms):
        """Test emergency symptoms trigger proper emergency response"""
        for symptom in emergency_symptoms:
            response = test_client.post("/v1/triage", json={"symptom_text": symptom})
            assert response.status_code == 200

            data = response.json()
            MedicalSafetyTestUtils.assert_emergency_response(data)

    def test_routine_symptoms_get_appropriate_response(self, test_client, routine_symptoms):
        """Test routine symptoms get appropriate non-emergency response"""
        for symptom in routine_symptoms:
            response = test_client.post("/v1/triage", json={"symptom_text": symptom})
            assert response.status_code == 200

            data = response.json()
            assert data["level"] in ["routine", "self-care"]
            assert data["should_call_119"] is False

    def test_triage_response_has_no_medical_diagnosis(self, test_client, routine_symptoms):
        """Test triage responses contain no definitive medical diagnosis"""
        for symptom in routine_symptoms:
            response = test_client.post("/v1/triage", json={"symptom_text": symptom})
            data = response.json()

            MedicalSafetyTestUtils.assert_no_medical_diagnosis(data["advice"])

    def test_triage_response_includes_disclaimer(self, test_client):
        """Test all triage responses include medical disclaimer"""
        response = test_client.post("/v1/triage", json={"symptom_text": "頭痛"})
        data = response.json()

        MedicalSafetyTestUtils.assert_contains_disclaimer(data)

    def test_triage_validates_input_length(self, test_client):
        """Test triage validates input length"""
        # Empty input
        response = test_client.post("/v1/triage", json={"symptom_text": ""})
        assert response.status_code == 422

        # Too long input
        long_text = "症狀" * 1000
        response = test_client.post("/v1/triage", json={"symptom_text": long_text})
        assert response.status_code == 422

    def test_triage_masks_personal_information(self, test_client):
        """Test triage masks personal information in input"""
        symptom_with_pii = "我的身分證是A123456789，電話0912345678，症狀是頭痛"
        response = test_client.post("/v1/triage", json={"symptom_text": symptom_with_pii})
        assert response.status_code == 200

        # Should not expose PII in any logs or responses
        data = response.json()
        assert "A123456789" not in str(data)
        assert "0912345678" not in str(data)

class TestHospitalSearch:
    """TDD tests for hospital search functionality"""

    @respx.mock
    def test_hospital_search_with_coordinates(self, test_client):
        """Test hospital search with latitude/longitude"""
        # Mock Google Places API response
        mock_response = {
            "results": [
                {
                    "name": "台大醫院",
                    "vicinity": "台北市中正區",
                    "rating": 4.5,
                    "opening_hours": {"open_now": True},
                    "geometry": {"location": {"lat": 25.0339, "lng": 121.5645}}
                }
            ]
        }

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        response = test_client.post("/v1/hospitals/nearby", json={
            "latitude": 25.0330,
            "longitude": 121.5654,
            "radius_km": 5
        })

        assert response.status_code == 200
        data = response.json()

        assert "hospitals" in data
        assert "search_location" in data
        assert len(data["hospitals"]) > 0

    @respx.mock
    def test_hospital_search_with_address(self, test_client):
        """Test hospital search with address geocoding"""
        # Mock Geocoding API response
        geocoding_response = {
            "results": [
                {
                    "geometry": {
                        "location": {"lat": 25.0330, "lng": 121.5654}
                    }
                }
            ]
        }

        # Mock Places API response
        places_response = {
            "results": [
                {
                    "name": "台北醫院",
                    "vicinity": "台北市",
                    "rating": 4.2,
                    "geometry": {"location": {"lat": 25.0330, "lng": 121.5654}}
                }
            ]
        }

        respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=geocoding_response)
        )

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=places_response)
        )

        response = test_client.post("/v1/hospitals/nearby", json={
            "address": "台北市中正區",
            "radius_km": 3
        })

        assert response.status_code == 200
        data = response.json()

        MedicalSafetyTestUtils.assert_taiwan_compliance(data)

    def test_hospital_search_requires_location(self, test_client):
        """Test hospital search requires either coordinates or address"""
        response = test_client.post("/v1/hospitals/nearby", json={
            "radius_km": 5
        })

        assert response.status_code == 400

    def test_hospital_search_validates_radius(self, test_client):
        """Test hospital search validates radius limits"""
        # Too small radius
        response = test_client.post("/v1/hospitals/nearby", json={
            "latitude": 25.0330,
            "longitude": 121.5654,
            "radius_km": 0
        })
        assert response.status_code == 422

        # Too large radius
        response = test_client.post("/v1/hospitals/nearby", json={
            "latitude": 25.0330,
            "longitude": 121.5654,
            "radius_km": 100
        })
        assert response.status_code == 422

class TestPrivacyCompliance:
    """TDD tests for PDPA privacy compliance"""

    def test_responses_include_request_id(self, test_client):
        """Test all responses include request ID for audit trail"""
        response = test_client.get("/healthz")
        assert "X-Request-ID" in response.headers

    def test_responses_include_privacy_headers(self, test_client):
        """Test responses include privacy compliance headers"""
        response = test_client.get("/healthz")
        assert "X-Privacy-Policy" in response.headers
        assert response.headers["X-Privacy-Policy"] == "PDPA-compliant"

    def test_error_responses_protect_privacy(self, test_client):
        """Test error responses don't expose sensitive information"""
        response = test_client.get("/nonexistent")
        assert response.status_code == 404

        # Should not expose internal server details
        error_text = response.text.lower()
        assert "traceback" not in error_text
        assert "internal" not in error_text

class TestMedicalSafetyService:
    """TDD tests for medical safety service"""

    def test_emergency_keyword_detection(self):
        """Test emergency keyword detection"""
        from fastapi_medical_service import MedicalSafetyService

        safety_service = MedicalSafetyService()

        # Should detect emergency keywords
        assert safety_service.check_emergency_keywords("胸痛") is True
        assert safety_service.check_emergency_keywords("嚴重呼吸困難") is True

        # Should not trigger on routine symptoms
        assert safety_service.check_emergency_keywords("輕微頭痛") is False
        assert safety_service.check_emergency_keywords("流鼻水") is False

    def test_emergency_response_format(self):
        """Test emergency response format"""
        from fastapi_medical_service import MedicalSafetyService

        safety_service = MedicalSafetyService()
        response = safety_service.get_emergency_response()

        assert response.level == "emergency"
        assert response.should_call_119 is True
        assert "119" in response.advice

class TestTaiwanLocalization:
    """TDD tests for Taiwan localization service"""

    @respx.mock
    async def test_geocoding_uses_taiwan_parameters(self):
        """Test geocoding uses Taiwan-specific parameters"""
        from fastapi_medical_service import TaiwanLocalizationService

        mock_response = {
            "results": [
                {
                    "geometry": {
                        "location": {"lat": 25.0330, "lng": 121.5654}
                    }
                }
            ]
        }

        request_mock = respx.get("https://maps.googleapis.com/maps/api/geocode/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = TaiwanLocalizationService()
        result = await service.geocode_taiwan_address("台北市中正區")

        # Verify Taiwan-specific parameters were used
        assert request_mock.calls[0].request.url.params["region"] == "TW"
        assert request_mock.calls[0].request.url.params["language"] == "zh-TW"

    @respx.mock
    async def test_hospital_search_uses_taiwan_parameters(self):
        """Test hospital search uses Taiwan-specific parameters"""
        from fastapi_medical_service import TaiwanLocalizationService

        mock_response = {"results": []}

        request_mock = respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json=mock_response)
        )

        service = TaiwanLocalizationService()
        await service.find_nearby_hospitals(25.0330, 121.5654)

        # Verify Taiwan-specific parameters were used
        assert request_mock.calls[0].request.url.params["language"] == "zh-TW"
        assert request_mock.calls[0].request.url.params["region"] == "TW"

# Integration tests
class TestIntegration:
    """Integration tests for medical AI system"""

    @pytest.mark.asyncio
    async def test_full_emergency_workflow(self, test_client):
        """Test complete emergency symptom workflow"""
        # 1. Submit emergency symptom
        response = test_client.post("/v1/triage", json={
            "symptom_text": "胸痛且呼吸困難"
        })

        assert response.status_code == 200
        triage_data = response.json()

        # 2. Verify emergency response
        MedicalSafetyTestUtils.assert_emergency_response(triage_data)

        # 3. Get emergency contact info
        emergency_response = test_client.get("/v1/meta/emergency")
        emergency_data = emergency_response.json()

        # 4. Verify emergency numbers are available
        assert "119" in emergency_data["emergency_numbers"]

    @respx.mock
    async def test_full_routine_workflow(self, test_client):
        """Test complete routine symptom workflow"""
        # Mock hospital search
        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        # 1. Submit routine symptom
        triage_response = test_client.post("/v1/triage", json={
            "symptom_text": "輕微頭痛"
        })

        assert triage_response.status_code == 200
        triage_data = triage_response.json()

        # 2. Verify non-emergency response
        assert triage_data["should_call_119"] is False

        # 3. Search for nearby hospitals
        hospital_response = test_client.post("/v1/hospitals/nearby", json={
            "latitude": 25.0330,
            "longitude": 121.5654
        })

        assert hospital_response.status_code == 200
        hospital_data = hospital_response.json()

        # 4. Verify Taiwan compliance throughout
        MedicalSafetyTestUtils.assert_taiwan_compliance(triage_data)
        MedicalSafetyTestUtils.assert_taiwan_compliance(hospital_data)

# Performance tests
class TestPerformance:
    """Performance tests for medical AI system"""

    def test_triage_response_time(self, test_client):
        """Test triage response time is acceptable"""
        import time

        start_time = time.time()
        response = test_client.post("/v1/triage", json={
            "symptom_text": "頭痛"
        })
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Should respond within 2 seconds

    @respx.mock
    def test_hospital_search_response_time(self, test_client):
        """Test hospital search response time is acceptable"""
        import time

        respx.get("https://maps.googleapis.com/maps/api/place/nearbysearch/json").mock(
            return_value=httpx.Response(200, json={"results": []})
        )

        start_time = time.time()
        response = test_client.post("/v1/hospitals/nearby", json={
            "latitude": 25.0330,
            "longitude": 121.5654
        })
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 3.0  # Should respond within 3 seconds

# Test runner and utilities
if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([
        __file__,
        "-v",
        "--cov=fastapi_medical_service",
        "--cov-report=html",
        "--cov-report=term"
    ])