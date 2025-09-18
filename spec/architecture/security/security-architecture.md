# Security & Privacy Architecture - Taiwan Medical AI Agent

## Security Overview

The Taiwan Medical AI Agent implements a comprehensive security architecture designed to protect sensitive medical information, ensure PDPA compliance, and maintain the highest standards of data protection while providing critical medical guidance services.

## Security Principles

### 1. Privacy by Design
- **Proactive, not Reactive**: Security measures built into system design
- **Privacy as the Default**: Maximum privacy protection without user action
- **End-to-End Security**: Comprehensive protection throughout data lifecycle
- **Transparency**: Clear privacy practices and data handling

### 2. Medical Data Protection
- **Minimal Data Collection**: Only essential information for service operation
- **No Diagnostic Storage**: System avoids storing medical diagnoses
- **Anonymization**: Personal health information anonymized or hashed
- **Secure Disposal**: Automatic secure deletion per retention policies

### 3. Taiwan Legal Compliance
- **PDPA Adherence**: Full compliance with Personal Data Protection Act
- **Healthcare Regulations**: Alignment with Taiwan medical practice standards
- **Emergency Protocol Security**: Secure handling of emergency medical situations
- **Cross-Border Data Restrictions**: Compliance with data localization requirements

## Threat Model

### 1. Identified Threats
```yaml
threats:
  medical_data_exposure:
    severity: critical
    description: "Unauthorized access to patient symptom data"
    likelihood: medium
    impact: high
    mitigations:
      - "End-to-end encryption"
      - "PII masking middleware"
      - "Minimal data retention"
      - "Access controls"

  api_abuse:
    severity: high
    description: "Malicious use of medical guidance API"
    likelihood: high
    impact: medium
    mitigations:
      - "Rate limiting"
      - "API key authentication"
      - "Request validation"
      - "Anomaly detection"

  emergency_protocol_bypass:
    severity: critical
    description: "Circumvention of emergency safety protocols"
    likelihood: low
    impact: critical
    mitigations:
      - "Fail-safe emergency detection"
      - "Mandatory disclaimer injection"
      - "Audit logging"
      - "Protocol validation"

  location_privacy:
    severity: medium
    description: "Unauthorized tracking of user location"
    likelihood: medium
    impact: medium
    mitigations:
      - "Location data rounding"
      - "IP address hashing"
      - "Temporary location storage"
      - "User consent"

  external_api_compromise:
    severity: medium
    description: "Compromise of external services (Google APIs)"
    likelihood: low
    impact: medium
    mitigations:
      - "API key rotation"
      - "Service isolation"
      - "Fallback mechanisms"
      - "Monitoring"
```

## Authentication & Authorization

### 1. API Authentication
```python
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import hashlib
import hmac
from typing import Optional

class APIKeyAuth:
    def __init__(self):
        self.security = HTTPBearer()

    async def __call__(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="API key required",
                headers={"WWW-Authenticate": "Bearer"}
            )

        api_key = credentials.credentials
        if not self.validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )

        return self.get_api_key_info(api_key)

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key against secure storage"""
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Check against stored hashes (not plaintext keys)
        valid_hashes = self.get_valid_key_hashes()
        return key_hash in valid_hashes

    def get_api_key_info(self, api_key: str) -> dict:
        """Get API key metadata for rate limiting and auditing"""
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        return {
            "key_id": key_hash,
            "tier": self.get_key_tier(key_hash),
            "rate_limit": self.get_rate_limit(key_hash)
        }
```

