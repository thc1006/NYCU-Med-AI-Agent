"""
健康檢查端點的單元測試
測試重點：
- GET /healthz 回應 200 狀態碼與 {"status": "ok"}
- 驗證回應 header 包含 "X-Request-Id"
- 嚴禁使用 pytest.skip
- 不得存取外網
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestHealthCheck:
    """健康檢查 API 測試類別"""

    def setup_method(self):
        """每個測試方法執行前的設置"""
        self.client = TestClient(app)

    def test_healthz_returns_200_status(self):
        """測試健康檢查端點回應 200 狀態碼"""
        response = self.client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_returns_correct_json_format(self):
        """測試健康檢查端點回應正確的 JSON 格式"""
        response = self.client.get("/healthz")
        assert response.json() == {"status": "ok"}

    def test_healthz_includes_request_id_header(self):
        """測試健康檢查端點回應包含 X-Request-Id header"""
        response = self.client.get("/healthz")
        assert "X-Request-Id" in response.headers
        # 確保 X-Request-Id 不為空
        assert response.headers["X-Request-Id"] != ""
        assert len(response.headers["X-Request-Id"]) > 0

    def test_healthz_response_content_type(self):
        """測試健康檢查端點回應的 Content-Type"""
        response = self.client.get("/healthz")
        assert response.headers["content-type"] == "application/json"

    def test_healthz_response_structure_complete(self):
        """測試健康檢查端點的完整回應結構"""
        response = self.client.get("/healthz")

        # 驗證狀態碼
        assert response.status_code == 200

        # 驗證 JSON 內容
        json_data = response.json()
        assert json_data == {"status": "ok"}

        # 驗證必要的 headers
        assert "X-Request-Id" in response.headers
        assert "content-type" in response.headers

        # 驗證 X-Request-Id 格式（應該是有效的 UUID 或類似格式）
        request_id = response.headers["X-Request-Id"]
        assert isinstance(request_id, str)
        assert len(request_id) >= 8  # 最少 8 字元的識別碼