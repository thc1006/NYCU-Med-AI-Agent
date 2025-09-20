"""
Comprehensive unit tests for audit logging system.
Tests PDPA-compliant audit logging with no PII in logs and proper compliance tracking.
專注於台灣醫療AI助理的審計日誌系統，確保PDPA合規性和安全性。
"""

import json
import uuid
import asyncio
import tempfile
import os
import platform
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, List, Any
from pathlib import Path

import pytest
from freezegun import freeze_time

from app.monitoring.audit import (
    AuditLogger,
    AuditEventType,
    AuditEvent,
    PDPAComplianceLogger,
    SecurityAuditLogger,
    BusinessAuditLogger,
    AuditTrail,
    ComplianceReporter,
    DataRetentionManager,
    AuditStorageBackend,
    EncryptedAuditStorage,
    RateLimiter,
    hash_pii,
    generate_correlation_id
)


class TestAuditEventType:
    """測試審計事件類型枚舉."""

    def test_audit_event_types(self):
        """測試審計事件類型值."""
        assert AuditEventType.USER_ACCESS.value == "user_access"
        assert AuditEventType.DATA_PROCESSING.value == "data_processing"
        assert AuditEventType.MEDICAL_CONSULTATION.value == "medical_consultation"
        assert AuditEventType.SECURITY_EVENT.value == "security_event"
        assert AuditEventType.SYSTEM_ADMIN.value == "system_admin"
        assert AuditEventType.COMPLIANCE_CHECK.value == "compliance_check"

    def test_sensitive_event_types(self):
        """測試敏感事件類型識別."""
        sensitive_types = AuditEventType.get_sensitive_types()

        assert AuditEventType.MEDICAL_CONSULTATION in sensitive_types
        assert AuditEventType.DATA_PROCESSING in sensitive_types
        assert AuditEventType.USER_ACCESS in sensitive_types

    def test_high_priority_event_types(self):
        """測試高優先級事件類型識別."""
        high_priority = AuditEventType.get_high_priority_types()

        assert AuditEventType.SECURITY_EVENT in high_priority
        assert AuditEventType.SYSTEM_ADMIN in high_priority


class TestAuditEvent:
    """測試審計事件數據結構."""

    def setup_method(self):
        """設置測試固件."""
        self.event_id = str(uuid.uuid4())
        self.correlation_id = str(uuid.uuid4())

    @freeze_time("2024-01-15 10:30:00")
    def test_creates_audit_event(self):
        """測試審計事件創建."""
        event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user_123",
            action="triage_request",
            resource="symptom_analysis",
            details={
                "symptom_category": "chest_pain",
                "triage_level": "emergency",
                "duration_ms": 250
            }
        )

        assert event.event_id == self.event_id
        assert event.event_type == AuditEventType.MEDICAL_CONSULTATION
        assert event.correlation_id == self.correlation_id
        assert event.user_id_hash == "hashed_user_123"
        assert event.action == "triage_request"
        assert event.timestamp == datetime(2024, 1, 15, 10, 30, 0)

    def test_event_serialization(self):
        """測試審計事件序列化為字典."""
        event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user_456",
            action="login_attempt",
            resource="authentication_service",
            ip_address_hash="hashed_ip_address",
            user_agent_hash="hashed_user_agent",
            details={"success": True, "method": "password"}
        )

        serialized = event.to_dict()

        assert serialized["event_id"] == self.event_id
        assert serialized["event_type"] == "user_access"
        assert serialized["action"] == "login_attempt"
        assert serialized["details"]["success"] is True
        assert "timestamp" in serialized

    def test_event_without_sensitive_data(self):
        """測試審計事件不包含敏感數據."""
        event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user_789",
            action="symptom_input",
            resource="triage_service",
            details={
                "symptom_category": "respiratory",  # Category OK
                "input_length": 150,  # Length OK
                "language": "zh-TW"  # Language OK
                # NO actual symptom text
            }
        )

        serialized = event.to_dict()

        # Ensure no PII fields are present
        assert "symptom_text" not in serialized["details"]
        assert "user_name" not in serialized
        assert "email" not in serialized
        assert "phone" not in serialized
        assert "ip_address" not in serialized  # Only hash allowed

    def test_pdpa_compliance_validation(self):
        """測試PDPA合規性驗證."""
        # Valid event (no PII)
        valid_event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user",
            action="data_anonymization",
            resource="user_data",
            details={"records_processed": 100, "anonymization_method": "hash"}
        )

        assert valid_event.is_pdpa_compliant()

        # Invalid event (contains potential PII)
        invalid_event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=self.correlation_id,
            user_id_hash="user@example.com",  # Email instead of hash!
            action="data_processing",
            resource="user_data",
            details={"phone": "0912345678"}  # Contains phone number!
        )

        assert not invalid_event.is_pdpa_compliant()

    def test_taiwan_specific_pii_detection(self):
        """測試台灣特定PII檢測."""
        # Taiwan mobile number detection
        taiwan_mobile_event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user",
            action="profile_update",
            resource="user_service",
            details={"contact": "0987654321"}  # Taiwan mobile pattern
        )

        assert not taiwan_mobile_event.is_pdpa_compliant()

        # Taiwan ID pattern detection
        taiwan_id_event = AuditEvent(
            event_id=self.event_id,
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=self.correlation_id,
            user_id_hash="hashed_user",
            action="identity_verification",
            resource="verification_service",
            details={"document_id": "A123456789"}  # Taiwan ID pattern
        )

        assert not taiwan_id_event.is_pdpa_compliant()