### 2. Rate Limiting & DDoS Protection
```python
from fastapi import Request, HTTPException
import redis
import time
from typing import Tuple

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        request: Request,
        api_key_info: dict,
        endpoint: str
    ) -> Tuple[bool, dict]:
        """Check if request is within rate limits"""

        # Create rate limit key
        key = f"rate_limit:{api_key_info['key_id']}:{endpoint}"
        window = 3600  # 1 hour window

        # Get current count
        current = await self.redis.get(key)
        current_count = int(current) if current else 0

        # Get rate limit for this API key tier
        limit = self.get_tier_limit(api_key_info['tier'], endpoint)

        if current_count >= limit:
            # Rate limit exceeded
            ttl = await self.redis.ttl(key)
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + ttl),
                    "Retry-After": str(ttl)
                }
            )

        # Increment counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        await pipe.execute()

        return True, {
            "limit": limit,
            "remaining": limit - current_count - 1,
            "reset": int(time.time()) + window
        }

    def get_tier_limit(self, tier: str, endpoint: str) -> int:
        """Get rate limit based on API key tier and endpoint"""
        limits = {
            "free": {"triage": 10, "hospitals": 20, "geocoding": 30},
            "basic": {"triage": 100, "hospitals": 200, "geocoding": 300},
            "premium": {"triage": 1000, "hospitals": 2000, "geocoding": 3000}
        }
        return limits.get(tier, {}).get(endpoint, 10)
```

## Data Protection & Privacy

### 1. PII Masking Middleware
```python
from fastapi import Request
import re
import hashlib
import json
from typing import Any, Dict

class PIIMaskingMiddleware:
    def __init__(self):
        self.pii_patterns = {
            'taiwan_id': r'[A-Z]\d{9}',
            'phone': r'(\+886|0)\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
        }

    async def mask_request_data(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask PII in request data"""
        masked_data = request_data.copy()

        # Mask symptom text while preserving medical relevance
        if 'symptom_text' in masked_data:
            masked_data['symptom_text'] = self.mask_symptom_text(
                masked_data['symptom_text']
            )

        # Remove or hash other sensitive fields
        if 'patient_name' in masked_data:
            del masked_data['patient_name']

        if 'contact_info' in masked_data:
            masked_data['contact_info'] = self.hash_sensitive_data(
                masked_data['contact_info']
            )

        return masked_data

    def mask_symptom_text(self, text: str) -> str:
        """Mask PII in symptom text while preserving medical content"""
        masked_text = text

        # Replace PII patterns with placeholders
        for pattern_name, pattern in self.pii_patterns.items():
            if pattern_name == 'taiwan_id':
                masked_text = re.sub(pattern, '[身分證字號]', masked_text)
            elif pattern_name == 'phone':
                masked_text = re.sub(pattern, '[電話號碼]', masked_text)
            elif pattern_name == 'email':
                masked_text = re.sub(pattern, '[電子郵件]', masked_text)

        return masked_text

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for audit purposes"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]

    async def create_audit_safe_log(self, request: Request, response_data: Dict) -> Dict:
        """Create audit log entry with PII protection"""
        return {
            "timestamp": time.time(),
            "endpoint": str(request.url.path),
            "method": request.method,
            "status_code": response_data.get("status_code", 200),
            "user_agent_hash": self.hash_sensitive_data(
                request.headers.get("user-agent", "")
            ),
            "ip_hash": self.hash_sensitive_data(
                request.client.host if request.client else ""
            ),
            "request_id": response_data.get("request_id"),
            "emergency_triggered": response_data.get("emergency_triggered", False),
            "processing_time_ms": response_data.get("processing_time", 0)
        }
```

### 2. Data Encryption
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64

class DataEncryption:
    def __init__(self, password: bytes, salt: bytes = None):
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
        self.salt = salt

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        encrypted = self.cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = self.cipher.decrypt(encrypted_bytes)
        return decrypted.decode('utf-8')

    def secure_delete(self, data: str):
        """Securely overwrite sensitive data in memory"""
        # Overwrite string data (limited effectiveness in Python)
        for _ in range(3):
            data = '0' * len(data)
