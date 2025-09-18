# Data Architecture - Taiwan Medical AI Agent

## Data Architecture Overview

The Taiwan Medical AI Agent employs a privacy-first data architecture designed for PDPA compliance, minimal data storage, and efficient caching strategies. The system prioritizes data minimization while ensuring optimal performance and Taiwan localization.

## Core Data Principles

### 1. Privacy by Design (PDPA Compliance)
- **Data Minimization**: Collect only necessary data for service operation
- **Purpose Limitation**: Data used only for stated medical guidance purposes
- **Storage Limitation**: Minimal retention periods with automatic cleanup
- **Anonymization**: PII masking and hashing for audit purposes

### 2. Medical Safety Data Handling
- **No Diagnostic Storage**: System doesn't store diagnostic conclusions
- **Symptom Anonymization**: Symptom text hashed or aggregated for analytics
- **Emergency Audit Trail**: Trackable emergency protocol triggers
- **Disclaimer Enforcement**: Mandatory medical disclaimers in all responses

### 3. Taiwan Localization Data
- **Language Consistency**: All stored text in Traditional Chinese (zh-TW)
- **Regional Configuration**: Taiwan-specific emergency numbers and protocols
- **Healthcare System Integration**: NHIA registry data integration
- **Cultural Appropriateness**: Taiwan healthcare context in all data models

## Data Storage Layers

### 1. Configuration Layer (Environment Variables)
```yaml
# Environment Configuration
DATABASE_URL: "postgresql://user:pass@localhost:5432/medai"
REDIS_URL: "redis://localhost:6379/0"
GOOGLE_PLACES_API_KEY: "${GOOGLE_PLACES_API_KEY}"
GOOGLE_GEOCODING_API_KEY: "${GOOGLE_GEOCODING_API_KEY}"

# Taiwan Localization
DEFAULT_LANGUAGE: "zh-TW"
DEFAULT_REGION: "TW"
TIMEZONE: "Asia/Taipei"

# Medical Safety
EMERGENCY_NUMBERS: "119,110,112,113,165"
EMERGENCY_KEYWORDS_FILE: "/config/emergency-keywords-zh-tw.yaml"

# Privacy & Compliance
AUDIT_RETENTION_DAYS: 30
PII_MASKING_ENABLED: true
PDPA_COMPLIANCE_MODE: true
```

### 2. Static Configuration Data (YAML/JSON)
```yaml
# Taiwan Emergency Configuration
emergency_contacts:
  - number: "119"
    description: "消防救護車"
    category: "medical_emergency"
    available_24h: true
    priority: 1

  - number: "110"
    description: "警察局"
    category: "police"
    available_24h: true
    priority: 2

  - number: "112"
    description: "行動電話國際緊急號碼"
    category: "international_emergency"
    available_24h: true
    note: "無卡亦可撥打"
    priority: 1

# Medical Safety Rules
emergency_keywords:
  critical:
    - "胸痛"
    - "呼吸困難"
    - "心臟病"
    - "中風"
    - "昏迷"
    - "大量出血"
    - "嚴重外傷"

  urgent:
    - "高燒"
    - "劇烈頭痛"
    - "嚴重腹痛"
    - "持續嘔吐"
    - "意識不清"

# Taiwan Localization
localization:
  language: "zh-TW"
  region: "TW"
  date_format: "YYYY年MM月DD日"
  time_format: "HH:mm"
  currency: "TWD"
  measurement_units: "metric"
```

### 3. Caching Layer (Redis)
```yaml
# Cache Key Patterns and TTL
cache_patterns:
  # Geocoding Results
  "geocoding:{address_hash}":
    ttl: 86400  # 24 hours
    data: {latitude, longitude, formatted_address}

  # Places Search Results
  "places:{lat}:{lng}:{radius}:{type}":
    ttl: 3600   # 1 hour
    data: {hospitals_list, search_metadata}

  # NHIA Hospital Verification
  "nhia:hospital:{place_id}":
    ttl: 21600  # 6 hours
    data: {is_contracted, nhia_code, verification_status}

  # Emergency Numbers Cache
  "emergency:contacts:zh-tw":
    ttl: 604800 # 7 days
    data: {emergency_numbers_list}

  # Rate Limiting
  "rate_limit:{api_key}:{endpoint}":
    ttl: 3600   # 1 hour
    data: {request_count, window_start}

  # Session Data (if needed)
  "session:{session_id}":
    ttl: 1800   # 30 minutes
    data: {user_preferences, location_cache}
```

