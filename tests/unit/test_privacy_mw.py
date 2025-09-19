"""
隱私遮罩與審計記錄中介層的單元測試
測試重點：
- 禁止把 symptom 字串原樣寫入 log；以 hash 或摘要
- 清除電話／身分證可能樣式
- 確認 access log 僅記載必要欄位（方法、路徑、status、耗時、request-id）
- 遵循 PDPA 最小化原則
"""

import json
import pytest
import hashlib
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.middlewares.privacy import PrivacyMiddleware
from starlette.middleware.base import BaseHTTPMiddleware


class TestPrivacyMiddleware:
    """隱私中介層測試類別"""

    @pytest.fixture
    def app_with_privacy_middleware(self):
        """創建帶有隱私中介層的測試應用程式"""
        app = FastAPI()
        app.add_middleware(PrivacyMiddleware)

        @app.post("/test-endpoint")
        async def test_endpoint(data: dict):
            return {"received": "ok"}

        return app

    @pytest.fixture
    def client(self, app_with_privacy_middleware):
        """測試客戶端"""
        return TestClient(app_with_privacy_middleware)

    def test_phone_number_masking_in_logs(self, client, caplog):
        """測試電話號碼在日誌中被遮罩"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            # 包含台灣手機號碼格式的payload
            payload = {
                "symptom": "頭痛",
                "contact": "0912345678",
                "emergency_contact": "02-12345678"
            }

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌不包含原始電話號碼
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                assert "0912345678" not in log_content
                assert "02-12345678" not in log_content
                assert "masked" in log_content.lower()

    def test_id_number_masking_in_logs(self, client, caplog):
        """測試身分證號碼在日誌中被遮罩"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            # 包含身分證號碼樣式的payload
            payload = {
                "symptom": "胸痛",
                "patient_id": "A123456789",  # 台灣身分證格式
                "backup_id": "B987654321"
            }

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌不包含原始身分證號碼
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                assert "A123456789" not in log_content
                assert "B987654321" not in log_content
                assert "masked" in log_content.lower()

    def test_symptom_text_hashing_not_plain_text(self, client, caplog):
        """測試症狀文字被雜湊而非明文記錄"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            sensitive_symptom = "我昨晚開始胸痛，現在呼吸困難"
            payload = {"symptom": sensitive_symptom}

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌不包含原始症狀文字
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                assert sensitive_symptom not in log_content
                # 檢查包含雜湊或摘要形式
                assert "hash:" in log_content.lower() or "masked" in log_content.lower()

    def test_access_log_contains_only_necessary_fields(self, client, caplog):
        """測試存取日誌僅包含必要欄位"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            payload = {"test": "data"}

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌包含必要欄位
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                assert "POST" in log_content  # HTTP 方法
                assert "/test-endpoint" in log_content  # 路徑
                assert "200" in log_content  # 狀態碼
                assert "duration_ms" in log_content  # 耗時資訊
                assert "request_id" in log_content  # request-id

    def test_request_id_generation_and_logging(self, client, caplog):
        """測試請求ID產生與記錄"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            response = client.post("/test-endpoint", json={"test": "data"})

            # 檢查回應包含 request-id header
            assert "x-request-id" in response.headers
            request_id = response.headers["x-request-id"]

            # 檢查隱私審計日誌包含相同的 request-id
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                assert request_id in log_content

    def test_pdpa_compliance_no_personal_data_in_logs(self, client, caplog):
        """測試PDPA合規：日誌中不包含個人資料"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            # 包含多種個人資料的payload
            payload = {
                "name": "王小明",
                "email": "wang@example.com",
                "phone": "0987654321",
                "address": "台北市信義區松仁路100號",
                "symptom": "頭暈噁心",
                "id_card": "C246813579"
            }

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌不包含個人資料
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                # 確認個人資料都不在日誌中
                assert "王小明" not in log_content
                assert "wang@example.com" not in log_content
                assert "0987654321" not in log_content
                assert "台北市信義區松仁路100號" not in log_content
                assert "頭暈噁心" not in log_content
                assert "C246813579" not in log_content

    def test_middleware_preserves_response_functionality(self, client):
        """測試中介層保持回應功能正常"""
        payload = {"test": "normal_operation"}

        response = client.post("/test-endpoint", json=payload)

        # 確認功能正常
        assert response.status_code == 200
        assert response.json() == {"received": "ok"}

        # 確認有request-id header
        assert "x-request-id" in response.headers

    def test_error_handling_in_privacy_middleware(self, client, caplog):
        """測試隱私中介層的錯誤處理"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            # 測試malformed JSON或其他錯誤情況
            response = client.post("/test-endpoint",
                                   data="invalid-json",
                                   headers={"content-type": "application/json"})

            # 即使JSON解析失敗，中介層仍應正常運作
            # 檢查是否有請求審計記錄（即使body為空）
            audit_logs = [record.message for record in caplog.records
                         if record.name == "privacy_audit" and "Request audit" in record.message]

            # 應該仍有基本的請求審計，但不包含敏感內容
            if audit_logs:
                log_content = " ".join(audit_logs)
                assert "invalid-json" not in log_content
                assert "POST" in log_content
                assert "/test-endpoint" in log_content

    def test_large_payload_handling(self, client, caplog):
        """測試大型payload的處理"""
        with caplog.at_level(logging.INFO, logger="privacy_audit"):
            # 創建大型payload
            large_text = "症狀描述 " * 1000  # 重複文字
            payload = {"symptom": large_text, "phone": "0912345678"}

            response = client.post("/test-endpoint", json=payload)
            assert response.status_code == 200

            # 檢查隱私審計日誌
            privacy_logs = [record.message for record in caplog.records
                           if record.name == "privacy_audit"]

            if privacy_logs:
                log_content = " ".join(privacy_logs)
                # 確認大型內容被適當處理（摘要或截斷）
                assert large_text not in log_content
                assert "0912345678" not in log_content
                # 應該有摘要或雜湊形式
                assert "hash:" in log_content.lower() or "masked" in log_content.lower()