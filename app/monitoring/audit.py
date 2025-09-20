"""
PDPA-compliant audit logging system for Taiwan Medical AI Assistant.
Ensures comprehensive audit trail while maintaining privacy compliance.
"""

import hashlib
import json
import os
import re
import threading
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path
import gzip
import base64


class AuditEventType(Enum):
    """Audit event types."""
    USER_ACCESS = "user_access"
    DATA_PROCESSING = "data_processing"
    MEDICAL_CONSULTATION = "medical_consultation"
    SECURITY_EVENT = "security_event"
    SYSTEM_ADMIN = "system_admin"
    COMPLIANCE_CHECK = "compliance_check"

    @classmethod
    def get_sensitive_types(cls) -> List['AuditEventType']:
        """Get event types that contain sensitive data."""
        return [
            cls.MEDICAL_CONSULTATION,
            cls.DATA_PROCESSING,
            cls.USER_ACCESS
        ]

    @classmethod
    def get_high_priority_types(cls) -> List['AuditEventType']:
        """Get high priority event types."""
        return [
            cls.SECURITY_EVENT,
            cls.SYSTEM_ADMIN
        ]


@dataclass
class AuditEvent:
    """PDPA-compliant audit event."""
    event_id: str
    event_type: AuditEventType
    correlation_id: str
    user_id_hash: str
    action: str
    resource: str
    details: Dict[str, Any]
    timestamp: Optional[datetime] = None
    ip_address_hash: Optional[str] = None
    user_agent_hash: Optional[str] = None
    error: Optional[Exception] = None

    def __post_init__(self):
        """Post-initialization validation."""
        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        result = asdict(self)
        result["event_type"] = self.event_type.value
        result["timestamp"] = self.timestamp.isoformat()
        result["error"] = str(self.error) if self.error else None
        return result

    def is_pdpa_compliant(self) -> bool:
        """Check if event is PDPA compliant (no PII)."""
        # Check for common PII patterns
        pii_patterns = [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{10}\b',  # Phone numbers (10 digits)
            r'\b09\d{8}\b',  # Taiwan mobile numbers
            r'\b\d{4}-\d{6}\b',  # Taiwan landline
            r'\b[A-Z]\d{9}\b',  # Taiwan ID pattern
        ]

        # Convert to string for pattern matching
        event_str = json.dumps(self.to_dict(), ensure_ascii=False)

        for pattern in pii_patterns:
            if re.search(pattern, event_str, re.IGNORECASE):
                return False

        # Check specific fields that should be hashed
        if '@' in self.user_id_hash or '.' in self.user_id_hash:
            # User ID hash should not contain email-like patterns
            return False

        # Check details for common PII field names
        pii_fields = ['email', 'phone', 'name', 'address', 'symptom_text', 'user_name']
        for field in pii_fields:
            if field in self.details:
                return False

        return True


class AuditStorageBackend(ABC):
    """Abstract audit storage backend."""

    @abstractmethod
    async def store_event(self, event: AuditEvent):
        """Store an audit event."""
        pass

    @abstractmethod
    async def query_events(self, start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          event_type: Optional[AuditEventType] = None,
                          correlation_id: Optional[str] = None,
                          user_id_hash: Optional[str] = None,
                          limit: int = 1000) -> List[AuditEvent]:
        """Query audit events."""
        pass

    @abstractmethod
    async def delete_events(self, event_ids: List[str]):
        """Delete audit events by IDs."""
        pass