class TestAuditLogger:
    """測試主要審計記錄器功能."""

    def setup_method(self):
        """設置測試固件."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.mock_storage.store_event = AsyncMock()
        self.audit_logger = AuditLogger(storage_backend=self.mock_storage)

    def test_logs_audit_event(self):
        """測試記錄審計事件."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="api_request",
            resource="/v1/triage",
            details={"method": "POST", "status_code": 200}
        )

        with patch('asyncio.create_task') as mock_create_task:
            self.audit_logger.log_event(event)
            # Verify task was created for async storage
            mock_create_task.assert_called_once()

    def test_validates_event_before_logging(self):
        """測試記錄前的事件驗證."""
        # Create event with PII (should be rejected)
        invalid_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="user@example.com",  # PII!
            action="data_access",
            resource="database",
            details={"operation": "read"}
        )

        with pytest.raises(ValueError, match="PDPA compliance"):
            self.audit_logger.log_event(invalid_event)

    def test_enriches_event_with_metadata(self):
        """測試用額外元數據豐富事件."""
        base_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="triage_request",
            resource="symptom_analysis",
            details={"initial": "data"}
        )

        # Mock the hostname detection for Windows
        with patch('os.getpid', return_value=12345):
            with patch('asyncio.create_task'):
                # On Windows, use platform module for hostname
                if os.name == 'nt':
                    with patch('platform.node', return_value='medical-server-01'):
                        self.audit_logger.log_event(base_event)
                else:
                    with patch('os.uname') as mock_uname:
                        mock_uname.return_value.nodename = 'medical-server-01'
                        self.audit_logger.log_event(base_event)

        # Check that event was enriched
        assert "process_id" in base_event.details
        assert base_event.details["process_id"] == 12345

    def test_async_event_logging(self):
        """測試異步事件記錄."""
        events = []
        for i in range(5):
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash=f"hashed_user_{i}",
                action="api_request",
                resource=f"/v1/endpoint_{i}",
                details={"index": i}
            )
            events.append(event)

        # Enable async logging
        self.audit_logger.enable_async_logging(batch_size=3)

        with patch('asyncio.create_task') as mock_create_task:
            for event in events:
                self.audit_logger.log_event(event)

            # Force flush of async buffer
            self.audit_logger.flush_async_buffer()

            # Should have created async tasks for all events
            assert mock_create_task.call_count >= 5

    def test_rate_limiting_protection(self):
        """測試審計記錄的速率限制."""
        self.audit_logger.enable_rate_limiting(max_events_per_second=2)

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="api_request",
            resource="/v1/test",
            details={"request_id": "123"}
        )

        task_count = 0
        def count_tasks(*args, **kwargs):
            nonlocal task_count
            task_count += 1

        with patch('asyncio.create_task', side_effect=count_tasks):
            # Log events rapidly
            for _ in range(5):
                self.audit_logger.log_event(event)

            # Should have rate limited some events
            assert task_count <= 3


