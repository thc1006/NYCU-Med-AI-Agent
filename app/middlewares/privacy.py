"""
隱私遮罩與審計記錄中介層
功能：
- 遮罩敏感個人資料（電話、身分證、地址等）
- 症狀文字雜湊化，不記錄明文
- 最小化日誌記錄，僅保留必要欄位
- 符合台灣個人資料保護法（PDPA）要求
"""

import json
import time
import uuid
import hashlib
import logging
import re
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 設定專用的日誌記錄器
privacy_logger = logging.getLogger("privacy_audit")
privacy_logger.setLevel(logging.INFO)

# 如果沒有handler，添加console handler
if not privacy_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    privacy_logger.addHandler(handler)
    privacy_logger.propagate = False  # 避免重複記錄


class PrivacyMiddleware(BaseHTTPMiddleware):
    """隱私保護中介層"""

    # 敏感資料patterns
    PHONE_PATTERNS = [
        r'09\d{8}',           # 台灣手機號碼
        r'0\d{1,2}-?\d{6,8}', # 台灣市話
        r'\+886-?\d{8,10}',   # 國際格式
    ]

    ID_PATTERNS = [
        r'[A-Z]\d{9}',        # 台灣身分證號碼
        r'[A-Z]{2}\d{8}',     # 居留證號碼
    ]

    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # 敏感欄位名稱
    SENSITIVE_FIELDS = {
        'symptom', 'symptoms', 'medical_history', 'diagnosis',
        'name', 'full_name', 'patient_name',
        'phone', 'mobile', 'telephone', 'contact', 'emergency_contact',
        'email', 'mail', 'email_address',
        'address', 'home_address', 'residence',
        'id', 'id_card', 'identity', 'patient_id', 'national_id',
        'birthday', 'birth_date', 'age',
        'insurance_number', 'health_card'
    }

    def __init__(self, app):
        super().__init__(app)
        self.mask_text = "***masked***"

    async def dispatch(self, request: Request, call_next):
        """處理請求與回應的主要方法"""
        start_time = time.time()

        # 生成唯一請求ID
        request_id = str(uuid.uuid4())

        # 讀取請求內容用於審計（但要遮罩）
        body = await self._read_request_body_safely(request)
        masked_body = self._mask_sensitive_data(body)

        # 處理請求
        response = await call_next(request)

        # 計算處理時間
        process_time = (time.time() - start_time) * 1000

        # 記錄遮罩後的審計日誌
        self._log_request_audit(
            request=request,
            response=response,
            request_id=request_id,
            masked_body=masked_body,
            duration_ms=process_time
        )

        # 添加請求ID到回應header
        response.headers["X-Request-Id"] = request_id

        return response

    async def _read_request_body_safely(self, request: Request) -> Optional[Dict[str, Any]]:
        """安全讀取請求內容，避免重複讀取問題"""
        try:
            if request.method in ("POST", "PUT", "PATCH"):
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # 使用 request.json() 方法，這會快取結果
                    body = await request.json()
                    return body
        except Exception as e:
            privacy_logger.warning(f"Failed to parse request body: {type(e).__name__}")
        return None


    def _mask_sensitive_data(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """遮罩敏感資料"""
        if not data:
            return None

        masked = {}
        for key, value in data.items():
            if self._is_sensitive_field(key):
                masked[key] = self._mask_field_value(key, value)
            elif isinstance(value, str):
                masked[key] = self._mask_patterns_in_text(value)
            elif isinstance(value, dict):
                masked[key] = self._mask_sensitive_data(value)
            elif isinstance(value, list):
                masked[key] = [self._mask_sensitive_data(item) if isinstance(item, dict)
                              else self._mask_patterns_in_text(str(item))
                              for item in value]
            else:
                masked[key] = value

        return masked

    def _is_sensitive_field(self, field_name: str) -> bool:
        """判斷是否為敏感欄位"""
        return field_name.lower() in self.SENSITIVE_FIELDS

    def _mask_field_value(self, field_name: str, value: Any) -> str:
        """根據欄位類型遮罩值"""
        if not value:
            return str(value)

        str_value = str(value)
        field_lower = field_name.lower()

        # 症狀相關欄位使用雜湊
        if field_lower in ('symptom', 'symptoms', 'medical_history', 'diagnosis'):
            return f"hash:{self._hash_text(str_value)}"

        # 其他敏感欄位直接遮罩
        return self.mask_text

    def _mask_patterns_in_text(self, text: str) -> str:
        """遮罩文字中的敏感patterns"""
        if not isinstance(text, str):
            return str(text)

        masked_text = text

        # 遮罩電話號碼
        for pattern in self.PHONE_PATTERNS:
            masked_text = re.sub(pattern, self.mask_text, masked_text)

        # 遮罩身分證號碼
        for pattern in self.ID_PATTERNS:
            masked_text = re.sub(pattern, self.mask_text, masked_text)

        # 遮罩Email
        masked_text = re.sub(self.EMAIL_PATTERN, self.mask_text, masked_text)

        return masked_text

    def _hash_text(self, text: str, length: int = 16) -> str:
        """對文字進行雜湊處理"""
        if not text:
            return ""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()[:length]

    def _log_request_audit(self, request: Request, response: Response,
                          request_id: str, masked_body: Optional[Dict[str, Any]],
                          duration_ms: float) -> None:
        """記錄審計日誌（僅必要資訊）"""
        audit_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "user_agent": request.headers.get("user-agent", "")[:100],  # 限制長度
            "client_ip": self._get_client_ip(request),
        }

        # 如果有遮罩後的body，記錄摘要
        if masked_body:
            body_summary = self._create_body_summary(masked_body)
            if body_summary:
                audit_data["body_summary"] = body_summary

        privacy_logger.info(f"Request audit: {json.dumps(audit_data, ensure_ascii=False)}")

    def _get_client_ip(self, request: Request) -> str:
        """取得客戶端IP（遮罩後）"""
        # 從headers取得真實IP
        real_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip() or
            request.headers.get("x-real-ip", "") or
            request.client.host if request.client else ""
        )

        # 部分遮罩IP（保留前兩段用於地理分析）
        if real_ip:
            parts = real_ip.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.***.**"

        return "***masked***"

    def _create_body_summary(self, masked_body: Dict[str, Any]) -> Optional[str]:
        """創建body摘要（不包含敏感內容）"""
        if not masked_body:
            return None

        # 創建非敏感欄位的摘要
        summary_fields = []
        for key, value in masked_body.items():
            if not self._is_sensitive_field(key):
                if isinstance(value, str) and len(value) > 50:
                    summary_fields.append(f"{key}:truncated({len(value)}chars)")
                else:
                    summary_fields.append(f"{key}:{type(value).__name__}")
            else:
                summary_fields.append(f"{key}:masked")

        return ",".join(summary_fields) if summary_fields else None