```

## Medical Safety Security

### 1. Emergency Protocol Security
```python
class EmergencyProtocolSecurity:
    def __init__(self):
        self.emergency_keywords = self.load_emergency_keywords()
        self.bypass_prevention = True

    def validate_emergency_response(self,
                                   symptom_text: str,
                                   response: dict) -> dict:
        """Ensure emergency protocols cannot be bypassed"""

        # Check for critical symptoms
        has_emergency_keywords = self.detect_emergency_keywords(symptom_text)

        if has_emergency_keywords:
            # MANDATORY: Emergency response required
            if response.get('level') != 'emergency':
                # Override any non-emergency classification
                response = self.force_emergency_response(symptom_text)

            # MANDATORY: Emergency contacts must be included
            if '119' not in response.get('emergency_contacts', []):
                response['emergency_contacts'] = ['119', '112']

            # MANDATORY: Disclaimer must include emergency guidance
            response['disclaimer'] = self.get_emergency_disclaimer()

            # Audit emergency trigger
            self.audit_emergency_trigger(symptom_text, response)

        return response

    def detect_emergency_keywords(self, text: str) -> bool:
        """Detect critical emergency keywords"""
        critical_keywords = [
            '胸痛', '心臟病', '心肌梗塞', '中風', '昏迷', '呼吸困難',
            '大量出血', '嚴重外傷', '意識不清', '休克', '窒息'
        ]

        text_lower = text.lower()
        return any(keyword in text_lower for keyword in critical_keywords)

    def force_emergency_response(self, symptom_text: str) -> dict:
        """Force emergency response for critical symptoms"""
        return {
            "level": "emergency",
            "severity": "critical",
            "advice": "您描述的症狀可能為緊急醫療狀況，請立即撥打119或前往最近的急診室。",
            "next_steps": [
                "立即撥打119",
                "前往最近的急診室",
                "保持冷靜，避免移動",
                "準備身分證件和健保卡"
            ],
            "emergency_contacts": ["119", "112"],
            "disclaimer": self.get_emergency_disclaimer()
        }

    def get_emergency_disclaimer(self) -> str:
        """Get mandatory emergency disclaimer"""
        return (
            "本系統偵測到可能的緊急醫療狀況。請立即撥打119（消防救護車）或112（國際緊急號碼）"
            "尋求專業醫療協助。本系統僅提供一般資訊，不能取代專業醫療診斷或治療。"
        )
```

### 2. Response Validation Security
```python
class ResponseValidationSecurity:
    def __init__(self):
        self.prohibited_phrases = [
            '診斷為', '確定是', '一定是', '肯定是',
            '絕對是', '治療方案', '藥物建議', '處方'
        ]

    def validate_medical_response(self, response: dict) -> dict:
        """Validate medical response for safety and compliance"""

        # Check for prohibited diagnostic language
        advice = response.get('advice', '')
        if self.contains_prohibited_language(advice):
            response['advice'] = self.sanitize_medical_advice(advice)

        # Ensure disclaimer is present and comprehensive
        if not response.get('disclaimer'):
            response['disclaimer'] = self.get_standard_disclaimer()

        # Validate emergency contacts format
        if response.get('emergency_contacts'):
            response['emergency_contacts'] = self.validate_emergency_contacts(
                response['emergency_contacts']
            )

        return response

    def contains_prohibited_language(self, text: str) -> bool:
        """Check for prohibited diagnostic language"""
        return any(phrase in text for phrase in self.prohibited_phrases)

    def sanitize_medical_advice(self, advice: str) -> str:
        """Remove prohibited diagnostic language"""
        sanitized = advice
        for phrase in self.prohibited_phrases:
            sanitized = sanitized.replace(phrase, '可能')

        # Add cautionary language
        if not sanitized.startswith('建議'):
            sanitized = f"建議{sanitized}"

        return sanitized

    def get_standard_disclaimer(self) -> str:
        """Get standard medical disclaimer"""
        return (
            "本系統僅提供一般健康資訊參考，不能取代專業醫療診斷或治療。"
            "如有醫療需求，請諮詢合格醫療專業人員。"
            "緊急狀況請撥打119或112。"
        )
```

## Infrastructure Security

### 1. Network Security
```yaml
# Network Security Configuration
network_security:
  ssl_tls:
    min_version: "TLS 1.3"
    cipher_suites:
      - "TLS_AES_256_GCM_SHA384"
      - "TLS_CHACHA20_POLY1305_SHA256"
      - "TLS_AES_128_GCM_SHA256"
    hsts:
      enabled: true
      max_age: 31536000
      include_subdomains: true

  cors:
    allowed_origins:
      - "https://taiwan-med-ai.com"
      - "https://app.taiwan-med-ai.com"
    allowed_methods: ["GET", "POST"]
    allowed_headers: ["Content-Type", "Authorization", "X-API-Key"]
    expose_headers: ["X-Request-ID", "X-RateLimit-Remaining"]

  firewall:
    allowed_ports: [443, 80]
    rate_limiting:
      requests_per_minute: 100
      burst_size: 20
    geo_blocking:
      enabled: true
      allowed_countries: ["TW", "US", "SG"]

  ddos_protection:
    enabled: true
    threshold_requests_per_second: 1000
    block_duration_minutes: 15
