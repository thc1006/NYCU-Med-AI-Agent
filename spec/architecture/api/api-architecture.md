# API Architecture - Taiwan Medical AI Agent

## API Design Principles

### 1. RESTful Design
- Resource-based URLs
- HTTP methods for operations
- Stateless interactions
- Standard HTTP status codes

### 2. Taiwan Localization
- All responses in Traditional Chinese (zh-TW)
- Taiwan-specific emergency numbers
- Local time zones and formats
- Cultural considerations in messaging

### 3. Safety & Compliance
- Medical disclaimers in all health-related responses
- Emergency protocol integration
- PDPA-compliant data handling
- Audit logging for all operations

### 4. Developer Experience
- OpenAPI/Swagger documentation
- Consistent error handling
- Clear request/response schemas
- Comprehensive examples

## API Structure

### Base URL Structure
```
Production:  https://api.taiwan-med-ai.com/v1
Staging:     https://staging-api.taiwan-med-ai.com/v1
Development: http://localhost:8000/v1
```

### API Versioning Strategy
- URL-based versioning: `/v1/`, `/v2/`
- Backward compatibility for one major version
- Deprecation notices with migration timeline
- Version-specific documentation

## Core API Endpoints

### 1. Health Check & Meta Information

#### `GET /healthz`
Basic health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-01-20T10:30:00+08:00",
  "version": "1.0.0",
  "environment": "production"
}
```

#### `GET /v1/meta/emergency`
Taiwan emergency contact information.

**Response:**
```json
{
  "emergencyNumbers": [
    {
      "number": "119",
      "description": "消防救護車",
      "category": "medical_emergency",
      "available24h": true
    },
    {
      "number": "110",
      "description": "警察局",
      "category": "police",
      "available24h": true
    },
    {
      "number": "112",
      "description": "行動電話國際緊急號碼",
      "category": "international_emergency",
      "available24h": true,
      "note": "無卡亦可撥打"
    },
    {
      "number": "113",
      "description": "婦幼保護專線",
      "category": "protection",
      "available24h": true
    },
    {
      "number": "165",
      "description": "反詐騙諮詢專線",
      "category": "fraud_prevention",
      "available24h": true
    }
  ],
  "updatedAt": "2024-01-20T10:30:00+08:00",
  "locale": "zh-TW"
}
```

### 2. Medical Triage Service

#### `POST /v1/triage`
Analyze symptoms and provide medical guidance.

**Request:**
```json
{
  "symptomText": "胸痛且呼吸困難",
  "patientAge": 45,
  "patientGender": "male",
  "preferences": {
    "includeEmergencyInfo": true,
    "includeSelfCareAdvice": true
  }
}
```

**Response (Emergency Case):**
```json
{
  "requestId": "triage_123456789",
  "level": "emergency",
  "severity": "critical",
  "advice": "您描述的胸痛合併呼吸困難屬於高度警訊症狀，請立即撥打119或前往就近急診室。",
  "nextSteps": [
    "立即撥打119",
    "前往最近的急診室",
    "保持冷靜，避免劇烈活動",
    "準備個人身分證件及健保卡"
  ],
  "emergencyContacts": ["119", "112"],
  "disclaimer": "本系統僅提供一般健康資訊參考，不能取代專業醫療診斷。如有緊急狀況，請立即撥打119或112。",
  "timestamp": "2024-01-20T10:30:00+08:00",
  "locale": "zh-TW"
}
```

**Response (Self-Care Case):**
```json
{
  "requestId": "triage_123456790",
  "level": "self_care",
  "severity": "mild",
  "advice": "感冒症狀通常可透過適當休息和自我照護改善。建議多休息、多喝水，並觀察症狀變化。",
  "nextSteps": [
    "充分休息，避免過度勞累",
    "多喝溫開水，保持身體水分",
    "如症狀持續3-5天未改善，建議就醫諮詢",
    "若出現高燒、呼吸困難等症狀，請立即就醫"
  ],
  "selfCareAdvice": [
    {
      "category": "rest",
      "advice": "每日睡眠8小時以上"
    },
    {
      "category": "hydration",
      "advice": "每日攝取2000-2500ml水分"
    },
    {
      "category": "monitoring",
      "advice": "每日監測體溫變化"
    }
  ],
  "warningSignsToSeekCare": [
    "持續高燒超過38.5°C",
    "呼吸困難或胸痛",
    "嚴重脫水症狀",
    "症狀惡化或持續超過一週"
  ],
  "emergencyContacts": ["119", "112"],
  "disclaimer": "本系統僅提供一般健康資訊參考，不能取代專業醫療診斷。如有緊急狀況，請立即撥打119或112。",
  "timestamp": "2024-01-20T10:30:00+08:00",
  "locale": "zh-TW"
}
```

### 3. Hospital Location Service

#### `GET /v1/hospitals/nearby`
Find nearby hospitals and medical facilities.

**Query Parameters:**
- `lat` (float): Latitude
- `lng` (float): Longitude
- `radius` (int): Search radius in meters (default: 3000, max: 10000)
- `address` (string): Address to geocode (alternative to lat/lng)
- `useIpLocation` (boolean): Use IP-based location detection (default: false)
- `includeEmergency` (boolean): Include emergency departments only (default: false)
- `maxResults` (int): Maximum results to return (default: 20, max: 50)

**Example Request:**
```
GET /v1/hospitals/nearby?lat=25.0339&lng=121.5645&radius=5000&includeEmergency=true
```

**Response:**
```json
{
  "requestId": "hospital_search_123456",
  "searchCriteria": {
    "location": {
      "latitude": 25.0339,
      "longitude": 121.5645
    },
    "radius": 5000,
    "includeEmergencyOnly": true
  },
  "results": [
    {
      "placeId": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "name": "臺大醫院",
      "address": "台北市中正區中山南路7號",
      "formattedAddress": "100台北市中正區中山南路7號",
      "location": {
        "latitude": 25.0408,
        "longitude": 121.5198
      },
      "distance": 820,
      "phone": "+886-2-2312-3456",
      "website": "https://www.ntuh.gov.tw",
      "rating": 4.2,
      "userRatingsTotal": 1234,
      "emergencyDepartment": {
        "available": true,
        "hours": "24小時",
        "phone": "+886-2-2312-3456"
      },
      "nhiaContracted": true,
      "nhiaCode": "0501140010",
      "departments": [
        "急診醫學科",
        "內科",
        "外科",
        "婦產科",
        "小兒科"
      ],
      "openingHours": {
        "periods": [
          {
            "open": {
              "day": 0,
              "time": "0000"
            },
            "close": {
              "day": 0,
              "time": "2359"
            }
          }
        ],
        "weekdayText": [
          "星期一: 24 小時營業",
          "星期二: 24 小時營業",
          "星期三: 24 小時營業",
          "星期四: 24 小時營業",
          "星期五: 24 小時營業",
          "星期六: 24 小時營業",
          "星期日: 24 小時營業"
        ]
      }
    }
  ],
  "emergencyContacts": ["119", "112"],
  "disclaimer": "醫院資訊僅供參考，實際服務時間與科別請事先致電確認。緊急狀況請直接撥打119。",
  "timestamp": "2024-01-20T10:30:00+08:00",
  "locale": "zh-TW"
}
```

### 4. Geocoding Service

#### `POST /v1/geocoding/address`
Convert address to coordinates.

**Request:**
```json
{
  "address": "台北市信義區市府路1號",
  "language": "zh-TW",
  "region": "TW"
}
```

**Response:**
```json
{
  "requestId": "geocoding_123456",
  "results": [
    {
      "formattedAddress": "110台北市信義區市府路1號",
      "location": {
        "latitude": 25.0377,
        "longitude": 121.5645
      },
      "locationType": "ROOFTOP",
      "types": ["street_address"],
      "addressComponents": [
        {
          "longName": "1號",
          "shortName": "1號",
          "types": ["street_number"]
        },
        {
          "longName": "市府路",
          "shortName": "市府路",
          "types": ["route"]
        },
        {
          "longName": "信義區",
          "shortName": "信義區",
          "types": ["administrative_area_level_3"]
        },
        {
          "longName": "台北市",
          "shortName": "台北市",
          "types": ["administrative_area_level_1"]
        },
        {
          "longName": "台灣",
          "shortName": "TW",
          "types": ["country", "political"]
        },
        {
          "longName": "110",
          "shortName": "110",
          "types": ["postal_code"]
        }
      ]
    }
  ],
  "status": "OK",
  "timestamp": "2024-01-20T10:30:00+08:00",
  "locale": "zh-TW"
}
```

## Error Handling

### Standard Error Response Format
```json
{
  "error": {
    "code": "INVALID_LOCATION",
    "message": "無法識別提供的地址或座標",
    "details": "地址格式不正確或座標超出台灣範圍",
    "timestamp": "2024-01-20T10:30:00+08:00",
    "requestId": "req_123456789",
    "suggestion": "請提供完整的台灣地址或有效的經緯度座標"
  }
}
```

### Error Codes

#### Client Errors (4xx)
- `INVALID_REQUEST` (400): 請求格式錯誤
- `AUTHENTICATION_FAILED` (401): API金鑰無效或遺失
- `ACCESS_DENIED` (403): 存取權限不足
- `RESOURCE_NOT_FOUND` (404): 資源不存在
- `METHOD_NOT_ALLOWED` (405): HTTP方法不被允許
- `VALIDATION_ERROR` (422): 請求資料驗證失敗
- `RATE_LIMIT_EXCEEDED` (429): 請求頻率超過限制

#### Server Errors (5xx)
- `INTERNAL_ERROR` (500): 內部伺服器錯誤
- `SERVICE_UNAVAILABLE` (503): 服務暫時不可用
- `GATEWAY_TIMEOUT` (504): 外部服務連線逾時

#### Medical-Specific Errors
- `EMERGENCY_PROTOCOL_TRIGGERED`: 緊急狀況觸發，返回急救指引
- `MEDICAL_DISCLAIMER_REQUIRED`: 醫療免責聲明必須包含在回應中
- `SAFETY_CHECK_FAILED`: 安全檢查失敗，無法提供建議

#### Location-Specific Errors
- `INVALID_LOCATION`: 無效的地理位置
- `GEOCODING_FAILED`: 地址解析失敗
- `OUTSIDE_TAIWAN`: 座標位於台灣境外
- `IP_LOCATION_UNAVAILABLE`: IP定位服務不可用

## Rate Limiting

### Rate Limit Headers
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642669800
X-RateLimit-Retry-After: 60
```

