"""
症狀分級 API 端到端測試
測試重點：
- 緊急症狀返回 emergency 級別與 119 提醒
- 輕症返回 self-care 級別與觀察建議
- 中文輸出與免責聲明
- 完整請求與快速評估端點
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestTriageAPI:
    """症狀分級 API 測試類別"""

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """設定測試環境"""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_triage_api_key_12345")

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    def test_triage_emergency_chest_pain(self, client):
        """測試緊急症狀 - 胸痛"""
        request_data = {
            "symptom_text": "胸口很痛，呼吸困難，冒冷汗",
            "age": 55,
            "gender": "M"
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 驗證緊急等級
        assert data["triage_level"] == "emergency"
        assert "119" in data["advice"]
        assert "急診" in data["advice"] or "立即" in data["advice"]

        # 驗證檢測到的症狀
        assert "detected_symptoms" in data
        assert any("胸" in s for s in data["detected_symptoms"])
        assert any("呼吸" in s for s in data["detected_symptoms"])

        # 驗證急救號碼
        assert "119" in data["emergency_numbers"]

        # 驗證免責聲明
        assert data["disclaimer"] is not None
        assert "參考" in data["disclaimer"]

        # 驗證其他必要欄位
        assert data["request_id"] is not None
        assert data["timestamp"] is not None
        assert data["locale"] == "zh-TW"

    def test_triage_mild_symptoms(self, client):
        """測試輕微症狀 - 流鼻水"""
        request_data = {
            "symptom_text": "流鼻水，喉嚨有點癢"
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 驗證自我照護等級
        assert data["triage_level"] == "self-care"
        assert "休息" in data["advice"] or "觀察" in data["advice"]

        # 驗證檢測到的症狀
        assert "流鼻水" in data["detected_symptoms"]

        # 驗證下一步建議
        assert len(data["next_steps"]) > 0
        assert any("觀察" in step or "休息" in step for step in data["next_steps"])

    def test_triage_moderate_fever(self, client):
        """測試中度症狀 - 發燒"""
        request_data = {
            "symptom_text": "發燒38.5度，全身痠痛，頭痛",
            "age": 30,
            "has_chronic_disease": False
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 驗證門診等級
        assert data["triage_level"] == "outpatient"
        assert "門診" in data["advice"] or "就醫" in data["advice"]

        # 驗證推薦科別
        assert data["recommended_departments"] is not None
        assert len(data["recommended_departments"]) > 0

    def test_triage_with_nearby_hospitals(self, client):
        """測試包含附近醫院搜尋"""
        request_data = {
            "symptom_text": "頭很痛",
            "include_nearby_hospitals": True,
            "location": {
                "latitude": 25.0339,
                "longitude": 121.5645
            }
        }

        # 由於需要 mock Places API，這裡只測試請求格式
        response = client.post("/v1/triage", json=request_data)

        # 應該不會失敗，即使醫院搜尋失敗
        assert response.status_code == 200
        data = response.json()
        assert "triage_level" in data

    def test_quick_assessment(self, client):
        """測試快速評估端點"""
        response = client.post(
            "/v1/triage/quick",
            params={"symptom_text": "肚子痛，想吐"}
        )

        assert response.status_code == 200
        data = response.json()

        # 驗證簡化回應格式
        assert "level" in data
        assert "advice" in data
        assert "next_steps" in data
        assert len(data["next_steps"]) <= 3  # 只顯示前3個步驟
        assert data["locale"] == "zh-TW"

    def test_quick_assessment_emergency(self, client):
        """測試快速評估 - 緊急狀況"""
        response = client.post(
            "/v1/triage/quick",
            params={"symptom_text": "昏迷不醒"}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["level"] == "emergency"
        assert "119" in data["emergency_numbers"]

    def test_get_emergency_symptoms_list(self, client):
        """測試取得緊急症狀列表"""
        response = client.get("/v1/triage/symptoms/emergency")

        assert response.status_code == 200
        data = response.json()

        assert "emergency_symptoms" in data
        assert isinstance(data["emergency_symptoms"], list)
        assert len(data["emergency_symptoms"]) > 0

        # 驗證包含關鍵緊急症狀
        symptoms = data["emergency_symptoms"]
        assert "胸痛" in symptoms
        assert "呼吸困難" in symptoms
        assert "昏迷" in symptoms

        assert data["locale"] == "zh-TW"

    def test_get_mild_symptoms_list(self, client):
        """測試取得輕微症狀列表"""
        response = client.get("/v1/triage/symptoms/mild")

        assert response.status_code == 200
        data = response.json()

        assert "mild_symptoms" in data
        assert isinstance(data["mild_symptoms"], list)
        assert len(data["mild_symptoms"]) > 0

        # 驗證包含輕微症狀
        symptoms = data["mild_symptoms"]
        assert "流鼻水" in symptoms
        assert "喉嚨痛" in symptoms

        # 驗證自我照護建議
        assert "self_care_tips" in data
        assert len(data["self_care_tips"]) > 0

    def test_get_department_mapping(self, client):
        """測試取得科別對照表"""
        response = client.get("/v1/triage/departments")

        assert response.status_code == 200
        data = response.json()

        assert "departments" in data
        departments = data["departments"]

        # 驗證科別資訊
        assert "急診" in departments
        assert "家醫科" in departments
        assert "心臟內科" in departments

        # 驗證科別結構
        for dept_name, dept_info in departments.items():
            assert "symptoms" in dept_info
            assert "description" in dept_info
            assert isinstance(dept_info["symptoms"], list)

    def test_triage_empty_symptom(self, client):
        """測試空症狀文字"""
        request_data = {
            "symptom_text": ""
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 應該返回自我照護等級
        assert data["triage_level"] == "self-care"
        assert "請描述" in data["advice"]

    def test_triage_with_medications(self, client):
        """測試包含用藥資訊"""
        request_data = {
            "symptom_text": "頭痛",
            "medications": ["阿斯匹靈", "降血壓藥"]
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 基本功能應該正常
        assert "triage_level" in data
        assert "advice" in data

    def test_triage_with_chronic_disease(self, client):
        """測試慢性病患者"""
        request_data = {
            "symptom_text": "胸悶",
            "age": 65,
            "has_chronic_disease": True
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 胸悶應該是緊急
        assert data["triage_level"] == "emergency"

    def test_triage_confidence_score(self, client):
        """測試信心分數"""
        request_data = {
            "symptom_text": "發燒"
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "confidence_score" in data
        assert 0.0 <= data["confidence_score"] <= 1.0

    def test_triage_chinese_output_only(self, client):
        """測試輸出為繁體中文"""
        request_data = {
            "symptom_text": "chest pain"  # 英文輸入
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 輸出應該是中文
        # 檢查是否沒有簡體字
        simplified_chars = ['医', '药', '诊', '头', '发', '护']
        full_text = data["advice"] + " ".join(data["next_steps"])

        for char in simplified_chars:
            assert char not in full_text

    def test_triage_validation_errors(self, client):
        """測試輸入驗證"""
        # 測試缺少必要欄位
        response = client.post("/v1/triage", json={})

        assert response.status_code == 422  # Validation error

        # 測試無效年齡
        request_data = {
            "symptom_text": "頭痛",
            "age": -5
        }

        response = client.post("/v1/triage", json=request_data)
        assert response.status_code == 422

    def test_quick_assessment_validation(self, client):
        """測試快速評估驗證"""
        # 缺少症狀文字
        response = client.post("/v1/triage/quick")
        assert response.status_code == 422

        # 空字串
        response = client.post("/v1/triage/quick", params={"symptom_text": ""})
        assert response.status_code == 422

    def test_triage_multiple_symptoms(self, client):
        """測試多重症狀"""
        request_data = {
            "symptom_text": "胸痛、呼吸困難、頭暈、冒冷汗"
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # 應該檢測到多個症狀
        assert len(data["detected_symptoms"]) >= 2
        # 有胸痛應該是緊急
        assert data["triage_level"] == "emergency"

    def test_triage_response_headers(self, client):
        """測試回應標頭"""
        request_data = {
            "symptom_text": "咳嗽"
        }

        response = client.post("/v1/triage", json=request_data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"