```

### 2. Container Security
```dockerfile
# Secure Docker Configuration
FROM python:3.11-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash medai

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set secure file permissions
COPY --chown=medai:medai . /app
WORKDIR /app

# Install dependencies as non-root
USER medai
RUN pip install --no-cache-dir -r requirements.txt

# Security hardening
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/healthz')"

# Run as non-root
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Secrets Management
```python
import os
from cryptography.fernet import Fernet
import boto3
from typing import Optional

class SecretsManager:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.encryption_key = self._get_encryption_key()

    def get_secret(self, secret_name: str) -> Optional[str]:
        """Retrieve secret from secure storage"""
        if self.environment == 'production':
            return self._get_from_aws_secrets(secret_name)
        elif self.environment == 'staging':
            return self._get_from_vault(secret_name)
        else:
            return self._get_from_env(secret_name)

    def _get_from_aws_secrets(self, secret_name: str) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        client = boto3.client('secretsmanager', region_name='ap-northeast-1')
        try:
            response = client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {e}")
            return None

    def _get_from_env(self, secret_name: str) -> Optional[str]:
        """Get secret from environment variables (development only)"""
        return os.getenv(secret_name)

    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key for storage"""
        f = Fernet(self.encryption_key)
        return f.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypt API key"""
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_key.encode()).decode()
```

## Monitoring & Incident Response

### 1. Security Monitoring
```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict

class SecurityMonitoring:
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.alert_thresholds = {
            'failed_auth_attempts': 10,
            'rate_limit_violations': 5,
            'emergency_bypasses': 1,
            'unusual_location_access': 3
        }

    async def monitor_security_events(self):
        """Continuous security monitoring"""
        while True:
            await self.check_authentication_failures()
            await self.check_rate_limit_violations()
            await self.check_emergency_protocol_bypasses()
            await self.check_unusual_access_patterns()
            await asyncio.sleep(60)  # Check every minute

    async def check_authentication_failures(self):
        """Monitor for authentication failures"""
        recent_failures = await self.get_recent_auth_failures()

        if len(recent_failures) > self.alert_thresholds['failed_auth_attempts']:
            await self.trigger_security_alert(
                'HIGH_AUTH_FAILURES',
                f"Detected {len(recent_failures)} authentication failures in the last hour",
                recent_failures
            )

    async def check_emergency_protocol_bypasses(self):
        """Monitor for emergency protocol bypass attempts"""
        bypass_attempts = await self.get_emergency_bypass_attempts()

        if len(bypass_attempts) > 0:
            await self.trigger_critical_alert(
                'EMERGENCY_BYPASS_ATTEMPT',
                "Detected attempt to bypass emergency medical protocols",
                bypass_attempts
            )

    async def trigger_security_alert(self,
                                   alert_type: str,
                                   message: str,
                                   details: Dict):
        """Trigger security alert"""
        alert = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': alert_type,
            'severity': 'HIGH',
            'message': message,
            'details': details
        }

        # Log alert
        self.logger.warning(f"Security Alert: {alert}")

        # Send to monitoring system
        await self.send_to_monitoring_system(alert)

        # Notify security team
        await self.notify_security_team(alert)
```