### Rate Limit Tiers
- **Free Tier**: 100 requests/hour
- **Basic Tier**: 1,000 requests/hour
- **Premium Tier**: 10,000 requests/hour
- **Enterprise**: Custom limits

## Authentication

### API Key Authentication
```http
Authorization: Bearer your-api-key-here
X-API-Key: your-api-key-here
```

### Request Headers
```http
Content-Type: application/json
Accept: application/json
Accept-Language: zh-TW
X-Request-ID: client-generated-uuid
User-Agent: YourApp/1.0.0
```

## API Versioning & Lifecycle

### Version Support Policy
- Current version: `v1` (fully supported)
- Previous version: `v0` (deprecated, limited support)
- Future version: `v2` (planned)

### Breaking Changes
- New major version for breaking changes
- 6-month deprecation notice
- Migration guides provided
- Parallel version support during transition

### Non-Breaking Changes
- New optional fields
- New endpoints
- Enhanced functionality
- Bug fixes and improvements

## Security Considerations

### Data Privacy (PDPA Compliance)
- No storage of personal medical information
- PII masking in logs and responses
- User consent tracking
- Data minimization principles

### Input Validation
- Strict schema validation
- SQL injection prevention
- XSS protection
- Input sanitization

### Output Security
- Medical disclaimer enforcement
- Emergency protocol validation
- Response sanitization
- Safe error messages

## Performance Characteristics

### Response Time Targets
- Health check: < 50ms
- Triage analysis: < 500ms
- Hospital search: < 1000ms
- Geocoding: < 800ms

### Caching Strategy
- Geocoding results: 24 hours
- Hospital data: 1 hour
- Emergency numbers: 7 days
- Configuration: 1 hour

### Monitoring Metrics
- Request rate and response time
- Error rates by endpoint
- External API dependency health
- Cache hit rates
- Medical safety triggers