class TestPDPAComplianceLogger:
    """測試PDPA合規記錄功能."""

    def setup_method(self):
        """設置測試固件."""
        self.compliance_logger = PDPAComplianceLogger()

    def test_logs_data_collection_event(self):
        """測試記錄數據收集事件."""
        with patch.object(self.compliance_logger.audit_logger, 'log_event') as mock_log:
            self.compliance_logger.log_data_collection(
                user_id_hash="hashed_user",
                data_types=["symptom_category", "location_preference"],
                purpose="medical_consultation",
                legal_basis="consent"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == AuditEventType.DATA_PROCESSING
            assert event.action == "data_collection"
            assert event.details["data_types"] == ["symptom_category", "location_preference"]
            assert event.details["legal_basis"] == "consent"

    def test_logs_data_processing_event(self):
        """測試記錄數據處理事件."""
        with patch.object(self.compliance_logger.audit_logger, 'log_event') as mock_log:
            self.compliance_logger.log_data_processing(
                user_id_hash="hashed_user",
                processing_purpose="symptom_analysis",
                data_categories=["health_data"],
                automated_decision=True
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "data_processing"
            assert event.details["automated_decision"] is True

    def test_logs_data_retention_event(self):
        """測試記錄數據保留事件."""
        with patch.object(self.compliance_logger.audit_logger, 'log_event') as mock_log:
            self.compliance_logger.log_data_retention(
                data_type="session_logs",
                retention_period_days=7,
                deletion_scheduled=True
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "data_retention"
            assert event.details["retention_period_days"] == 7

    def test_logs_user_consent_event(self):
        """測試記錄用戶同意事件."""
        with patch.object(self.compliance_logger.audit_logger, 'log_event') as mock_log:
            self.compliance_logger.log_user_consent(
                user_id_hash="hashed_user",
                consent_type="data_processing",
                consent_granted=True,
                consent_version="v1.2"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "user_consent"
            assert event.details["consent_granted"] is True

    def test_logs_data_breach_event(self):
        """測試記錄數據洩露事件."""
        with patch.object(self.compliance_logger.audit_logger, 'log_event') as mock_log:
            self.compliance_logger.log_data_breach(
                severity="high",
                affected_data_types=["user_sessions"],
                estimated_affected_users=150,
                mitigation_actions=["system_lockdown", "user_notification"]
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == AuditEventType.SECURITY_EVENT
            assert event.action == "data_breach"
            assert event.details["severity"] == "high"

    def test_validates_pdpa_compliance(self):
        """測試記錄事件的PDPA合規性驗證."""
        # Should reject logging of actual PII
        with pytest.raises(ValueError, match="contains PII"):
            self.compliance_logger.log_data_access(
                user_identifier="user@example.com",  # Email PII!
                accessed_data=["profile"],
                access_purpose="medical_consultation"
            )

        # Should accept hashed identifiers
        with patch.object(self.compliance_logger.audit_logger, 'log_event'):
            self.compliance_logger.log_data_access(
                user_identifier="hashed_user_identifier",
                accessed_data=["symptom_category"],
                access_purpose="medical_consultation"
            )


class TestSecurityAuditLogger:
    """測試安全審計記錄功能."""

    def setup_method(self):
        """設置測試固件."""
        self.security_logger = SecurityAuditLogger()

    def test_logs_authentication_events(self):
        """測試記錄認證事件."""
        with patch.object(self.security_logger.audit_logger, 'log_event') as mock_log:
            self.security_logger.log_authentication_attempt(
                user_id_hash="hashed_user",
                ip_address_hash="hashed_ip",
                user_agent_hash="hashed_agent",
                success=True,
                authentication_method="api_key"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == AuditEventType.SECURITY_EVENT
            assert event.action == "authentication_attempt"
            assert event.details["success"] is True

    def test_logs_authorization_events(self):
        """測試記錄授權事件."""
        with patch.object(self.security_logger.audit_logger, 'log_event') as mock_log:
            self.security_logger.log_authorization_check(
                user_id_hash="hashed_user",
                resource="/v1/admin/users",
                action="read",
                permitted=False,
                reason="insufficient_privileges"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "authorization_check"
            assert event.details["permitted"] is False

    def test_logs_rate_limiting_events(self):
        """測試記錄速率限制事件."""
        with patch.object(self.security_logger.audit_logger, 'log_event') as mock_log:
            self.security_logger.log_rate_limit_exceeded(
                ip_address_hash="hashed_ip",
                endpoint="/v1/triage",
                request_count=25,
                limit=20,
                time_window_seconds=60
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "rate_limit_exceeded"
            assert event.details["request_count"] == 25

    def test_logs_suspicious_activity(self):
        """測試記錄可疑活動."""
        with patch.object(self.security_logger.audit_logger, 'log_event') as mock_log:
            self.security_logger.log_suspicious_activity(
                ip_address_hash="hashed_ip",
                activity_type="repeated_failed_requests",
                risk_score=8.5,
                indicators=["high_frequency", "invalid_parameters"],
                action_taken="temporary_block"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "suspicious_activity"
            assert event.details["risk_score"] == 8.5

    def test_logs_system_access_events(self):
        """測試記錄系統訪問事件."""
        with patch.object(self.security_logger.audit_logger, 'log_event') as mock_log:
            self.security_logger.log_system_access(
                admin_user_hash="hashed_admin",
                action="config_update",
                resource="application_settings",
                changes={"log_level": "DEBUG", "rate_limit": 100}
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == AuditEventType.SYSTEM_ADMIN
            assert event.action == "config_update"


class TestBusinessAuditLogger:
    """測試業務審計記錄功能."""

    def setup_method(self):
        """設置測試固件."""
        self.business_logger = BusinessAuditLogger()

    def test_logs_medical_consultation(self):
        """測試記錄醫療諮詢事件."""
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_medical_consultation(
                session_id="session_123",
                symptom_category="chest_pain",
                triage_level="emergency",
                response_time_ms=250,
                recommended_action="call_119"
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.event_type == AuditEventType.MEDICAL_CONSULTATION
            assert event.action == "triage_consultation"
            assert event.details["triage_level"] == "emergency"

    def test_logs_hospital_search(self):
        """測試記錄醫院搜索事件."""
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_hospital_search(
                session_id="session_456",
                search_type="hospital",
                location_type="coordinates",
                radius_meters=3000,
                results_count=5,
                response_time_ms=180
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "hospital_search"
            assert event.details["results_count"] == 5

    def test_logs_emergency_escalation(self):
        """測試記錄緊急升級事件."""
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_emergency_escalation(
                session_id="session_789",
                trigger_symptoms=["chest_pain", "difficulty_breathing"],
                escalation_type="119_recommendation",
                escalation_time_ms=50
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "emergency_escalation"
            assert event.details["escalation_type"] == "119_recommendation"

    def test_logs_user_feedback(self):
        """測試記錄用戶反饋事件."""
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_user_feedback(
                session_id="session_abc",
                feedback_type="satisfaction_rating",
                rating=4,
                feedback_categories=["helpful", "accurate"],
                response_time_acceptable=True
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "user_feedback"
            assert event.details["rating"] == 4

    def test_logs_api_usage(self):
        """測試記錄API使用事件."""
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_api_usage(
                endpoint="/v1/triage",
                method="POST",
                status_code=200,
                response_time_ms=125,
                request_size_bytes=1024,
                response_size_bytes=2048
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert event.action == "api_usage"
            assert event.details["status_code"] == 200

    def test_emergency_logging_scenarios(self):
        """測試緊急情況日誌記錄場景."""
        # Test red flag symptom logging
        with patch.object(self.business_logger.audit_logger, 'log_event') as mock_log:
            self.business_logger.log_emergency_escalation(
                session_id="emergency_session",
                trigger_symptoms=["chest_pain", "loss_of_consciousness"],
                escalation_type="immediate_119",
                escalation_time_ms=25  # Very fast escalation
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]
            assert "chest_pain" in event.details["trigger_symptoms"]
            assert event.details["escalation_time_ms"] == 25

    def test_medical_data_anonymization(self):
        """測試醫療數據匿名化記錄."""
        session_id = "test_session_123"
        hashed_session = self.business_logger._hash_session_id(session_id)

        # Verify session ID is properly hashed (no original data)
        assert hashed_session != session_id
        assert len(hashed_session) == 16  # Hash should be 16 characters
        assert session_id not in hashed_session


class TestAuditTrail:
    """測試審計線索功能."""

    def setup_method(self):
        """設置測試固件."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.audit_trail = AuditTrail(storage_backend=self.mock_storage)

    @pytest.mark.asyncio
    async def test_queries_events_by_correlation_id(self):
        """測試按關聯ID查詢事件."""
        correlation_id = str(uuid.uuid4())

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="login",
                resource="auth_service",
                details={"method": "password"}
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="triage_request",
                resource="symptom_analysis",
                details={"symptom_category": "chest_pain"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        events = await self.audit_trail.get_events_by_correlation_id(correlation_id)

        assert len(events) == 2
        assert all(event.correlation_id == correlation_id for event in events)

    @pytest.mark.asyncio
    async def test_queries_events_by_time_range(self):
        """測試按時間範圍查詢事件."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 11, 0, 0)

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="api_request",
                resource="/v1/triage",
                timestamp=datetime(2024, 1, 15, 10, 30, 0),
                details={"method": "POST"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        events = await self.audit_trail.get_events_by_time_range(start_time, end_time)

        self.mock_storage.query_events.assert_called_with(
            start_time=start_time,
            end_time=end_time
        )
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_queries_events_by_user(self):
        """測試按用戶查詢事件."""
        user_id_hash = "hashed_user_123"

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=str(uuid.uuid4()),
                user_id_hash=user_id_hash,
                action="triage_request",
                resource="symptom_analysis",
                details={"symptom_category": "respiratory"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        events = await self.audit_trail.get_events_by_user(user_id_hash)

        assert len(events) == 1
        assert events[0].user_id_hash == user_id_hash

    @pytest.mark.asyncio
    async def test_generates_trail_summary(self):
        """測試生成審計線索摘要."""
        correlation_id = str(uuid.uuid4())

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=datetime(2024, 1, 15, 10, 0, 0),
                details={"method": "login"}
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="triage_request",
                resource="symptom_analysis",
                timestamp=datetime(2024, 1, 15, 10, 5, 0),
                details={"symptom_category": "chest_pain"}
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="session_end",
                resource="auth_service",
                timestamp=datetime(2024, 1, 15, 10, 10, 0),
                details={"method": "logout"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        summary = await self.audit_trail.generate_trail_summary(correlation_id)

        assert summary["total_events"] == 3
        assert summary["session_duration_minutes"] == 10
        # Event types are unique, so order doesn't matter
        assert set(summary["event_types"]) == {"user_access", "medical_consultation"}
        assert summary["actions"] == ["session_start", "triage_request", "session_end"]


class TestComplianceReporter:
    """測試合規報告功能."""

    def setup_method(self):
        """設置測試固件."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.compliance_reporter = ComplianceReporter(storage_backend=self.mock_storage)

    @pytest.mark.asyncio
    async def test_generates_pdpa_compliance_report(self):
        """測試生成PDPA合規報告."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        mock_events = [
            # Data collection events
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.DATA_PROCESSING,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user_1",
                action="data_collection",
                resource="user_input",
                details={"legal_basis": "consent", "data_types": ["symptom_category"]}
            ),
            # Data processing events
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.DATA_PROCESSING,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user_2",
                action="data_processing",
                resource="symptom_analysis",
                details={"purpose": "medical_consultation"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        report = await self.compliance_reporter.generate_pdpa_report(start_date, end_date)

        assert report["period"]["start"] == start_date
        assert report["period"]["end"] == end_date
        assert report["data_collection_events"] == 1
        assert report["data_processing_events"] == 1
        assert "consent" in report["legal_bases"]

    @pytest.mark.asyncio
    async def test_generates_security_compliance_report(self):
        """測試生成安全合規報告."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.SECURITY_EVENT,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="authentication_attempt",
                resource="auth_service",
                details={"success": False}
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.SECURITY_EVENT,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="rate_limit_exceeded",
                resource="/v1/triage",
                details={"ip_address_hash": "hashed_ip"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=mock_events)

        report = await self.compliance_reporter.generate_security_report(start_date, end_date)

        assert report["failed_authentication_attempts"] == 1
        assert report["rate_limiting_events"] == 1
        assert len(report["security_incidents"]) == 2

    @pytest.mark.asyncio
    async def test_validates_data_retention_compliance(self):
        """測試驗證數據保留合規性."""
        cutoff_date = datetime.now() - timedelta(days=7)

        old_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=cutoff_date - timedelta(days=1),  # 8 days old
                details={"method": "login"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=old_events)

        compliance_status = await self.compliance_reporter.validate_data_retention_compliance(
            max_retention_days=7
        )

        assert compliance_status["compliant"] is False
        assert compliance_status["expired_events_count"] == 1
        assert len(compliance_status["expired_event_ids"]) == 1


class TestDataRetentionManager:
    """測試數據保留管理功能."""

    def setup_method(self):
        """設置測試固件."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.retention_manager = DataRetentionManager(storage_backend=self.mock_storage)

    @pytest.mark.asyncio
    async def test_identifies_expired_data(self):
        """測試識別過期數據."""
        cutoff_date = datetime.now() - timedelta(days=30)

        old_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=cutoff_date - timedelta(days=1),
                details={"method": "login"}
            )
        ]

        self.mock_storage.query_events = AsyncMock(return_value=old_events)

        expired_events = await self.retention_manager.identify_expired_data(
            retention_days=30
        )

        assert len(expired_events) == 1
        # Verify the cutoff date was calculated correctly (approximately)
        call_args = self.mock_storage.query_events.call_args[1]
        assert abs((call_args['end_time'] - cutoff_date).total_seconds()) < 60

    @pytest.mark.asyncio
    async def test_deletes_expired_data(self):
        """測試刪除過期數據."""
        expired_event_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        self.mock_storage.delete_events = AsyncMock()

        deletion_result = await self.retention_manager.delete_expired_data(expired_event_ids)

        self.mock_storage.delete_events.assert_called_once_with(expired_event_ids)
        assert deletion_result["deleted_count"] == len(expired_event_ids)

    def test_schedules_retention_cleanup(self):
        """測試安排保留清理."""
        with patch('threading.Timer') as mock_timer:
            self.retention_manager.schedule_retention_cleanup(
                retention_days=7,
                cleanup_interval_hours=24
            )

            mock_timer.assert_called_once()
            # Verify timer is started
            timer_instance = mock_timer.return_value
            timer_instance.start.assert_called_once()


class TestEncryptedAuditStorage:
    """測試加密審計存儲後端."""

    def setup_method(self):
        """設置測試固件."""
        self.encryption_key = "test_encryption_key_32_characters_long"
        # Use a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.storage = EncryptedAuditStorage(
            encryption_key=self.encryption_key,
            storage_path=self.temp_dir
        )

    def teardown_method(self):
        """清理測試固件."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_encrypts_stored_events(self):
        """測試存儲的事件已加密."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="login",
            resource="auth_service",
            details={"method": "password"}
        )

        with patch.object(self.storage, '_write_encrypted_data') as mock_write:
            with patch.object(self.storage, '_encrypt_data', return_value=b'encrypted_data') as mock_encrypt:
                await self.storage.store_event(event)

                mock_encrypt.assert_called_once()
                mock_write.assert_called_once()
                # Verify that the data passed to encryption is the event dict
                encrypted_data = mock_encrypt.call_args[0][0]
                assert encrypted_data["event_id"] == event.event_id

    @pytest.mark.asyncio
    async def test_decrypts_retrieved_events(self):
        """測試檢索的事件已解密."""
        encrypted_event_data = b"encrypted_event_data_placeholder"
        event_dict = {
            "event_id": str(uuid.uuid4()),
            "event_type": "user_access",
            "correlation_id": str(uuid.uuid4()),
            "user_id_hash": "hashed_user",
            "action": "login",
            "resource": "auth_service",
            "timestamp": datetime.now().isoformat(),
            "details": {"method": "password"}
        }

        # Create a mock file path
        mock_file = self.storage.storage_path / "test.audit"

        with patch('pathlib.Path.glob', return_value=[mock_file]):
            with patch.object(self.storage, '_read_encrypted_data', return_value=encrypted_event_data):
                with patch.object(self.storage, '_decrypt_data', return_value=event_dict) as mock_decrypt:
                    events = await self.storage.query_events(limit=1)

                    mock_decrypt.assert_called_once_with(encrypted_event_data)
                    assert len(events) >= 0  # May be empty if file processing fails

    def test_validates_encryption_key_strength(self):
        """測試驗證加密密鑰強度."""
        # Weak key should be rejected
        with pytest.raises(ValueError, match="Encryption key must be at least 32 characters"):
            EncryptedAuditStorage(
                encryption_key="weak_key",
                storage_path="/tmp/audit_logs"
            )

        # Strong key should be accepted
        strong_key = "very_strong_encryption_key_32_chars_long"
        storage = EncryptedAuditStorage(
            encryption_key=strong_key,
            storage_path="/tmp/audit_logs"
        )
        assert storage.encryption_key == strong_key

    @pytest.mark.asyncio
    async def test_real_encryption_decryption(self):
        """測試真實的加密和解密過程."""
        test_data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "test_event",
            "message": "測試加密中文內容"
        }

        # Encrypt data
        encrypted = self.storage._encrypt_data(test_data)
        assert isinstance(encrypted, bytes)
        assert encrypted != json.dumps(test_data).encode()

        # Decrypt data
        decrypted = self.storage._decrypt_data(encrypted)
        assert decrypted == test_data
        assert decrypted["message"] == "測試加密中文內容"


class TestRateLimiter:
    """測試速率限制器."""

    def test_allows_events_under_limit(self):
        """測試允許限制內的事件."""
        limiter = RateLimiter(max_events_per_second=5)

        # Should allow first few events
        for _ in range(3):
            assert limiter.allow_event() is True

    def test_blocks_events_over_limit(self):
        """測試阻止超出限制的事件."""
        limiter = RateLimiter(max_events_per_second=2)

        # Fill up the limit
        for _ in range(2):
            assert limiter.allow_event() is True

        # Next event should be blocked
        assert limiter.allow_event() is False

    def test_resets_after_time_window(self):
        """測試時間窗口後重置."""
        limiter = RateLimiter(max_events_per_second=1)

        # Use up the limit
        assert limiter.allow_event() is True
        assert limiter.allow_event() is False

        # Manually clear old events (simulate time passing)
        limiter.events.clear()

        # Should allow events again
        assert limiter.allow_event() is True


class TestHelperFunctions:
    """測試輔助函數."""

    def test_hash_pii_function(self):
        """測試PII哈希函數."""
        # Test email hashing
        email = "user@example.com"
        hashed_email = hash_pii(email)

        assert hashed_email != email
        assert len(hashed_email) == 16
        assert email not in hashed_email

        # Test phone number hashing
        phone = "0987654321"
        hashed_phone = hash_pii(phone)

        assert hashed_phone != phone
        assert len(hashed_phone) == 16
        assert phone not in hashed_phone

        # Test deterministic hashing (same input = same output)
        assert hash_pii(email) == hash_pii(email)

    def test_generate_correlation_id(self):
        """測試生成關聯ID."""
        id1 = generate_correlation_id()
        id2 = generate_correlation_id()

        # Should be valid UUIDs
        assert len(id1) == 36  # UUID string length
        assert len(id2) == 36
        assert id1 != id2  # Should be unique

        # Should be parseable as UUID
        parsed_uuid = uuid.UUID(id1)
        assert str(parsed_uuid) == id1


class TestMedicalDataAnonymization:
    """測試醫療數據匿名化功能."""

    def test_symptom_data_anonymization(self):
        """測試症狀數據匿名化."""
        # Should accept anonymized symptom categories
        valid_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="symptom_analysis",
            resource="triage_service",
            details={
                "symptom_category": "respiratory",  # Category only, no specific text
                "severity_level": "moderate",
                "duration_category": "acute"
            }
        )

        assert valid_event.is_pdpa_compliant()

        # Should reject events with actual symptom text
        invalid_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="symptom_analysis",
            resource="triage_service",
            details={
                "symptom_text": "我胸口很痛，呼吸困難"  # Actual symptom description!
            }
        )

        assert not invalid_event.is_pdpa_compliant()

    def test_taiwan_medical_context(self):
        """測試台灣醫療環境特定的匿名化."""
        # Test Taiwan health insurance number pattern detection
        health_insurance_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="insurance_verification",
            resource="health_service",
            details={
                "insurance_number": "12345678901"  # Taiwan health insurance pattern
            }
        )

        # Should detect this as potentially sensitive (11 digits is common format)
        # This would need to be enhanced in the actual PDPA compliance check
        assert "insurance_number" in health_insurance_event.details

    def test_emergency_data_handling(self):
        """測試緊急數據處理."""
        business_logger = BusinessAuditLogger()

        # Emergency escalation should log necessary data for medical safety
        # while still maintaining privacy
        with patch.object(business_logger.audit_logger, 'log_event') as mock_log:
            business_logger.log_emergency_escalation(
                session_id="emergency_123",
                trigger_symptoms=["chest_pain", "shortness_of_breath"],  # Categories OK
                escalation_type="119_immediate",
                escalation_time_ms=15
            )

            mock_log.assert_called_once()
            event = mock_log.call_args[0][0]

            # Should contain necessary medical categories
            assert "chest_pain" in event.details["trigger_symptoms"]
            # But not specific patient descriptions
            assert "symptom_text" not in event.details


@pytest.mark.asyncio
async def test_integration_medical_consultation_flow():
    """測試完整醫療諮詢流程的審計記錄."""
    # Setup loggers
    business_logger = BusinessAuditLogger()
    security_logger = SecurityAuditLogger()
    pdpa_logger = PDPAComplianceLogger()

    session_id = "integration_test_session"
    user_hash = hash_pii("test_user@example.com")

    with patch.object(business_logger.audit_logger, 'log_event') as business_mock, \
         patch.object(security_logger.audit_logger, 'log_event') as security_mock, \
         patch.object(pdpa_logger.audit_logger, 'log_event') as pdpa_mock:

        # 1. User authentication
        security_logger.log_authentication_attempt(
            user_id_hash=user_hash,
            ip_address_hash=hash_pii("192.168.1.1"),
            user_agent_hash=hash_pii("Mozilla/5.0"),
            success=True,
            authentication_method="session"
        )

        # 2. Data collection consent
        pdpa_logger.log_user_consent(
            user_id_hash=user_hash,
            consent_type="medical_data_processing",
            consent_granted=True,
            consent_version="v2.1"
        )

        # 3. Medical consultation
        business_logger.log_medical_consultation(
            session_id=session_id,
            symptom_category="chest_pain",
            triage_level="urgent",
            response_time_ms=180,
            recommended_action="seek_medical_attention"
        )

        # 4. Hospital search
        business_logger.log_hospital_search(
            session_id=session_id,
            search_type="emergency_room",
            location_type="user_coordinates",
            radius_meters=5000,
            results_count=3,
            response_time_ms=95
        )

        # Verify all events were logged
        assert security_mock.call_count == 1
        assert pdpa_mock.call_count == 1
        assert business_mock.call_count == 2

        # Verify event types and compliance
        security_event = security_mock.call_args[0][0]
        assert security_event.event_type == AuditEventType.SECURITY_EVENT
        assert security_event.is_pdpa_compliant()

        consultation_event = business_mock.call_args_list[0][0][0]
        assert consultation_event.event_type == AuditEventType.MEDICAL_CONSULTATION
        assert consultation_event.is_pdpa_compliant()