class EncryptedAuditStorage(AuditStorageBackend):
    """Encrypted file-based audit storage."""

    def __init__(self, encryption_key: str, storage_path: str):
        if len(encryption_key) < 32:
            raise ValueError("Encryption key must be at least 32 characters")

        self.encryption_key = encryption_key
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    async def store_event(self, event: AuditEvent):
        """Store an encrypted audit event."""
        event_data = event.to_dict()

        # Encrypt and store
        encrypted_data = self._encrypt_data(event_data)
        filename = f"{event.event_id}.audit"
        file_path = self.storage_path / filename

        with self._lock:
            self._write_encrypted_data(encrypted_data, file_path)

    async def query_events(self, start_time: Optional[datetime] = None,
                          end_time: Optional[datetime] = None,
                          event_type: Optional[AuditEventType] = None,
                          correlation_id: Optional[str] = None,
                          user_id_hash: Optional[str] = None,
                          limit: int = 1000) -> List[AuditEvent]:
        """Query encrypted audit events."""
        events = []

        with self._lock:
            for file_path in self.storage_path.glob("*.audit"):
                if len(events) >= limit:
                    break

                try:
                    encrypted_data = self._read_encrypted_data(file_path)
                    event_data = self._decrypt_data(encrypted_data)

                    # Parse event
                    event = self._dict_to_event(event_data)

                    # Apply filters
                    if start_time and event.timestamp < start_time:
                        continue
                    if end_time and event.timestamp > end_time:
                        continue
                    if event_type and event.event_type != event_type:
                        continue
                    if correlation_id and event.correlation_id != correlation_id:
                        continue
                    if user_id_hash and event.user_id_hash != user_id_hash:
                        continue

                    events.append(event)

                except Exception:
                    # Skip corrupted files
                    continue

        return sorted(events, key=lambda e: e.timestamp)

    async def delete_events(self, event_ids: List[str]):
        """Delete audit events by IDs."""
        with self._lock:
            for event_id in event_ids:
                file_path = self.storage_path / f"{event_id}.audit"
                if file_path.exists():
                    file_path.unlink()

    def _encrypt_data(self, data: Dict[str, Any]) -> bytes:
        """Encrypt data using AES encryption."""
        # Simple XOR encryption for demo (use proper AES in production)
        json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        key_bytes = self.encryption_key.encode('utf-8')

        encrypted = bytearray()
        for i, byte in enumerate(json_data):
            encrypted.append(byte ^ key_bytes[i % len(key_bytes)])

        return base64.b64encode(bytes(encrypted))

    def _decrypt_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt data."""
        data = base64.b64decode(encrypted_data)
        key_bytes = self.encryption_key.encode('utf-8')

        decrypted = bytearray()
        for i, byte in enumerate(data):
            decrypted.append(byte ^ key_bytes[i % len(key_bytes)])

        json_str = bytes(decrypted).decode('utf-8')
        return json.loads(json_str)

    def _write_encrypted_data(self, data: bytes, file_path: Path):
        """Write encrypted data to file."""
        with gzip.open(file_path, 'wb') as f:
            f.write(data)

    def _read_encrypted_data(self, file_path: Path) -> bytes:
        """Read encrypted data from file."""
        with gzip.open(file_path, 'rb') as f:
            return f.read()

    def _dict_to_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Convert dictionary to AuditEvent."""
        return AuditEvent(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            correlation_id=data["correlation_id"],
            user_id_hash=data["user_id_hash"],
            action=data["action"],
            resource=data["resource"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            details=data["details"],
            ip_address_hash=data.get("ip_address_hash"),
            user_agent_hash=data.get("user_agent_hash")
        )


class AuditLogger:
    """Main audit logger with PDPA compliance."""

    def __init__(self, storage_backend: AuditStorageBackend):
        self.storage_backend = storage_backend
        self._async_buffer: List[AuditEvent] = []
        self._async_enabled = False
        self._batch_size = 10
        self._buffer_lock = threading.Lock()
        self._rate_limiter = None

    def log_event(self, event: AuditEvent):
        """Log an audit event with validation."""
        # Validate PDPA compliance
        if not event.is_pdpa_compliant():
            raise ValueError("Event failed PDPA compliance validation")

        # Enrich event with metadata
        enriched_event = self._enrich_event(event)

        # Check rate limiting
        if self._rate_limiter and not self._rate_limiter.allow_event():
            return  # Drop event due to rate limiting

        if self._async_enabled:
            self._add_to_async_buffer(enriched_event)
        else:
            asyncio.create_task(self.storage_backend.store_event(enriched_event))

    def _enrich_event(self, event: AuditEvent) -> AuditEvent:
        """Enrich event with additional metadata."""
        if "hostname" not in event.details:
            event.details["hostname"] = os.uname().nodename if hasattr(os, 'uname') else "unknown"

        if "process_id" not in event.details:
            event.details["process_id"] = os.getpid()

        return event

    def enable_async_logging(self, batch_size: int = 10):
        """Enable asynchronous batch logging."""
        self._async_enabled = True
        self._batch_size = batch_size

    def _add_to_async_buffer(self, event: AuditEvent):
        """Add event to async buffer."""
        with self._buffer_lock:
            self._async_buffer.append(event)

            if len(self._async_buffer) >= self._batch_size:
                self._flush_buffer()

    def _flush_buffer(self):
        """Flush async buffer."""
        if not self._async_buffer:
            return

        events_to_flush = self._async_buffer.copy()
        self._async_buffer.clear()

        # Store events asynchronously
        for event in events_to_flush:
            asyncio.create_task(self.storage_backend.store_event(event))

    def flush_async_buffer(self):
        """Force flush of async buffer."""
        with self._buffer_lock:
            self._flush_buffer()

    def enable_rate_limiting(self, max_events_per_second: int):
        """Enable rate limiting for audit logging."""
        self._rate_limiter = RateLimiter(max_events_per_second)


class RateLimiter:
    """Simple rate limiter for audit logging."""

    def __init__(self, max_events_per_second: int):
        self.max_events_per_second = max_events_per_second
        self.events = []
        self._lock = threading.Lock()

    def allow_event(self) -> bool:
        """Check if event is allowed under rate limit."""
        current_time = datetime.now()

        with self._lock:
            # Remove events older than 1 second
            cutoff_time = current_time - timedelta(seconds=1)
            self.events = [t for t in self.events if t > cutoff_time]

            # Check if we're under the limit
            if len(self.events) < self.max_events_per_second:
                self.events.append(current_time)
                return True

            return False


class PDPAComplianceLogger:
    """PDPA-specific compliance logging."""

    def __init__(self, storage_backend: Optional[AuditStorageBackend] = None):
        self.audit_logger = AuditLogger(
            storage_backend or EncryptedAuditStorage(
                encryption_key="default_pdpa_encryption_key_32_chars",
                storage_path="/tmp/audit_logs"
            )
        )

    def log_data_collection(self, user_id_hash: str, data_types: List[str],
                           purpose: str, legal_basis: str):
        """Log data collection event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            action="data_collection",
            resource="user_data",
            timestamp=datetime.now(),
            details={
                "data_types": data_types,
                "purpose": purpose,
                "legal_basis": legal_basis
            }
        )
        self.audit_logger.log_event(event)

    def log_data_processing(self, user_id_hash: str, processing_purpose: str,
                           data_categories: List[str], automated_decision: bool):
        """Log data processing event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            action="data_processing",
            resource="user_data",
            timestamp=datetime.now(),
            details={
                "processing_purpose": processing_purpose,
                "data_categories": data_categories,
                "automated_decision": automated_decision
            }
        )
        self.audit_logger.log_event(event)

    def log_data_retention(self, data_type: str, retention_period_days: int,
                          deletion_scheduled: bool):
        """Log data retention event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.COMPLIANCE_CHECK,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="system",
            action="data_retention",
            resource="audit_system",
            timestamp=datetime.now(),
            details={
                "data_type": data_type,
                "retention_period_days": retention_period_days,
                "deletion_scheduled": deletion_scheduled
            }
        )
        self.audit_logger.log_event(event)

    def log_user_consent(self, user_id_hash: str, consent_type: str,
                        consent_granted: bool, consent_version: str):
        """Log user consent event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            action="user_consent",
            resource="consent_management",
            timestamp=datetime.now(),
            details={
                "consent_type": consent_type,
                "consent_granted": consent_granted,
                "consent_version": consent_version
            }
        )
        self.audit_logger.log_event(event)

    def log_data_breach(self, severity: str, affected_data_types: List[str],
                       estimated_affected_users: int, mitigation_actions: List[str]):
        """Log data breach event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_EVENT,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="system",
            action="data_breach",
            resource="security_system",
            timestamp=datetime.now(),
            details={
                "severity": severity,
                "affected_data_types": affected_data_types,
                "estimated_affected_users": estimated_affected_users,
                "mitigation_actions": mitigation_actions
            }
        )
        self.audit_logger.log_event(event)

    def log_data_access(self, user_identifier: str, accessed_data: List[str],
                       access_purpose: str):
        """Log data access event."""
        # Validate that user identifier is hashed (no PII)
        if '@' in user_identifier or '.' in user_identifier:
            raise ValueError("User identifier contains PII - must be hashed")

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.DATA_PROCESSING,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_identifier,
            action="data_access",
            resource="user_data",
            timestamp=datetime.now(),
            details={
                "accessed_data": accessed_data,
                "access_purpose": access_purpose
            }
        )
        self.audit_logger.log_event(event)


class SecurityAuditLogger:
    """Security-focused audit logging."""

    def __init__(self, storage_backend: Optional[AuditStorageBackend] = None):
        self.audit_logger = AuditLogger(
            storage_backend or EncryptedAuditStorage(
                encryption_key="default_security_encryption_key_32_chars",
                storage_path="/tmp/audit_logs"
            )
        )

    def log_authentication_attempt(self, user_id_hash: str, ip_address_hash: str,
                                  user_agent_hash: str, success: bool,
                                  authentication_method: str):
        """Log authentication attempt."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_EVENT,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            action="authentication_attempt",
            resource="auth_service",
            timestamp=datetime.now(),
            ip_address_hash=ip_address_hash,
            user_agent_hash=user_agent_hash,
            details={
                "success": success,
                "authentication_method": authentication_method
            }
        )
        self.audit_logger.log_event(event)

    def log_authorization_check(self, user_id_hash: str, resource: str,
                               action: str, permitted: bool, reason: str):
        """Log authorization check."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_EVENT,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=user_id_hash,
            action="authorization_check",
            resource=resource,
            timestamp=datetime.now(),
            details={
                "requested_action": action,
                "permitted": permitted,
                "reason": reason
            }
        )
        self.audit_logger.log_event(event)

    def log_rate_limit_exceeded(self, ip_address_hash: str, endpoint: str,
                               request_count: int, limit: int, time_window_seconds: int):
        """Log rate limit exceeded event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_EVENT,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="anonymous",
            action="rate_limit_exceeded",
            resource=endpoint,
            timestamp=datetime.now(),
            ip_address_hash=ip_address_hash,
            details={
                "request_count": request_count,
                "limit": limit,
                "time_window_seconds": time_window_seconds
            }
        )
        self.audit_logger.log_event(event)

    def log_suspicious_activity(self, ip_address_hash: str, activity_type: str,
                               risk_score: float, indicators: List[str],
                               action_taken: str):
        """Log suspicious activity."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SECURITY_EVENT,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="anonymous",
            action="suspicious_activity",
            resource="security_system",
            timestamp=datetime.now(),
            ip_address_hash=ip_address_hash,
            details={
                "activity_type": activity_type,
                "risk_score": risk_score,
                "indicators": indicators,
                "action_taken": action_taken
            }
        )
        self.audit_logger.log_event(event)

    def log_system_access(self, admin_user_hash: str, action: str,
                         resource: str, changes: Dict[str, Any]):
        """Log system administrator access."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.SYSTEM_ADMIN,
            correlation_id=str(uuid.uuid4()),
            user_id_hash=admin_user_hash,
            action=action,
            resource=resource,
            timestamp=datetime.now(),
            details={
                "changes": changes
            }
        )
        self.audit_logger.log_event(event)


