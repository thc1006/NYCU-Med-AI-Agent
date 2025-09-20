"""
隱私中介軟體單元測試
測試範圍：
- 敏感資料遮罩功能
- PDPA合規性驗證
- 審計日誌記錄
- 個人識別資訊保護
- 症狀文字雜湊化
- 電話、身分證、Email遮罩
- 請求追蹤與監控
"""

import pytest
import json
import hashlib
import uuid
from unittest.mock import Mock, patch, AsyncMock
from fastapi import Request, Response
from fastapi.testclient import TestClient
from fastapi.applications import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from app.middlewares.privacy import PrivacyMiddleware


class TestPrivacyMiddleware:
    """隱私中介軟體測試類別"""

    @pytest.fixture
    def privacy_middleware(self):
        """隱私中介軟體實例"""
        app = FastAPI()
        return PrivacyMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """模擬HTTP請求"""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url.path = "/v1/triage"
        request.headers = {
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 TestAgent",
            "x-forwarded-for": "192.168.1.100"
        }
        request.client.host = "192.168.1.100"
        return request

    @pytest.fixture
    def mock_response(self):
        """模擬HTTP回應"""
        response = Mock(spec=Response)
        response.status_code = 200
        response.headers = {}
        return response

    @pytest.fixture
    def sensitive_request_data(self):
        """包含敏感資料的請求數據"""
        return {
            "symptoms": "胸痛、呼吸困難",
            "name": "陳小明",
            "phone": "0912345678",
            "id_card": "A123456789",
            "email": "test@example.com",
            "address": "台北市信義區市府路1號",
            "age": 30,
            "emergency_contact": "0987654321",
            "medical_history": "高血壓病史"
        }

    def test_phone_pattern_masking(self, privacy_middleware):
        """測試電話號碼遮罩"""
        # 台灣手機號碼
        assert privacy_middleware._mask_patterns_in_text("我的電話是0912345678") == "我的電話是***masked***"

        # 台灣市話
        assert privacy_middleware._mask_patterns_in_text("公司電話02-12345678") == "公司電話***masked***"

        # 國際格式
        assert privacy_middleware._mask_patterns_in_text("國際電話+886-912345678") == "國際電話***masked***"

        # 多個電話號碼
        text = "手機0912345678，市話02-87654321"
        result = privacy_middleware._mask_patterns_in_text(text)
        assert "***masked***" in result
        assert "0912345678" not in result
        assert "02-87654321" not in result

    def test_id_pattern_masking(self, privacy_middleware):
        """測試身分證號碼遮罩"""
        # 台灣身分證
        assert privacy_middleware._mask_patterns_in_text("身分證A123456789") == "身分證***masked***"

        # 居留證
        assert privacy_middleware._mask_patterns_in_text("居留證AB12345678") == "居留證***masked***"

        # 混合文字
        text = "身分證號碼是A123456789，請確認"
        result = privacy_middleware._mask_patterns_in_text(text)
        assert "***masked***" in result
        assert "A123456789" not in result

    def test_email_pattern_masking(self, privacy_middleware):
        """測試Email遮罩"""
        assert privacy_middleware._mask_patterns_in_text("我的email是test@example.com") == "我的email是***masked***"
        assert privacy_middleware._mask_patterns_in_text("聯絡user123@gmail.com") == "聯絡***masked***"

        # 多個Email
        text = "主要信箱admin@company.com，備用信箱backup@company.org"
        result = privacy_middleware._mask_patterns_in_text(text)
        assert result.count("***masked***") == 2

    def test_sensitive_field_detection(self, privacy_middleware):
        """測試敏感欄位偵測"""
        assert privacy_middleware._is_sensitive_field("symptoms") == True
        assert privacy_middleware._is_sensitive_field("name") == True
        assert privacy_middleware._is_sensitive_field("phone") == True
        assert privacy_middleware._is_sensitive_field("email") == True
        assert privacy_middleware._is_sensitive_field("address") == True
        assert privacy_middleware._is_sensitive_field("id_card") == True
        assert privacy_middleware._is_sensitive_field("medical_history") == True

        # 非敏感欄位
        assert privacy_middleware._is_sensitive_field("timestamp") == False
        assert privacy_middleware._is_sensitive_field("status") == False
        assert privacy_middleware._is_sensitive_field("location_type") == False

    def test_symptom_field_hashing(self, privacy_middleware):
        """測試症狀欄位雜湊化"""
        symptom_text = "胸痛、呼吸困難"
        result = privacy_middleware._mask_field_value("symptoms", symptom_text)

        assert result.startswith("hash:")
        assert symptom_text not in result

        # 驗證雜湊一致性
        result2 = privacy_middleware._mask_field_value("symptoms", symptom_text)
        assert result == result2

        # 不同症狀產生不同雜湊
        different_symptom = "頭痛、發燒"
        result3 = privacy_middleware._mask_field_value("symptoms", different_symptom)
        assert result != result3

    def test_general_sensitive_field_masking(self, privacy_middleware):
        """測試一般敏感欄位遮罩"""
        # 姓名
        assert privacy_middleware._mask_field_value("name", "陳小明") == "***masked***"

        # 電話
        assert privacy_middleware._mask_field_value("phone", "0912345678") == "***masked***"

        # Email
        assert privacy_middleware._mask_field_value("email", "test@example.com") == "***masked***"

        # 空值處理
        assert privacy_middleware._mask_field_value("name", None) == "None"
        assert privacy_middleware._mask_field_value("name", "") == ""

    def test_mask_sensitive_data_nested_structure(self, privacy_middleware, sensitive_request_data):
        """測試嵌套結構的敏感資料遮罩"""
        nested_data = {
            "patient_info": {
                "name": "陳小明",
                "symptoms": "胸痛",
                "contact": {
                    "phone": "0912345678",
                    "email": "test@example.com"
                }
            },
            "emergency_contacts": [
                {"name": "家屬一", "phone": "0987654321"},
                {"name": "家屬二", "phone": "0976543210"}
            ],
            "non_sensitive": "正常資料"
        }

        masked = privacy_middleware._mask_sensitive_data(nested_data)

        # 驗證嵌套物件遮罩
        assert masked["patient_info"]["name"] == "***masked***"
        assert masked["patient_info"]["symptoms"].startswith("hash:")
        assert masked["patient_info"]["contact"]["phone"] == "***masked***"
        assert masked["patient_info"]["contact"]["email"] == "***masked***"

        # 驗證陣列遮罩
        assert masked["emergency_contacts"][0]["name"] == "***masked***"
        assert masked["emergency_contacts"][0]["phone"] == "***masked***"
        assert masked["emergency_contacts"][1]["phone"] == "***masked***"

        # 驗證非敏感資料保持不變
        assert masked["non_sensitive"] == "正常資料"

    def test_mask_patterns_in_text_mixed_content(self, privacy_middleware):
        """測試混合敏感內容的文字遮罩"""
        mixed_text = "患者陳小明，身分證A123456789，電話0912345678，email是test@example.com，地址台北市信義區"

        result = privacy_middleware._mask_patterns_in_text(mixed_text)

        # 驗證所有patterns都被遮罩
        assert "A123456789" not in result
        assert "0912345678" not in result
        assert "test@example.com" not in result
        assert result.count("***masked***") == 3

    def test_hash_text_consistency(self, privacy_middleware):
        """測試文字雜湊一致性"""
        text = "測試症狀文字"

        hash1 = privacy_middleware._hash_text(text)
        hash2 = privacy_middleware._hash_text(text)

        assert hash1 == hash2
        assert len(hash1) == 16  # 預設長度
        assert text not in hash1

        # 不同文字產生不同雜湊
        different_text = "不同的症狀文字"
        hash3 = privacy_middleware._hash_text(different_text)
        assert hash1 != hash3

    def test_get_client_ip_masking(self, privacy_middleware, mock_request):
        """測試客戶端IP遮罩"""
        # 標準IPv4
        mock_request.headers = {"x-forwarded-for": "192.168.1.100"}
        ip = privacy_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.***.**"

        # 多個forwarded IP
        mock_request.headers = {"x-forwarded-for": "203.75.15.20, 192.168.1.1"}
        ip = privacy_middleware._get_client_ip(mock_request)
        assert ip == "203.75.***.**"

        # x-real-ip header
        mock_request.headers = {"x-real-ip": "10.0.0.1"}
        ip = privacy_middleware._get_client_ip(mock_request)
        assert ip == "10.0.***.**"

        # 無IP資訊
        mock_request.headers = {}
        mock_request.client = None
        ip = privacy_middleware._get_client_ip(mock_request)
        assert ip == "***masked***"

    def test_create_body_summary(self, privacy_middleware):
        """測試請求內容摘要創建"""
        body_data = {
            "symptoms": "***masked***",
            "location": "台北市",
            "urgency": "high",
            "name": "***masked***",
            "long_text": "a" * 100  # 長文字
        }

        summary = privacy_middleware._create_body_summary(body_data)

        assert "symptoms:masked" in summary
        assert "location:str" in summary
        assert "urgency:str" in summary
        assert "name:masked" in summary
        assert "long_text:truncated(100chars)" in summary

    @pytest.mark.asyncio
    async def test_read_request_body_safely_json(self, privacy_middleware, mock_request):
        """測試安全讀取JSON請求內容"""
        test_data = {"test": "data"}
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.json = AsyncMock(return_value=test_data)

        result = await privacy_middleware._read_request_body_safely(mock_request)
        assert result == test_data

    @pytest.mark.asyncio
    async def test_read_request_body_safely_non_json(self, privacy_middleware, mock_request):
        """測試讀取非JSON請求內容"""
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "text/plain"}

        result = await privacy_middleware._read_request_body_safely(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_read_request_body_safely_get_method(self, privacy_middleware, mock_request):
        """測試GET方法不讀取請求內容"""
        mock_request.method = "GET"

        result = await privacy_middleware._read_request_body_safely(mock_request)
        assert result is None

    @pytest.mark.asyncio
    async def test_read_request_body_safely_exception(self, privacy_middleware, mock_request):
        """測試讀取請求內容異常處理"""
        mock_request.method = "POST"
        mock_request.headers = {"content-type": "application/json"}
        mock_request.json = AsyncMock(side_effect=ValueError("Invalid JSON"))

        result = await privacy_middleware._read_request_body_safely(mock_request)
        assert result is None

    @patch('app.middlewares.privacy.privacy_logger')
    def test_log_request_audit(self, mock_logger, privacy_middleware, mock_request, mock_response):
        """測試審計日誌記錄"""
        request_id = "test-request-id"
        masked_body = {"test": "data"}
        duration_ms = 123.45

        privacy_middleware._log_request_audit(
            request=mock_request,
            response=mock_response,
            request_id=request_id,
            masked_body=masked_body,
            duration_ms=duration_ms
        )

        # 驗證日誌被調用
        mock_logger.info.assert_called_once()

        # 驗證日誌內容
        log_call = mock_logger.info.call_args[0][0]
        assert request_id in log_call
        assert "POST" in log_call
        assert "/v1/triage" in log_call
        assert "200" in log_call

    @patch('app.middlewares.privacy.privacy_logger')
    def test_log_request_audit_no_body(self, mock_logger, privacy_middleware, mock_request, mock_response):
        """測試無請求內容的審計日誌"""
        request_id = "test-request-id"

        privacy_middleware._log_request_audit(
            request=mock_request,
            response=mock_response,
            request_id=request_id,
            masked_body=None,
            duration_ms=100.0
        )

        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call.split("Request audit: ")[1])

        assert "body_summary" not in log_data

    @pytest.mark.asyncio
    async def test_middleware_dispatch_flow(self, privacy_middleware, mock_request, sensitive_request_data):
        """測試中介軟體完整處理流程"""
        # 模擬call_next
        async def mock_call_next(request):
            response = Mock(spec=Response)
            response.status_code = 200
            response.headers = {}
            return response

        mock_request.json = AsyncMock(return_value=sensitive_request_data)

        with patch('app.middlewares.privacy.privacy_logger') as mock_logger:
            response = await privacy_middleware.dispatch(mock_request, mock_call_next)

        # 驗證回應包含請求ID
        assert "X-Request-Id" in response.headers
        assert len(response.headers["X-Request-Id"]) > 0

        # 驗證審計日誌被記錄
        mock_logger.info.assert_called_once()

    def test_pdpa_compliance_verification(self, privacy_middleware, sensitive_request_data):
        """測試PDPA合規性驗證"""
        masked_data = privacy_middleware._mask_sensitive_data(sensitive_request_data)

        # 驗證所有個人識別資訊被遮罩
        assert "陳小明" not in str(masked_data)
        assert "0912345678" not in str(masked_data)
        assert "A123456789" not in str(masked_data)
        assert "test@example.com" not in str(masked_data)
        assert "台北市信義區市府路1號" not in str(masked_data)

        # 驗證症狀被雜湊化而非完全遮罩
        assert masked_data["symptoms"].startswith("hash:")

        # 驗證非敏感資料保持可用
        assert masked_data["age"] == 30

    def test_mask_text_configuration(self, privacy_middleware):
        """測試遮罩文字配置"""
        assert privacy_middleware.mask_text == "***masked***"

        # 測試自定義遮罩文字
        custom_middleware = PrivacyMiddleware(FastAPI())
        custom_middleware.mask_text = "[REDACTED]"

        result = custom_middleware._mask_field_value("name", "測試")
        assert result == "[REDACTED]"

    def test_sensitive_fields_coverage(self, privacy_middleware):
        """測試敏感欄位覆蓋完整性"""
        # 醫療相關
        assert privacy_middleware._is_sensitive_field("symptoms") == True
        assert privacy_middleware._is_sensitive_field("medical_history") == True
        assert privacy_middleware._is_sensitive_field("diagnosis") == True

        # 個人識別
        assert privacy_middleware._is_sensitive_field("name") == True
        assert privacy_middleware._is_sensitive_field("patient_name") == True
        assert privacy_middleware._is_sensitive_field("id_card") == True
        assert privacy_middleware._is_sensitive_field("national_id") == True

        # 聯絡資訊
        assert privacy_middleware._is_sensitive_field("phone") == True
        assert privacy_middleware._is_sensitive_field("email") == True
        assert privacy_middleware._is_sensitive_field("address") == True
        assert privacy_middleware._is_sensitive_field("emergency_contact") == True

        # 健保資訊
        assert privacy_middleware._is_sensitive_field("insurance_number") == True
        assert privacy_middleware._is_sensitive_field("health_card") == True

    def test_empty_data_handling(self, privacy_middleware):
        """測試空資料處理"""
        assert privacy_middleware._mask_sensitive_data(None) is None
        assert privacy_middleware._mask_sensitive_data({}) == {}

        # 空字串處理
        result = privacy_middleware._mask_field_value("name", "")
        assert result == ""

        # None值處理
        result = privacy_middleware._mask_field_value("phone", None)
        assert result == "None"