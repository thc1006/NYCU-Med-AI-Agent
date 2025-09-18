# FastAPI Medical Patterns
# Best practices and patterns for medical AI implementation with Taiwan compliance

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import httpx
import logging
import uuid
import re
from datetime import datetime
import json

# Taiwan Medical AI Configuration
class TaiwanMedicalConfig:
    """Configuration for Taiwan medical AI compliance"""

    # Language and localization
    LANGUAGE = "zh-TW"
    REGION = "TW"
    TIMEZONE = "Asia/Taipei"

    # Emergency contact information
    EMERGENCY_NUMBERS = {
        "119": "消防局救護車",
        "110": "警察局",
        "112": "行動電話國際緊急號碼（無卡可撥）",
        "113": "保護專線（婦幼、老人、身心障礙）",
        "165": "反詐騙諮詢專線"
    }

    # Medical safety keywords
    EMERGENCY_KEYWORDS = [
        "胸痛", "胸悶", "呼吸困難", "呼吸急促", "氣喘",
        "意識不清", "昏迷", "暈倒", "抽搐", "癲癇",
        "劇烈頭痛", "突然頭痛", "頭部外傷",
        "嚴重出血", "大量出血", "吐血", "便血",
        "嚴重腹痛", "劇烈腹痛",
        "嚴重外傷", "骨折", "燒燙傷",
        "中毒", "誤食", "過敏反應", "休克",
        "心悸", "心律不整", "胸痛冒冷汗"
    ]

    # Privacy protection patterns
    PII_PATTERNS = {
        "taiwan_id": r"\b[A-Z][12]\d{8}\b",  # Taiwan ID format
        "phone": r"\b09\d{8}\b",  # Taiwan mobile phone
        "landline": r"\b0\d{1,2}-?\d{6,8}\b",  # Taiwan landline
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    }

    # Medical disclaimer
    MEDICAL_DISCLAIMER = """
⚠️ 重要醫療聲明：
• 本系統提供之資訊僅供參考，不可取代專業醫療建議、診斷或治療
• 如有緊急醫療狀況，請立即撥打119或前往就近急診室
• 任何醫療決定應諮詢合格醫療專業人員
• 本系統不提供醫療診斷，僅提供一般健康資訊參考
• 使用本系統即表示同意上述聲明
"""

# Base Models for Medical AI
class MedicalBaseModel(BaseModel):
    """Base model with medical safety and Taiwan compliance"""

    class Config:
        # Ensure proper JSON encoding for Traditional Chinese
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('*', pre=True, allow_reuse=True)
    def sanitize_input(cls, v):
        """Sanitize input to remove PII patterns"""
        if isinstance(v, str):
            # Mask Taiwan ID numbers
            v = re.sub(TaiwanMedicalConfig.PII_PATTERNS["taiwan_id"], "[身分證號已遮罩]", v)
            # Mask phone numbers
            v = re.sub(TaiwanMedicalConfig.PII_PATTERNS["phone"], "[電話號碼已遮罩]", v)
            v = re.sub(TaiwanMedicalConfig.PII_PATTERNS["landline"], "[電話號碼已遮罩]", v)
            # Mask email addresses
            v = re.sub(TaiwanMedicalConfig.PII_PATTERNS["email"], "[電子郵件已遮罩]", v)
        return v

class MedicalResponse(MedicalBaseModel):
    """Base response model for medical AI endpoints"""

    status: str = "success"
    locale: str = TaiwanMedicalConfig.LANGUAGE
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    disclaimer: str = TaiwanMedicalConfig.MEDICAL_DISCLAIMER
    emergency_numbers: Dict[str, str] = TaiwanMedicalConfig.EMERGENCY_NUMBERS

class EmergencyResponse(MedicalResponse):
    """Emergency response with immediate action guidance"""

    level: str = "emergency"
    immediate_action: str = "請立即撥打119或前往就近急診室"
    should_call_119: bool = True
    next_steps: List[str] = [
        "立即撥打119救護車",
        "保持冷靜，準備身分證件",
        "記錄症狀發生時間",
        "如有藥物過敏史，請告知醫護人員"
    ]