### 4. NHIA Registry Data (Local Cache)
```sql
-- NHIA Hospital Registry (Local SQLite/PostgreSQL)
CREATE TABLE nhia_hospitals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nhia_code VARCHAR(20) UNIQUE NOT NULL,
    name_zh_tw VARCHAR(255) NOT NULL,
    name_en VARCHAR(255),
    address_zh_tw TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100) NOT NULL,
    postal_code VARCHAR(10),
    phone VARCHAR(20),
    website VARCHAR(255),
    hospital_type VARCHAR(50) NOT NULL, -- 醫學中心, 區域醫院, 地區醫院
    bed_count INTEGER,
    has_emergency BOOLEAN DEFAULT false,
    specialties JSONB, -- Array of medical specialties
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    is_active BOOLEAN DEFAULT true,
    contracted_services JSONB, -- NHIA contracted services
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for efficient searching
    INDEX idx_nhia_code (nhia_code),
    INDEX idx_name_zh_tw (name_zh_tw),
    INDEX idx_city_district (city, district),
    INDEX idx_location (location_lat, location_lng),
    INDEX idx_has_emergency (has_emergency),
    INDEX idx_is_active (is_active)
);

-- Sample Data Structure
INSERT INTO nhia_hospitals VALUES (
    gen_random_uuid(),
    '0501140010',
    '國立臺灣大學醫學院附設醫院',
    'National Taiwan University Hospital',
    '台北市中正區中山南路7號',
    '台北市',
    '中正區',
    '100',
    '+886-2-2312-3456',
    'https://www.ntuh.gov.tw',
    '醫學中心',
    2500,
    true,
    '["內科", "外科", "婦產科", "小兒科", "急診醫學科", "神經科", "精神科", "皮膚科", "泌尿科", "眼科", "耳鼻喉科", "骨科", "復健科", "麻醉科", "病理科", "放射科"]'::jsonb,
    25.0408,
    121.5198,
    true,
    '{"general_practice": true, "specialist_care": true, "emergency_care": true}'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
```

### 5. Audit and Compliance Data
```sql
-- PDPA-Compliant Audit Log
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    endpoint VARCHAR(100) NOT NULL,
    method VARCHAR(10) NOT NULL,
    status_code INTEGER NOT NULL,
    user_agent_hash VARCHAR(64), -- Hashed for privacy
    ip_address_hash VARCHAR(64), -- Hashed for privacy
    api_key_id VARCHAR(50), -- Reference, not actual key
    processing_time_ms INTEGER,
    error_code VARCHAR(50),
    emergency_triggered BOOLEAN DEFAULT false,
    location_lat_rounded DECIMAL(6, 4), -- Rounded to ~100m precision
    location_lng_rounded DECIMAL(7, 4), -- Rounded to ~100m precision
    symptom_category VARCHAR(50), -- Categorized, not raw text
    hospital_search_radius INTEGER,
    hospital_results_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes for analytics
    INDEX idx_endpoint (endpoint),
    INDEX idx_status_code (status_code),
    INDEX idx_emergency_triggered (emergency_triggered),
    INDEX idx_created_at (created_at),
    INDEX idx_request_id (request_id)
) PARTITION BY RANGE (created_at);

-- Partitioning for performance and compliance
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
-- ... additional monthly partitions

-- Automatic cleanup policy (PDPA compliance)
-- Drop partitions older than retention period
```

## Data Models (Pydantic)

### 1. Core Medical Models
```python
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum

class TriageLevel(str, Enum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"
    SELF_CARE = "self_care"

class PatientGender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    NOT_SPECIFIED = "not_specified"

class SymptomCategory(str, Enum):
    PAIN = "pain"
    FEVER = "fever"
    RESPIRATORY = "respiratory"
    GASTROINTESTINAL = "gastrointestinal"
    NEUROLOGICAL = "neurological"
    CARDIOVASCULAR = "cardiovascular"
    DERMATOLOGICAL = "dermatological"
    OTHER = "other"

class TriageRequest(BaseModel):
    symptom_text: str = Field(..., min_length=1, max_length=1000, description="症狀描述")
    patient_age: Optional[int] = Field(None, ge=0, le=120, description="患者年齡")
    patient_gender: Optional[PatientGender] = None

    @validator('symptom_text')
    def validate_symptom_text(cls, v):
        # Basic validation for Traditional Chinese content
        if not v.strip():
            raise ValueError('症狀描述不得為空')
        return v.strip()

class TriageResponse(BaseModel):
    request_id: str
    level: TriageLevel
    severity: Literal["critical", "high", "moderate", "mild"]
    advice: str = Field(..., description="醫療建議")
    next_steps: List[str] = Field(..., description="建議採取的行動")
    emergency_contacts: List[str] = Field(default=["119", "112"])
    disclaimer: str = Field(..., description="醫療免責聲明")
    timestamp: datetime
    locale: Literal["zh-TW"] = "zh-TW"

    # Optional fields
    self_care_advice: Optional[List[Dict[str, str]]] = None
    warning_signs: Optional[List[str]] = None
```

