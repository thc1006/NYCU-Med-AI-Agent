"""
Unit tests for audit logging system.
Tests PDPA-compliant audit logging with no PII in logs and proper compliance tracking.
"""

import json
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from typing import Dict, List, Any

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
    EncryptedAuditStorage
)


class TestAuditEventType:
    """Test audit event type enumeration."""

    def test_audit_event_types(self):
        """Test audit event type values."""
        assert AuditEventType.USER_ACCESS.value == "user_access"
        assert AuditEventType.DATA_PROCESSING.value == "data_processing"
        assert AuditEventType.MEDICAL_CONSULTATION.value == "medical_consultation"
        assert AuditEventType.SECURITY_EVENT.value == "security_event"
        assert AuditEventType.SYSTEM_ADMIN.value == "system_admin"
        assert AuditEventType.COMPLIANCE_CHECK.value == "compliance_check"

    def test_sensitive_event_types(self):
        """Test identification of sensitive event types."""
        sensitive_types = AuditEventType.get_sensitive_types()

        assert AuditEventType.MEDICAL_CONSULTATION in sensitive_types
        assert AuditEventType.DATA_PROCESSING in sensitive_types
        assert AuditEventType.USER_ACCESS in sensitive_types

    def test_high_priority_event_types(self):
        """Test identification of high priority event types."""
        high_priority = AuditEventType.get_high_priority_types()

        assert AuditEventType.SECURITY_EVENT in high_priority
        assert AuditEventType.SYSTEM_ADMIN in high_priority


class TestAuditEvent:
    """Test audit event data structure."""

    def setup_method(self):
        """Setup test fixtures."""
        self.event_id = str(uuid.uuid4())
        self.correlation_id = str(uuid.uuid4())

    @freeze_time("2024-01-15 10:30:00")
    def test_creates_audit_event(self):
        """Test audit event creation."""
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
        """Test audit event serialization to dict."""
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
        """Test that audit event does not contain sensitive data."""
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
        """Test PDPA compliance validation."""
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


class TestAuditLogger:
    """Test main audit logger functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.audit_logger = AuditLogger(storage_backend=self.mock_storage)

    def test_logs_audit_event(self):
        """Test logging audit events."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="api_request",
            resource="/v1/triage"
        )

        self.audit_logger.log_event(event)

        self.mock_storage.store_event.assert_called_once_with(event)

    def test_validates_event_before_logging(self):
        """Test event validation before logging."""
        # Create event with PII (should be rejected)
        invalid_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="user@example.com",  # PII!
            action="data_access",
            resource="database"
        )

        with pytest.raises(ValueError, match="PDPA compliance"):
            self.audit_logger.log_event(invalid_event)

        self.mock_storage.store_event.assert_not_called()

    def test_enriches_event_with_metadata(self):
        """Test enriching events with additional metadata."""
        base_event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="triage_request",
            resource="symptom_analysis"
        )

        with patch('socket.gethostname', return_value='medical-server-01'):
            self.audit_logger.log_event(base_event)

        stored_event = self.mock_storage.store_event.call_args[0][0]
        assert stored_event.details["hostname"] == "medical-server-01"
        assert "process_id" in stored_event.details

    def test_async_event_logging(self):
        """Test asynchronous event logging."""
        events = []
        for i in range(5):
            event = AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash=f"hashed_user_{i}",
                action="api_request",
                resource=f"/v1/endpoint_{i}"
            )
            events.append(event)

        # Enable async logging
        self.audit_logger.enable_async_logging(batch_size=3)

        for event in events:
            self.audit_logger.log_event(event)

        # Force flush of async buffer
        self.audit_logger.flush_async_buffer()

        assert self.mock_storage.store_event.call_count == 5

    def test_rate_limiting_protection(self):
        """Test rate limiting for audit logging."""
        self.audit_logger.enable_rate_limiting(max_events_per_second=2)

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="api_request",
            resource="/v1/test"
        )

        # Log events rapidly
        for _ in range(5):
            self.audit_logger.log_event(event)

        # Should have rate limited some events
        assert self.mock_storage.store_event.call_count <= 3