# Medical Safety Services
class MedicalSafetyValidator:
    """Medical safety validation service"""

    @staticmethod
    def validate_emergency_keywords(text: str) -> bool:
        """Check if text contains emergency keywords"""
        text_normalized = text.lower().strip()
        return any(keyword in text_normalized for keyword in TaiwanMedicalConfig.EMERGENCY_KEYWORDS)

    @staticmethod
    def validate_medical_response(response_text: str) -> Dict[str, Any]:
        """Validate medical response for safety compliance"""
        violations = []

        # Check for definitive medical diagnosis language
        dangerous_patterns = [
            r"你患有|您患有",
            r"診斷為|確診為",
            r"肯定是|一定是",
            r"你的病是|您的疾病是"
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                violations.append(f"Contains definitive diagnosis language: {pattern}")

        return {
            "is_safe": len(violations) == 0,
            "violations": violations,
            "contains_disclaimer": "專業醫療" in response_text,
            "contains_emergency_guidance": "119" in response_text
        }

    @staticmethod
    def generate_safe_medical_response(symptom_assessment: str, level: str = "routine") -> str:
        """Generate medically safe response text"""

        if level == "emergency":
            return "根據您描述的症狀，建議您立即尋求緊急醫療協助。請撥打119或前往就近急診室。"

        # Use non-diagnostic language
        safe_phrases = [
            "根據您的描述，建議您",
            "您可能需要考慮",
            "建議您觀察症狀變化",
            "如症狀持續或惡化，請"
        ]

        # Always include disclaimer reminder
        response = f"{symptom_assessment} 此建議僅供參考，如有疑慮請諮詢醫療專業人員。"

        return response

class TaiwanComplianceValidator:
    """Taiwan compliance validation service"""

    @staticmethod
    def validate_language_compliance(text: str) -> bool:
        """Validate Traditional Chinese language usage"""
        # Check for simplified Chinese characters that shouldn't be used
        simplified_chars = ["医", "疗", "症", "诊", "药"]  # Common simplified chars
        return not any(char in text for char in simplified_chars)

    @staticmethod
    def validate_emergency_numbers(config: Dict[str, Any]) -> bool:
        """Validate Taiwan emergency numbers are present"""
        required_numbers = ["119", "110", "112"]
        return all(num in config.get("emergency_numbers", {}) for num in required_numbers)

    @staticmethod
    def validate_pdpa_compliance(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate PDPA compliance for request data"""
        pii_found = []

        for field, value in request_data.items():
            if isinstance(value, str):
                for pii_type, pattern in TaiwanMedicalConfig.PII_PATTERNS.items():
                    if re.search(pattern, value):
                        pii_found.append(f"{pii_type} in {field}")

        return {
            "is_compliant": len(pii_found) == 0,
            "pii_detected": pii_found,
            "recommendation": "Remove or mask PII before processing" if pii_found else "Compliant"
        }

# FastAPI Medical Middleware
class MedicalSafetyMiddleware:
    """Middleware for medical safety and compliance"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.safety_validator = MedicalSafetyValidator()
        self.compliance_validator = TaiwanComplianceValidator()

    async def __call__(self, request: Request, call_next):
        # Generate request ID for audit trail
        request.state.request_id = str(uuid.uuid4())
        request.state.start_time = datetime.now()

        # Log request (minimal PII exposure)
        self._log_request_minimal(request)

        try:
            response = await call_next(request)

            # Add compliance headers
            response.headers["X-Request-ID"] = request.state.request_id
            response.headers["X-Medical-Safety"] = "validated"
            response.headers["X-Taiwan-Compliance"] = "validated"
            response.headers["X-PDPA-Compliant"] = "true"

            # Log response (minimal data)
            self._log_response_minimal(request, response)

            return response

        except Exception as e:
            # Log error without exposing sensitive data
            logging.error(f"Request {request.state.request_id} failed: {type(e).__name__}")
            raise

    def _log_request_minimal(self, request: Request):
        """Log minimal request information for audit"""
        log_data = {
            "request_id": request.state.request_id,
            "method": request.method,
            "path": request.url.path,
            "timestamp": request.state.start_time.isoformat(),
            "user_agent": request.headers.get("user-agent", "unknown")[:100],  # Truncate
            "ip_hash": self._hash_ip(request.client.host if request.client else "unknown")
        }

        logging.info(f"Medical API Request: {json.dumps(log_data, ensure_ascii=False)}")

    def _log_response_minimal(self, request: Request, response: Response):
        """Log minimal response information for audit"""
        duration = (datetime.now() - request.state.start_time).total_seconds()

        log_data = {
            "request_id": request.state.request_id,
            "status_code": response.status_code,
            "duration_seconds": round(duration, 3),
            "response_size": len(response.body) if hasattr(response, 'body') else 0
        }

        logging.info(f"Medical API Response: {json.dumps(log_data, ensure_ascii=False)}")

    def _hash_ip(self, ip: str) -> str:
        """Hash IP address for privacy"""
        import hashlib
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

# Medical AI Service Patterns
class MedicalTriageService:
    """Medical triage service with safety validation"""

    def __init__(self):
        self.safety_validator = MedicalSafetyValidator()
        self.compliance_validator = TaiwanComplianceValidator()

    async def assess_symptoms(self, symptom_text: str, context: Dict[str, Any] = None) -> MedicalResponse:
        """Assess symptoms with medical safety checks"""

        # First check for emergency keywords
        if self.safety_validator.validate_emergency_keywords(symptom_text):
            return EmergencyResponse(
                advice="根據您描述的症狀，這可能是緊急醫療狀況",
                recommendation="請立即撥打119或前往就近急診室"
            )

        # Perform routine triage
        assessment = await self._perform_routine_triage(symptom_text, context)

        # Validate response safety
        safety_check = self.safety_validator.validate_medical_response(assessment.get("advice", ""))

        if not safety_check["is_safe"]:
            # Regenerate with safer language
            assessment["advice"] = self.safety_validator.generate_safe_medical_response(
                assessment.get("advice", ""), "routine"
            )

        return MedicalResponse(
            level=assessment.get("level", "routine"),
            advice=assessment["advice"],
            next_steps=assessment.get("next_steps", []),
            confidence=assessment.get("confidence", 0.5)
        )

    async def _perform_routine_triage(self, symptom_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform routine triage assessment"""

        # Basic symptom analysis (placeholder for actual ML/rule engine)
        severity_keywords = {
            "mild": ["輕微", "一點", "少許", "偶爾"],
            "moderate": ["中等", "明顯", "持續", "經常"],
            "severe": ["嚴重", "劇烈", "非常", "無法"]
        }

        symptom_lower = symptom_text.lower()
        severity = "mild"

        for level, keywords in severity_keywords.items():
            if any(keyword in symptom_lower for keyword in keywords):
                severity = level
                break

        # Generate appropriate advice
        if severity == "severe":
            advice = "根據您的症狀描述，建議您盡快就醫檢查"
            next_steps = ["就近就醫", "準備相關病歷", "如症狀加劇請立即就醫"]
            level = "urgent"
        elif severity == "moderate":
            advice = "建議您觀察症狀變化，如持續或惡化請就醫"
            next_steps = ["觀察症狀變化", "充分休息", "如無改善請就醫"]
            level = "routine"
        else:
            advice = "建議您多休息並觀察症狀，如有疑慮可諮詢醫療專業人員"
            next_steps = ["充分休息", "多喝水", "觀察症狀變化"]
            level = "self-care"

        return {
            "level": level,
            "advice": advice,
            "next_steps": next_steps,
            "confidence": 0.7,
            "severity": severity
        }

class TaiwanHospitalService:
    """Taiwan hospital search service with localization"""

    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.compliance_validator = TaiwanComplianceValidator()

    async def find_nearby_hospitals(self, lat: float, lng: float, radius_km: int = 5) -> Dict[str, Any]:
        """Find nearby hospitals using Google Places API with Taiwan settings"""

        async with httpx.AsyncClient() as client:
            try:
                # Use Taiwan-specific parameters
                params = {
                    "location": f"{lat},{lng}",
                    "radius": radius_km * 1000,  # Convert to meters
                    "type": "hospital",
                    "language": TaiwanMedicalConfig.LANGUAGE,
                    "region": TaiwanMedicalConfig.REGION,
                    "key": self.google_api_key
                }

                response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params=params,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    hospitals = self._process_hospital_data(data.get("results", []))

                    return {
                        "hospitals": hospitals,
                        "search_location": {"latitude": lat, "longitude": lng},
                        "total_found": len(hospitals),
                        "search_radius_km": radius_km
                    }
                else:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail="醫院搜尋服務暫時無法使用，請稍後再試"
                    )

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=408,
                    detail="搜尋請求逾時，請檢查網路連線或稍後再試"
                )
            except Exception as e:
                logging.error(f"Hospital search failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="醫院搜尋服務發生錯誤，請稍後再試"
                )

    def _process_hospital_data(self, places_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process and normalize hospital data"""

        hospitals = []

        for place in places_data:
            hospital = {
                "name": place.get("name", "未知醫院"),
                "address": place.get("vicinity", "地址未提供"),
                "rating": place.get("rating"),
                "total_ratings": place.get("user_ratings_total"),
                "is_open_now": place.get("opening_hours", {}).get("open_now"),
                "phone": place.get("formatted_phone_number"),
                "location": place.get("geometry", {}).get("location"),
                "types": place.get("types", []),
                "place_id": place.get("place_id")
            }

            # Add Taiwan-specific enhancements
            hospital["emergency_available"] = self._check_emergency_services(place)
            hospital["health_insurance_accepted"] = True  # Assume NHI coverage in Taiwan

            hospitals.append(hospital)

        # Sort by rating and distance
        hospitals.sort(key=lambda x: (x.get("rating", 0), x.get("total_ratings", 0)), reverse=True)

        return hospitals

    def _check_emergency_services(self, place_data: Dict[str, Any]) -> bool:
        """Check if hospital provides emergency services"""

        # Look for emergency indicators in types or name
        emergency_indicators = ["emergency", "急診", "emergency_room"]

        name = place_data.get("name", "").lower()
        types = place_data.get("types", [])

        return any(indicator in name for indicator in emergency_indicators) or \
               "hospital" in types

# FastAPI Application Factory
def create_medical_app(config: Dict[str, Any] = None) -> FastAPI:
    """Create FastAPI application with medical safety and Taiwan compliance"""

    app = FastAPI(
        title="Taiwan Medical AI Assistant",
        description="醫療AI助理 - 提供症狀評估與就近醫療院所查詢服務",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware with Taiwan-specific settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("allowed_origins", ["*"]) if config else ["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Add medical safety middleware
    app.add_middleware(MedicalSafetyMiddleware)

    # Initialize services
    triage_service = MedicalTriageService()
    hospital_service = TaiwanHospitalService(
        google_api_key=config.get("google_api_key") if config else "demo_key"
    )

    # Health check endpoint
    @app.get("/healthz", response_model=MedicalResponse)
    async def health_check():
        """Health check with Taiwan compliance verification"""
        return MedicalResponse(
            status="healthy",
            message="Taiwan Medical AI Assistant 運作正常"
        )

    # Emergency information endpoint
    @app.get("/v1/meta/emergency", response_model=MedicalResponse)
    async def get_emergency_info():
        """Get Taiwan emergency contact information"""
        return MedicalResponse(
            emergency_contact_info={
                "primary_emergency": "119",
                "police": "110",
                "international_emergency": "112",
                "protection_hotline": "113",
                "anti_fraud": "165"
            },
            usage_instructions="緊急醫療狀況請撥打119，一般諮詢可參考其他專線"
        )

    # Symptom triage endpoint
    @app.post("/v1/triage", response_model=Union[MedicalResponse, EmergencyResponse])
    async def symptom_triage(request: Dict[str, Any]):
        """Symptom triage with medical safety validation"""

        symptom_text = request.get("symptom_text", "").strip()

        if not symptom_text:
            raise HTTPException(
                status_code=400,
                detail="請提供症狀描述"
            )

        if len(symptom_text) > 1000:
            raise HTTPException(
                status_code=400,
                detail="症狀描述過長，請控制在1000字以內"
            )

        # Perform triage assessment
        result = await triage_service.assess_symptoms(
            symptom_text=symptom_text,
            context=request.get("context", {})
        )

        return result

    # Hospital search endpoint
    @app.post("/v1/hospitals/nearby", response_model=MedicalResponse)
    async def find_nearby_hospitals(request: Dict[str, Any]):
        """Find nearby hospitals with Taiwan localization"""

        lat = request.get("latitude")
        lng = request.get("longitude")
        radius_km = request.get("radius_km", 5)

        if not lat or not lng:
            raise HTTPException(
                status_code=400,
                detail="請提供經緯度座標"
            )

        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            raise HTTPException(
                status_code=400,
                detail="經緯度座標格式不正確"
            )

        if not (1 <= radius_km <= 50):
            raise HTTPException(
                status_code=400,
                detail="搜尋半徑應在1-50公里範圍內"
            )

        # Find hospitals
        hospital_data = await hospital_service.find_nearby_hospitals(lat, lng, radius_km)

        return MedicalResponse(
            **hospital_data,
            search_summary=f"在 {radius_km} 公里範圍內找到 {hospital_data['total_found']} 家醫療院所"
        )

    # Error handlers with medical safety
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom HTTP exception handler with medical safety"""

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "locale": TaiwanMedicalConfig.LANGUAGE,
                "emergency_guidance": "如遇緊急狀況請撥打119",
                "disclaimer": TaiwanMedicalConfig.MEDICAL_DISCLAIMER,
                "emergency_numbers": TaiwanMedicalConfig.EMERGENCY_NUMBERS
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """General exception handler with privacy protection"""

        # Log error without exposing sensitive information
        logging.error(f"Unhandled error in request {getattr(request.state, 'request_id', 'unknown')}: {type(exc).__name__}")

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "系統暫時無法處理您的請求，請稍後再試",
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "locale": TaiwanMedicalConfig.LANGUAGE,
                "emergency_guidance": "如遇緊急狀況請撥打119",
                "disclaimer": TaiwanMedicalConfig.MEDICAL_DISCLAIMER,
                "emergency_numbers": TaiwanMedicalConfig.EMERGENCY_NUMBERS
            }
        )

    return app

# Example usage and testing
if __name__ == "__main__":
    import uvicorn

    # Configuration
    config = {
        "google_api_key": "your_google_api_key_here",
        "allowed_origins": ["http://localhost:3000", "https://yourdomain.com"]
    }

    # Create app
    app = create_medical_app(config)

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )