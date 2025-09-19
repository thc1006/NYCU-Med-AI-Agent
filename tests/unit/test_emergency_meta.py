"""
台灣急救與熱線常數的單元測試
測試重點：
- config.EMERGENCY_NUMBERS 必含 119/110/112/113/165 與描述
- GET /v1/meta/emergency 回傳含 119/110/112/113/165 與中文描述
- 驗證 112 說明為「行動電話國際緊急號碼」
- 實作 routers/meta.py 與 config 常數，保持資料來源註解
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings


class TestEmergencyNumbers:
    """台灣急救熱線測試類別"""

    @pytest.fixture(autouse=True)
    def setup_environment(self, monkeypatch):
        """設定測試環境"""
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_emergency_key")

    @pytest.fixture
    def client(self):
        """測試客戶端"""
        return TestClient(app)

    def test_config_contains_taiwan_emergency_numbers(self):
        """測試配置包含台灣急救號碼"""
        settings = get_settings()

        # 驗證 emergency_numbers 存在且包含所有必要號碼
        assert hasattr(settings, 'emergency_numbers')
        emergency_numbers = settings.emergency_numbers

        # 必須包含的台灣急救號碼
        required_numbers = ["119", "110", "112", "113", "165"]

        for number in required_numbers:
            assert number in emergency_numbers, f"Emergency number {number} is missing"

    def test_emergency_meta_endpoint_exists(self, client):
        """測試急救元數據端點存在"""
        response = client.get("/v1/meta/emergency")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_emergency_endpoint_returns_all_numbers(self, client):
        """測試急救端點返回所有必要號碼"""
        response = client.get("/v1/meta/emergency")

        assert response.status_code == 200
        data = response.json()

        # 驗證回應結構
        assert "numbers" in data
        assert "updated_at" in data
        assert "locale" in data
        assert data["locale"] == "zh-TW"

        numbers = data["numbers"]
        assert isinstance(numbers, list)
        assert len(numbers) >= 5  # 至少包含 5 個急救號碼

        # 檢查所有必要號碼都存在
        number_codes = [num["code"] for num in numbers]
        required_numbers = ["119", "110", "112", "113", "165"]

        for required in required_numbers:
            assert required in number_codes, f"Missing emergency number: {required}"

    def test_emergency_numbers_have_chinese_descriptions(self, client):
        """測試急救號碼包含中文描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        # 驗證每個號碼都有中文描述
        for number in numbers:
            assert "code" in number
            assert "description" in number
            assert "category" in number

            # 描述應該是中文且非空
            desc = number["description"]
            assert isinstance(desc, str)
            assert len(desc.strip()) > 0

            # 驗證描述包含中文字符
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in desc)
            assert has_chinese, f"Description for {number['code']} should contain Chinese characters"

    def test_emergency_112_specific_description(self, client):
        """測試 112 的特定描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        # 找到 112 號碼
        number_112 = next((num for num in numbers if num["code"] == "112"), None)
        assert number_112 is not None, "Emergency number 112 not found"

        # 驗證 112 的描述包含「行動電話」或「國際緊急」
        desc = number_112["description"]
        assert "行動電話" in desc or "國際緊急" in desc or "國際緊急號碼" in desc

    def test_emergency_119_fire_ambulance_description(self, client):
        """測試 119 消防救護描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        number_119 = next((num for num in numbers if num["code"] == "119"), None)
        assert number_119 is not None

        desc = number_119["description"]
        assert "消防" in desc or "救護" in desc or "火災" in desc

    def test_emergency_110_police_description(self, client):
        """測試 110 警察描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        number_110 = next((num for num in numbers if num["code"] == "110"), None)
        assert number_110 is not None

        desc = number_110["description"]
        assert "警察" in desc or "治安" in desc or "報案" in desc

    def test_emergency_113_womens_children_protection(self, client):
        """測試 113 婦幼保護描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        number_113 = next((num for num in numbers if num["code"] == "113"), None)
        assert number_113 is not None

        desc = number_113["description"]
        assert "婦幼" in desc or "保護" in desc or "家暴" in desc

    def test_emergency_165_anti_fraud_description(self, client):
        """測試 165 反詐騙描述"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        number_165 = next((num for num in numbers if num["code"] == "165"), None)
        assert number_165 is not None

        desc = number_165["description"]
        assert "詐騙" in desc or "反詐" in desc or "防詐" in desc

    def test_emergency_numbers_categories(self, client):
        """測試急救號碼分類"""
        response = client.get("/v1/meta/emergency")
        data = response.json()
        numbers = data["numbers"]

        # 驗證分類存在且合理
        valid_categories = ["消防救護", "警政治安", "通訊緊急", "社會保護", "防詐反詐"]

        for number in numbers:
            category = number["category"]
            assert category in valid_categories, f"Invalid category: {category}"

    def test_emergency_endpoint_response_format(self, client):
        """測試急救端點回應格式"""
        response = client.get("/v1/meta/emergency")
        data = response.json()

        # 驗證完整回應格式
        assert "numbers" in data
        assert "updated_at" in data
        assert "locale" in data
        assert "source" in data
        assert "disclaimer" in data

        # 驗證 updated_at 格式
        updated_at = data["updated_at"]
        assert isinstance(updated_at, str)
        # 應該是 ISO 格式或類似的時間戳

        # 驗證來源資訊
        source = data["source"]
        assert "台北市政府" in source or "NCC" in source or "政府" in source

        # 驗證免責聲明
        disclaimer = data["disclaimer"]
        assert "緊急" in disclaimer
        assert len(disclaimer.strip()) > 10

    def test_emergency_endpoint_includes_usage_notes(self, client):
        """測試急救端點包含使用說明"""
        response = client.get("/v1/meta/emergency")
        data = response.json()

        # 驗證包含使用說明
        assert "usage_notes" in data
        usage_notes = data["usage_notes"]

        assert isinstance(usage_notes, list)
        assert len(usage_notes) > 0

        # 檢查說明內容
        notes_text = " ".join(usage_notes)
        assert "緊急" in notes_text
        assert "撥打" in notes_text or "通報" in notes_text

    def test_emergency_endpoint_caching_headers(self, client):
        """測試急救端點快取標頭"""
        response = client.get("/v1/meta/emergency")

        # 急救號碼資訊應該可以快取
        assert "cache-control" in response.headers or "Cache-Control" in response.headers

    def test_emergency_data_consistency_with_config(self, client):
        """測試急救數據與配置的一致性"""
        # 取得配置中的急救號碼
        settings = get_settings()
        config_numbers = settings.emergency_numbers

        # 取得 API 回應
        response = client.get("/v1/meta/emergency")
        data = response.json()
        api_numbers = [num["code"] for num in data["numbers"]]

        # 確保 API 回應包含配置中的所有號碼
        for config_number in config_numbers:
            assert config_number in api_numbers, f"API missing config number: {config_number}"