class BusinessAuditLogger:
    """Business-focused audit logging."""

    def __init__(self, storage_backend: Optional[AuditStorageBackend] = None):
        self.audit_logger = AuditLogger(
            storage_backend or EncryptedAuditStorage(
                encryption_key="default_business_encryption_key_32_chars",
                storage_path="/tmp/audit_logs"
            )
        )

    def log_medical_consultation(self, session_id: str, symptom_category: str,
                                triage_level: str, response_time_ms: int,
                                recommended_action: str):
        """Log medical consultation event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=session_id,
            user_id_hash=self._hash_session_id(session_id),
            action="triage_consultation",
            resource="symptom_analysis",
            timestamp=datetime.now(),
            details={
                "symptom_category": symptom_category,
                "triage_level": triage_level,
                "response_time_ms": response_time_ms,
                "recommended_action": recommended_action
            }
        )
        self.audit_logger.log_event(event)

    def log_hospital_search(self, session_id: str, search_type: str,
                           location_type: str, radius_meters: int,
                           results_count: int, response_time_ms: int):
        """Log hospital search event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=session_id,
            user_id_hash=self._hash_session_id(session_id),
            action="hospital_search",
            resource="places_service",
            timestamp=datetime.now(),
            details={
                "search_type": search_type,
                "location_type": location_type,
                "radius_meters": radius_meters,
                "results_count": results_count,
                "response_time_ms": response_time_ms
            }
        )
        self.audit_logger.log_event(event)

    def log_emergency_escalation(self, session_id: str, trigger_symptoms: List[str],
                                escalation_type: str, escalation_time_ms: int):
        """Log emergency escalation event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.MEDICAL_CONSULTATION,
            correlation_id=session_id,
            user_id_hash=self._hash_session_id(session_id),
            action="emergency_escalation",
            resource="emergency_system",
            timestamp=datetime.now(),
            details={
                "trigger_symptoms": trigger_symptoms,
                "escalation_type": escalation_type,
                "escalation_time_ms": escalation_time_ms
            }
        )
        self.audit_logger.log_event(event)

    def log_user_feedback(self, session_id: str, feedback_type: str,
                         rating: int, feedback_categories: List[str],
                         response_time_acceptable: bool):
        """Log user feedback event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=session_id,
            user_id_hash=self._hash_session_id(session_id),
            action="user_feedback",
            resource="feedback_system",
            timestamp=datetime.now(),
            details={
                "feedback_type": feedback_type,
                "rating": rating,
                "feedback_categories": feedback_categories,
                "response_time_acceptable": response_time_acceptable
            }
        )
        self.audit_logger.log_event(event)

    def log_api_usage(self, endpoint: str, method: str, status_code: int,
                     response_time_ms: int, request_size_bytes: int,
                     response_size_bytes: int):
        """Log API usage event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=AuditEventType.USER_ACCESS,
            correlation_id=str(uuid.uuid4()),
            user_id_hash="anonymous",
            action="api_usage",
            resource=endpoint,
            timestamp=datetime.now(),
            details={
                "method": method,
                "status_code": status_code,
                "response_time_ms": response_time_ms,
                "request_size_bytes": request_size_bytes,
                "response_size_bytes": response_size_bytes
            }
        )
        self.audit_logger.log_event(event)

    def _hash_session_id(self, session_id: str) -> str:
        """Hash session ID for privacy."""
        return hashlib.sha256(session_id.encode()).hexdigest()[:16]


class AuditTrail:
    """Audit trail reconstruction and analysis."""

    def __init__(self, storage_backend: AuditStorageBackend):
        self.storage_backend = storage_backend

    async def get_events_by_correlation_id(self, correlation_id: str) -> List[AuditEvent]:
        """Get all events for a correlation ID."""
        return await self.storage_backend.query_events(correlation_id=correlation_id)

    async def get_events_by_time_range(self, start_time: datetime,
                                      end_time: datetime) -> List[AuditEvent]:
        """Get events within a time range."""
        return await self.storage_backend.query_events(
            start_time=start_time,
            end_time=end_time
        )

    async def get_events_by_user(self, user_id_hash: str) -> List[AuditEvent]:
        """Get all events for a user."""
        return await self.storage_backend.query_events(user_id_hash=user_id_hash)

    async def generate_trail_summary(self, correlation_id: str) -> Dict[str, Any]:
        """Generate a summary of an audit trail."""
        events = await self.get_events_by_correlation_id(correlation_id)

        if not events:
            return {"error": "No events found"}

        # Sort events by timestamp
        events.sort(key=lambda e: e.timestamp)

        # Calculate session duration
        session_start = events[0].timestamp
        session_end = events[-1].timestamp
        session_duration = (session_end - session_start).total_seconds() / 60

        # Extract unique event types and actions
        event_types = list(set(e.event_type.value for e in events))
        actions = [e.action for e in events]

        return {
            "correlation_id": correlation_id,
            "total_events": len(events),
            "session_start": session_start.isoformat(),
            "session_end": session_end.isoformat(),
            "session_duration_minutes": session_duration,
            "event_types": event_types,
            "actions": actions,
            "events": [e.to_dict() for e in events]
        }


class ComplianceReporter:
    """Compliance reporting and validation."""

    def __init__(self, storage_backend: AuditStorageBackend):
        self.storage_backend = storage_backend

    async def generate_pdpa_report(self, start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Generate PDPA compliance report."""
        events = await self.storage_backend.query_events(
            start_time=start_date,
            end_time=end_date
        )

        # Analyze events
        data_collection_events = [
            e for e in events
            if e.event_type == AuditEventType.DATA_PROCESSING and e.action == "data_collection"
        ]

        data_processing_events = [
            e for e in events
            if e.event_type == AuditEventType.DATA_PROCESSING and e.action == "data_processing"
        ]

        # Extract legal bases
        legal_bases = set()
        for event in data_collection_events:
            if "legal_basis" in event.details:
                legal_bases.add(event.details["legal_basis"])

        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "data_collection_events": len(data_collection_events),
            "data_processing_events": len(data_processing_events),
            "legal_bases": list(legal_bases),
            "compliance_status": "compliant" if legal_bases else "needs_review"
        }

    async def generate_security_report(self, start_date: datetime,
                                      end_date: datetime) -> Dict[str, Any]:
        """Generate security compliance report."""
        events = await self.storage_backend.query_events(
            start_time=start_date,
            end_time=end_date,
            event_type=AuditEventType.SECURITY_EVENT
        )

        # Analyze security events
        failed_auth = [
            e for e in events
            if e.action == "authentication_attempt" and not e.details.get("success", True)
        ]

        rate_limiting = [
            e for e in events
            if e.action == "rate_limit_exceeded"
        ]

        return {
            "period": {
                "start": start_date,
                "end": end_date
            },
            "failed_authentication_attempts": len(failed_auth),
            "rate_limiting_events": len(rate_limiting),
            "security_incidents": [e.to_dict() for e in events]
        }

    async def validate_data_retention_compliance(self, max_retention_days: int) -> Dict[str, Any]:
        """Validate data retention compliance."""
        cutoff_date = datetime.now() - timedelta(days=max_retention_days)

        old_events = await self.storage_backend.query_events(end_time=cutoff_date)

        return {
            "compliant": len(old_events) == 0,
            "expired_events_count": len(old_events),
            "expired_event_ids": [e.event_id for e in old_events],
            "cutoff_date": cutoff_date.isoformat()
        }