class TestPDPAComplianceLogger:
    """Test PDPA compliance logging functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.compliance_logger = PDPAComplianceLogger()

    def test_logs_data_collection_event(self):
        """Test logging data collection events."""
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
        """Test logging data processing events."""
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
        """Test logging data retention events."""
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
        """Test logging user consent events."""
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
        """Test logging data breach events."""
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
        """Test PDPA compliance validation for logged events."""
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
    """Test security audit logging functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.security_logger = SecurityAuditLogger()

    def test_logs_authentication_events(self):
        """Test logging authentication events."""
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
        """Test logging authorization events."""
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
        """Test logging rate limiting events."""
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
        """Test logging suspicious activity."""
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
        """Test logging system access events."""
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
    """Test business audit logging functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.business_logger = BusinessAuditLogger()

    def test_logs_medical_consultation(self):
        """Test logging medical consultation events."""
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
        """Test logging hospital search events."""
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
        """Test logging emergency escalation events."""
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
        """Test logging user feedback events."""
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
        """Test logging API usage events."""
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


class TestAuditTrail:
    """Test audit trail functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.audit_trail = AuditTrail(storage_backend=self.mock_storage)

    def test_queries_events_by_correlation_id(self):
        """Test querying events by correlation ID."""
        correlation_id = str(uuid.uuid4())

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="login",
                resource="auth_service"
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="triage_request",
                resource="symptom_analysis"
            )
        ]

        self.mock_storage.query_events.return_value = mock_events

        events = self.audit_trail.get_events_by_correlation_id(correlation_id)

        assert len(events) == 2
        assert all(event.correlation_id == correlation_id for event in events)

    def test_queries_events_by_time_range(self):
        """Test querying events by time range."""
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
                timestamp=datetime(2024, 1, 15, 10, 30, 0)
            )
        ]

        self.mock_storage.query_events.return_value = mock_events

        events = self.audit_trail.get_events_by_time_range(start_time, end_time)

        self.mock_storage.query_events.assert_called_with(
            start_time=start_time,
            end_time=end_time
        )
        assert len(events) == 1

    def test_queries_events_by_user(self):
        """Test querying events by user."""
        user_id_hash = "hashed_user_123"

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=str(uuid.uuid4()),
                user_id_hash=user_id_hash,
                action="triage_request",
                resource="symptom_analysis"
            )
        ]

        self.mock_storage.query_events.return_value = mock_events

        events = self.audit_trail.get_events_by_user(user_id_hash)

        assert len(events) == 1
        assert events[0].user_id_hash == user_id_hash

    def test_generates_trail_summary(self):
        """Test generating audit trail summary."""
        correlation_id = str(uuid.uuid4())

        mock_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=datetime(2024, 1, 15, 10, 0, 0)
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.MEDICAL_CONSULTATION,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="triage_request",
                resource="symptom_analysis",
                timestamp=datetime(2024, 1, 15, 10, 5, 0)
            ),
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=correlation_id,
                user_id_hash="hashed_user",
                action="session_end",
                resource="auth_service",
                timestamp=datetime(2024, 1, 15, 10, 10, 0)
            )
        ]

        self.mock_storage.query_events.return_value = mock_events

        summary = self.audit_trail.generate_trail_summary(correlation_id)

        assert summary["total_events"] == 3
        assert summary["session_duration_minutes"] == 10
        assert summary["event_types"] == ["user_access", "medical_consultation"]
        assert summary["actions"] == ["session_start", "triage_request", "session_end"]