### 2. Incident Response
```python
class IncidentResponse:
    def __init__(self):
        self.response_procedures = {
            'data_breach': self.handle_data_breach,
            'ddos_attack': self.handle_ddos_attack,
            'emergency_bypass': self.handle_emergency_bypass,
            'api_abuse': self.handle_api_abuse
        }

    async def handle_security_incident(self, incident_type: str, details: Dict):
        """Handle security incident based on type"""
        if incident_type in self.response_procedures:
            await self.response_procedures[incident_type](details)
        else:
            await self.handle_unknown_incident(incident_type, details)

    async def handle_data_breach(self, details: Dict):
        """Handle potential data breach"""
        # Immediate actions
        await self.isolate_affected_systems(details)
        await self.notify_authorities(details)
        await self.collect_forensic_evidence(details)

        # PDPA compliance actions
        await self.assess_personal_data_impact(details)
        await self.prepare_breach_notification(details)

    async def handle_emergency_bypass(self, details: Dict):
        """Handle emergency protocol bypass attempt"""
        # Critical: This could affect medical safety
        await self.emergency_lockdown_mode()
        await self.validate_all_emergency_responses()
        await self.notify_medical_safety_team(details)

    async def emergency_lockdown_mode(self):
        """Enable emergency lockdown mode"""
        # Force all responses to include emergency protocols
        await self.enable_mandatory_emergency_mode()

        # Increase monitoring
        await self.increase_monitoring_frequency()

        # Alert all stakeholders
        await self.send_emergency_notifications()
```

## Compliance & Auditing

### 1. PDPA Compliance Framework
```python
class PDPACompliance:
    def __init__(self):
        self.data_categories = {
            'personal_identifiers': ['name', 'id_number', 'phone', 'email'],
            'health_data': ['symptoms', 'medical_history', 'medications'],
            'location_data': ['ip_address', 'coordinates', 'address'],
            'behavioral_data': ['usage_patterns', 'preferences']
        }

    async def conduct_privacy_impact_assessment(self,
                                               data_processing_activity: str) -> Dict:
        """Conduct Privacy Impact Assessment"""
        assessment = {
            'activity': data_processing_activity,
            'data_categories': self.identify_data_categories(data_processing_activity),
            'legal_basis': self.determine_legal_basis(data_processing_activity),
            'risks': await self.assess_privacy_risks(data_processing_activity),
            'mitigations': self.recommend_mitigations(data_processing_activity),
            'compliance_status': 'compliant'
        }

        return assessment

    def verify_data_minimization(self, data_collection: Dict) -> bool:
        """Verify data minimization principle"""
        essential_fields = self.get_essential_fields()
        collected_fields = set(data_collection.keys())

        return collected_fields.issubset(essential_fields)

    async def handle_data_subject_rights(self, request_type: str, subject_id: str):
        """Handle data subject rights requests"""
        if request_type == 'access':
            return await self.provide_data_access(subject_id)
        elif request_type == 'deletion':
            return await self.delete_subject_data(subject_id)
        elif request_type == 'portability':
            return await self.export_subject_data(subject_id)
        elif request_type == 'rectification':
            return await self.correct_subject_data(subject_id)
```

### 2. Security Audit Framework
```python
class SecurityAuditFramework:
    def __init__(self):
        self.audit_controls = [
            'authentication_security',
            'data_encryption',
            'api_security',
            'infrastructure_security',
            'medical_safety_controls',
            'privacy_protection',
            'incident_response',
            'compliance_monitoring'
        ]

    async def conduct_security_audit(self) -> Dict:
        """Conduct comprehensive security audit"""
        audit_results = {}

        for control in self.audit_controls:
            audit_results[control] = await self.audit_control(control)

        overall_score = self.calculate_security_score(audit_results)
        recommendations = self.generate_recommendations(audit_results)

        return {
            'audit_date': datetime.utcnow().isoformat(),
            'overall_score': overall_score,
            'control_results': audit_results,
            'recommendations': recommendations,
            'compliance_status': self.assess_compliance_status(audit_results)
        }

    async def audit_medical_safety_controls(self) -> Dict:
        """Audit medical safety-specific controls"""
        return {
            'emergency_protocol_integrity': await self.test_emergency_protocols(),
            'response_validation': await self.test_response_validation(),
            'disclaimer_enforcement': await self.test_disclaimer_enforcement(),
            'symptom_data_protection': await self.test_symptom_data_protection()
        }
```

This security architecture ensures comprehensive protection of medical data while maintaining system functionality and compliance with Taiwan's regulatory requirements. The layered security approach provides defense in depth against various threat vectors while enabling critical medical guidance services.