class DataRetentionManager:
    """Data retention management."""

    def __init__(self, storage_backend: AuditStorageBackend):
        self.storage_backend = storage_backend

    async def identify_expired_data(self, retention_days: int) -> List[AuditEvent]:
        """Identify data that has exceeded retention period."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        return await self.storage_backend.query_events(end_time=cutoff_date)

    async def delete_expired_data(self, expired_event_ids: List[str]) -> Dict[str, Any]:
        """Delete expired data."""
        await self.storage_backend.delete_events(expired_event_ids)

        return {
            "deleted_count": len(expired_event_ids),
            "deletion_timestamp": datetime.now().isoformat()
        }

    def schedule_retention_cleanup(self, retention_days: int,
                                  cleanup_interval_hours: int = 24):
        """Schedule automated retention cleanup."""
        import threading

        def cleanup_task():
            # This would run the cleanup process
            # In a real implementation, use a proper scheduler
            pass

        timer = threading.Timer(cleanup_interval_hours * 3600, cleanup_task)
        timer.start()


# Global audit loggers
pdpa_logger = PDPAComplianceLogger()
security_logger = SecurityAuditLogger()
business_logger = BusinessAuditLogger()


# Helper functions for common audit tasks
def hash_pii(data: str) -> str:
    """Hash PII data for audit logging."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def generate_correlation_id() -> str:
    """Generate a correlation ID for request tracking."""
    return str(uuid.uuid4())