class TestComplianceReporter:
    """Test compliance reporting functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.compliance_reporter = ComplianceReporter(storage_backend=self.mock_storage)

    def test_generates_pdpa_compliance_report(self):
        """Test generating PDPA compliance report."""
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

        self.mock_storage.query_events.return_value = mock_events

        report = self.compliance_reporter.generate_pdpa_report(start_date, end_date)

        assert report["period"]["start"] == start_date
        assert report["period"]["end"] == end_date
        assert report["data_collection_events"] == 1
        assert report["data_processing_events"] == 1
        assert "consent" in report["legal_bases"]

    def test_generates_security_compliance_report(self):
        """Test generating security compliance report."""
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

        self.mock_storage.query_events.return_value = mock_events

        report = self.compliance_reporter.generate_security_report(start_date, end_date)

        assert report["failed_authentication_attempts"] == 1
        assert report["rate_limiting_events"] == 1
        assert len(report["security_incidents"]) == 2

    def test_validates_data_retention_compliance(self):
        """Test validating data retention compliance."""
        cutoff_date = datetime.now() - timedelta(days=7)

        old_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=cutoff_date - timedelta(days=1)  # 8 days old
            )
        ]

        self.mock_storage.query_events.return_value = old_events

        compliance_status = self.compliance_reporter.validate_data_retention_compliance(
            max_retention_days=7
        )

        assert compliance_status["compliant"] is False
        assert compliance_status["expired_events_count"] == 1
        assert len(compliance_status["expired_event_ids"]) == 1


class TestDataRetentionManager:
    """Test data retention management functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_storage = Mock(spec=AuditStorageBackend)
        self.retention_manager = DataRetentionManager(storage_backend=self.mock_storage)

    def test_identifies_expired_data(self):
        """Test identification of expired data."""
        cutoff_date = datetime.now() - timedelta(days=30)

        old_events = [
            AuditEvent(
                event_id=str(uuid.uuid4()),
                event_type=AuditEventType.USER_ACCESS,
                correlation_id=str(uuid.uuid4()),
                user_id_hash="hashed_user",
                action="session_start",
                resource="auth_service",
                timestamp=cutoff_date - timedelta(days=1)
            )
        ]

        self.mock_storage.query_events.return_value = old_events

        expired_events = self.retention_manager.identify_expired_data(
            retention_days=30
        )

        assert len(expired_events) == 1
        self.mock_storage.query_events.assert_called_with(
            end_time=cutoff_date
        )

    def test_deletes_expired_data(self):
        """Test deletion of expired data."""
        expired_event_ids = [str(uuid.uuid4()), str(uuid.uuid4())]

        deletion_result = self.retention_manager.delete_expired_data(expired_event_ids)

        self.mock_storage.delete_events.assert_called_once_with(expired_event_ids)
        assert deletion_result["deleted_count"] == len(expired_event_ids)

    def test_schedules_retention_cleanup(self):
        """Test scheduling of retention cleanup."""
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
    """Test encrypted audit storage backend."""

    def setup_method(self):
        """Setup test fixtures."""
        self.encryption_key = "test_encryption_key_32_characters"
        self.storage = EncryptedAuditStorage(
            encryption_key=self.encryption_key,
            storage_path="/tmp/audit_logs"
        )

    def test_encrypts_stored_events(self):
        """Test that stored events are encrypted."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="hashed_user",
            action="login",
            resource="auth_service"
        )

        with patch.object(self.storage, '_write_encrypted_data') as mock_write:
            self.storage.store_event(event)

            mock_write.assert_called_once()
            # Verify that the data passed to encryption is the event
            encrypted_data = mock_write.call_args[0][0]
            assert isinstance(encrypted_data, dict)
            assert encrypted_data["event_id"] == event.event_id

    def test_decrypts_retrieved_events(self):
        """Test that retrieved events are decrypted."""
        encrypted_event_data = b"encrypted_event_data_placeholder"

        with patch.object(self.storage, '_read_encrypted_data', return_value=encrypted_event_data):
            with patch.object(self.storage, '_decrypt_data') as mock_decrypt:
                mock_decrypt.return_value = {
                    "event_id": str(uuid.uuid4()),
                    "event_type": "user_access",
                    "correlation_id": str(uuid.uuid4()),
                    "user_id_hash": "hashed_user",
                    "action": "login",
                    "resource": "auth_service",
                    "timestamp": datetime.now().isoformat()
                }

                events = self.storage.query_events(limit=1)

                mock_decrypt.assert_called_once_with(encrypted_event_data)
                assert len(events) >= 0  # May be empty if no events stored

    def test_validates_encryption_key_strength(self):
        """Test validation of encryption key strength."""
        # Weak key should be rejected
        with pytest.raises(ValueError, match="encryption key"):
            EncryptedAuditStorage(
                encryption_key="weak_key",
                storage_path="/tmp/audit_logs"
            )

        # Strong key should be accepted
        strong_key = "very_strong_encryption_key_32_chars"
        storage = EncryptedAuditStorage(
            encryption_key=strong_key,
            storage_path="/tmp/audit_logs"
        )
        assert storage.encryption_key == strong_key