### 2. Location and Hospital Models
```python
class Location(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @validator('latitude', 'longitude')
    def validate_taiwan_bounds(cls, v, field):
        # Validate coordinates are within Taiwan bounds
        if field.name == 'latitude' and not (21.5 <= v <= 26.5):
            raise ValueError('緯度必須在台灣範圍內')
        if field.name == 'longitude' and not (119.5 <= v <= 122.5):
            raise ValueError('經度必須在台灣範圍內')
        return v

class EmergencyDepartment(BaseModel):
    available: bool
    hours: Optional[str] = None
    phone: Optional[str] = None

class Hospital(BaseModel):
    place_id: str
    name: str = Field(..., description="醫院名稱")
    address: str = Field(..., description="醫院地址")
    formatted_address: Optional[str] = None
    location: Location
    distance: int = Field(..., description="距離（公尺）")
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = Field(None, ge=1, le=5)
    user_ratings_total: Optional[int] = None
    emergency_department: Optional[EmergencyDepartment] = None
    nhia_contracted: Optional[bool] = None
    nhia_code: Optional[str] = None
    departments: Optional[List[str]] = None

class HospitalSearchRequest(BaseModel):
    location: Optional[Location] = None
    address: Optional[str] = None
    radius: int = Field(default=3000, ge=500, le=10000)
    include_emergency_only: bool = False
    max_results: int = Field(default=20, ge=1, le=50)
    use_ip_location: bool = False
```

### 3. Audit and Privacy Models
```python
class AuditLogEntry(BaseModel):
    request_id: str
    endpoint: str
    method: str
    status_code: int
    processing_time_ms: int
    emergency_triggered: bool = False
    location_rounded: Optional[Location] = None  # Rounded for privacy
    symptom_category: Optional[SymptomCategory] = None
    error_code: Optional[str] = None

    class Config:
        # Exclude sensitive fields from serialization
        fields = {
            'user_agent': {'write_only': True},
            'ip_address': {'write_only': True},
            'api_key': {'write_only': True}
        }

class PrivacySettings(BaseModel):
    pii_masking_enabled: bool = True
    audit_retention_days: int = 30
    symptom_anonymization: bool = True
    location_precision_meters: int = 100  # Round location to 100m
```

## Data Flow Patterns

### 1. Request Processing Flow
```
User Request → PII Masking → Validation → Business Logic → Cache Check → External API → Response Assembly → Audit Log
```

### 2. Caching Strategy
```
Request → Cache Hit? → Yes: Return Cached Data
                   → No: Fetch from Source → Cache Result → Return Data
```

### 3. NHIA Verification Flow
```
Google Places Result → Extract Hospital Name/Address → NHIA Registry Lookup → Fuzzy Match → Contract Status → Enhanced Result
```

## Data Privacy Implementation

### 1. PII Masking Functions
```python
import hashlib
import re
from typing import Optional

def mask_phone_number(text: str) -> str:
    """Mask phone numbers in text"""
    phone_pattern = r'(\+886|0)\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}'
    return re.sub(phone_pattern, '[電話號碼]', text)

def mask_id_number(text: str) -> str:
    """Mask Taiwan ID numbers"""
    id_pattern = r'[A-Z]\d{9}'
    return re.sub(id_pattern, '[身分證字號]', text)

def hash_sensitive_data(data: str) -> str:
    """Hash sensitive data for audit purposes"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()[:16]

def round_location(lat: float, lng: float, precision: int = 100) -> tuple:
    """Round location to specified precision (meters)"""
    # Convert precision to decimal degrees (approximate)
    degree_precision = precision / 111000  # 1 degree ≈ 111km
    return (
        round(lat / degree_precision) * degree_precision,
        round(lng / degree_precision) * degree_precision
    )
```

### 2. Audit Logging with Privacy
```python
def create_audit_log(
    request_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    processing_time: int,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    location: Optional[Location] = None,
    emergency_triggered: bool = False
) -> AuditLogEntry:
    """Create privacy-compliant audit log entry"""

    return AuditLogEntry(
        request_id=request_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        processing_time_ms=processing_time,
        user_agent_hash=hash_sensitive_data(user_agent) if user_agent else None,
        ip_address_hash=hash_sensitive_data(ip_address) if ip_address else None,
        location_rounded=round_location(location.latitude, location.longitude) if location else None,
        emergency_triggered=emergency_triggered
    )
```

