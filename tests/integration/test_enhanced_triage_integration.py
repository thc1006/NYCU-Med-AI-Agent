"""
增強版症狀分級整合測試
測試完整 API 流程與系統整合
"""

import pytest
import respx
import httpx
from fastapi.testclient import TestClient
from datetime import datetime
from app.main import app
from app.domain.models import TriageLevel


class TestEnhancedTriageAPIIntegration:
    """增強版症狀分級 API 整合測試"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @respx.mock
    def test_紅旗症狀API回應(self, client):
        """測試：紅旗症狀透過API正確回應緊急等級"""
        # Given - 紅旗症狀請求
        request_data = {
            "symptom_text": "我胸口很痛，呼吸困難",
            "age": 65,
            "gender": "M",
            "has_chronic_disease": True
        }
        
        # When - 發送API請求
        response = client.post("/v1/triage", json=request_data)
        
        # Then - 驗證回應
        assert response.status_code == 200
        data = response.json()
        
        assert data["triage_level"] == "emergency"
        assert "119" in data["emergency_numbers"]
        assert "緊急" in data["advice"]
        assert data["confidence_score"] >= 0.7  # 規則基礎系統的信心分數
        assert data["disclaimer"]  # 必須有免責聲明
        
        # 驗證緊急指引
        assert any("119" in step for step in data["next_steps"])
        if "recommended_departments" in data:
            assert "急診" in data["recommended_departments"]
    
    @respx.mock
    def test_多語言症狀處理(self, client):
        """測試：多語言輸入正確處理"""
        test_cases = [
            # 繁體中文
            {
                "input": "我頭痛發燒",
                "expected_symptoms": ["頭痛", "發燒"]
            },
            # 簡體中文
            {
                "input": "头痛发烧",
                "expected_symptoms": ["頭痛", "發燒"]
            },
            # 英文
            {
                "input": "headache and fever",
                "expected_symptoms": ["頭痛", "發燒"]
            },
            # 中英混合
            {
                "input": "我有headache還有發燒",
                "expected_symptoms": ["頭痛", "發燒"]
            }
        ]
        
        for test_case in test_cases:
            # When
            response = client.post("/v1/triage", json={
                "symptom_text": test_case["input"]
            })
            
            # Then
            assert response.status_code == 200
            data = response.json()
            
            # 驗證症狀識別
            detected = data["detected_symptoms"]
            for expected in test_case["expected_symptoms"]:
                assert any(expected in s for s in detected), \
                    f"Expected {expected} in {detected} for input: {test_case['input']}"
    
    @respx.mock
    def test_科別推薦正確性(self, client):
        """測試：科別推薦符合台灣醫療體系"""
        # Given - 不同症狀
        test_cases = [
            {
                "symptoms": "胸痛心悸",
                "expected_dept": "心臟內科"
            },
            {
                "symptoms": "咳嗽呼吸困難",
                "expected_dept": "胸腔內科"
            },
            {
                "symptoms": "頭痛暈眩",
                "expected_dept": "神經內科"
            },
            {
                "symptoms": "發燒喉嚨痛",
                "expected_dept": "耳鼻喉科"
            }
        ]
        
        for test_case in test_cases:
            # When
            response = client.post("/v1/triage", json={
                "symptom_text": test_case["symptoms"]
            })
            
            # Then
            assert response.status_code == 200
            data = response.json()
            
            departments = data.get("recommended_departments", [])
            assert test_case["expected_dept"] in departments or "家醫科" in departments, \
                f"Expected {test_case['expected_dept']} in {departments}"
    
    @respx.mock
    def test_位置基礎醫院搜尋(self, client):
        """測試：根據位置搜尋附近醫院"""
        # Mock Google Places API
        respx.post("https://places.googleapis.com/").mock(
            return_value=httpx.Response(
                200,
                json={
                    "places": [
                        {
                            "displayName": {"text": "台大醫院"},
                            "formattedAddress": "台北市中正區中山南路7號",
                            "nationalPhoneNumber": "02-23123456",
                            "rating": 4.3
                        },
                        {
                            "displayName": {"text": "馬偕醫院"},
                            "formattedAddress": "台北市中山區中山北路二段92號",
                            "nationalPhoneNumber": "02-25433535",
                            "rating": 4.1
                        }
                    ]
                }
            )
        )
        
        # Given - 緊急症狀與位置
        request_data = {
            "symptom_text": "胸痛",
            "location": {
                "latitude": 25.0330,
                "longitude": 121.5654
            },
            "include_nearby_hospitals": True
        }
        
        # When
        response = client.post("/v1/triage", json=request_data)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        
        assert data["triage_level"] == "emergency"
        
        # 驗證醫院資訊
        if "nearby_hospitals" in data:
            hospitals = data["nearby_hospitals"]
            assert len(hospitals) > 0
            # 驗證醫院資訊結構
            for hospital in hospitals:
                assert "name" in hospital
                assert "address" in hospital
    
    @respx.mock
    def test_症狀歷史追蹤功能(self, client):
        """測試：症狀歷史追蹤與惡化偵測"""
        session_id = "test-session-123"
        
        # 第一次評估 - 輕微症狀
        response1 = client.post("/v1/triage", json={
            "symptom_text": "輕微頭痛",
            "session_id": session_id
        })
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["triage_level"] == "self-care"
        
        # 第二次評估 - 症狀惡化
        response2 = client.post("/v1/triage", json={
            "symptom_text": "劇烈頭痛嘔吐",
            "session_id": session_id
        })
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["triage_level"] == "emergency"
        
        # 查詢歷史
        history_response = client.get(f"/v1/triage/history/{session_id}")
        if history_response.status_code == 200:
            history = history_response.json()
            assert len(history) >= 2
            # 驗證惡化警告
            if "pattern" in history:
                assert history["pattern"]["trend"] == "worsening"
                assert history["pattern"]["alert"] == True
    
    @respx.mock
    def test_免責聲明必存在(self, client):
        """測試：所有回應必須包含免責聲明"""
        # Given - 任意症狀
        test_inputs = [
            "頭痛",
            "胸痛",
            "咳嗽",
            ""  # 空輸入
        ]
        
        for symptom in test_inputs:
            # When
            response = client.post("/v1/triage", json={
                "symptom_text": symptom
            })
            
            # Then
            assert response.status_code == 200
            data = response.json()
            
            # 驗證免責聲明
            assert "disclaimer" in data
            assert data["disclaimer"]
            assert "僅供參考" in data["disclaimer"]
            assert "非醫療診斷" in data["disclaimer"]
            assert "119" in data["disclaimer"]
    
    @respx.mock
    def test_錯誤處理和回退(self, client):
        """測試：錯誤處理和優雅回退"""
        # Given - 無效請求
        invalid_requests = [
            # 年齡超出範圍
            {
                "symptom_text": "頭痛",
                "age": 200
            },
            # 無效性別
            {
                "symptom_text": "頭痛",
                "gender": "invalid"
            },
            # 無效位置
            {
                "symptom_text": "頭痛",
                "location": {
                    "latitude": 200,  # 無效緯度
                    "longitude": 121
                }
            }
        ]
        
        for request in invalid_requests:
            # When
            response = client.post("/v1/triage", json=request)
            
            # Then - 應該回傳錯誤但不應當機
            assert response.status_code in [400, 422]
            error_data = response.json()
            assert "detail" in error_data
    
    @respx.mock
    def test_效能要求(self, client):
        """測試：回應時間符合要求"""
        import time
        
        # Given
        request_data = {
            "symptom_text": "胸痛呼吸困難"
        }
        
        # When
        start_time = time.time()
        response = client.post("/v1/triage", json=request_data)
        end_time = time.time()
        
        # Then
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # 驗證回應時間 < 2秒（根據需求）
        assert response_time < 2.0, f"Response time {response_time}s exceeds 2s requirement"
        
        # 緊急情況應該更快
        data = response.json()
        if data["triage_level"] == "emergency":
            assert response_time < 1.0, f"Emergency response time {response_time}s exceeds 1s requirement"