## Data Validation and Quality

### 1. Taiwan-Specific Validation
```python
def validate_taiwan_address(address: str) -> bool:
    """Validate Taiwan address format"""
    taiwan_cities = [
        '台北市', '新北市', '桃園市', '台中市', '台南市', '高雄市',
        '基隆市', '新竹市', '嘉義市', '新竹縣', '苗栗縣', '彰化縣',
        '南投縣', '雲林縣', '嘉義縣', '屏東縣', '宜蘭縣', '花蓮縣',
        '台東縣', '澎湖縣', '金門縣', '連江縣'
    ]

    return any(city in address for city in taiwan_cities)

def validate_phone_number_tw(phone: str) -> bool:
    """Validate Taiwan phone number format"""
    patterns = [
        r'^\+886-\d{1,2}-\d{3,4}-\d{4}$',  # International format
        r'^0\d{1,2}-\d{3,4}-\d{4}$',       # Domestic format
        r'^\d{4}$'                         # Emergency numbers
    ]

    return any(re.match(pattern, phone) for pattern in patterns)
```

### 2. Data Quality Checks
```python
def validate_hospital_data(hospital: Hospital) -> List[str]:
    """Validate hospital data quality"""
    errors = []

    # Required fields
    if not hospital.name:
        errors.append("醫院名稱為必填欄位")

    if not hospital.address:
        errors.append("醫院地址為必填欄位")

    # Taiwan-specific validations
    if not validate_taiwan_address(hospital.address):
        errors.append("地址必須為台灣地址")

    if hospital.phone and not validate_phone_number_tw(hospital.phone):
        errors.append("電話號碼格式不正確")

    # Location bounds
    try:
        hospital.location  # Triggers Pydantic validation
    except ValueError as e:
        errors.append(f"座標驗證失敗: {e}")

    return errors
```

## Performance Optimization

### 1. Database Indexing Strategy
```sql
-- Optimized indexes for common queries
CREATE INDEX CONCURRENTLY idx_hospitals_location_emergency
ON nhia_hospitals USING GIST (
    ST_Point(location_lng, location_lat)
) WHERE has_emergency = true AND is_active = true;

CREATE INDEX CONCURRENTLY idx_audit_logs_performance
ON audit_logs (created_at DESC, endpoint, status_code)
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days';

-- Partial indexes for active records only
CREATE INDEX CONCURRENTLY idx_hospitals_active_name
ON nhia_hospitals (name_zh_tw)
WHERE is_active = true;
```

### 2. Cache Optimization
```python
# Cache warming strategy
async def warm_cache():
    """Pre-populate frequently accessed cache entries"""

    # Cache emergency contacts
    emergency_contacts = load_emergency_contacts()
    await cache.setex(
        "emergency:contacts:zh-tw",
        604800,  # 7 days
        json.dumps(emergency_contacts)
    )

    # Cache major hospital data
    major_hospitals = await get_major_hospitals()
    for hospital in major_hospitals:
        cache_key = f"nhia:hospital:{hospital.place_id}"
        await cache.setex(cache_key, 21600, json.dumps(hospital.dict()))
```

## Data Migration and Maintenance

### 1. NHIA Registry Updates
```python
async def update_nhia_registry():
    """Update NHIA hospital registry from official sources"""

    # Download latest registry from MOHW
    registry_data = await download_nhia_registry()

    # Validate and transform data
    hospitals = []
    for record in registry_data:
        hospital = transform_nhia_record(record)
        if validate_hospital_data(hospital):
            hospitals.append(hospital)

    # Bulk update database
    await bulk_upsert_hospitals(hospitals)

    # Clear related caches
    await cache.delete_pattern("nhia:hospital:*")
```

### 2. Data Cleanup and Retention
```python
async def cleanup_expired_data():
    """Clean up expired data according to retention policies"""

    # Remove expired audit logs (PDPA compliance)
    cutoff_date = datetime.now() - timedelta(days=30)
    await delete_audit_logs_before(cutoff_date)

    # Clean expired cache entries
    await cache.flushdb_expired()

    # Vacuum and analyze tables
    await vacuum_analyze_tables()
```

This data architecture ensures compliance with Taiwan's Personal Data Protection Act while providing efficient, localized medical guidance services with proper emergency protocol integration.