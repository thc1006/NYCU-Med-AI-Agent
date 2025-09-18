# FastAPI Medical Service Template
# Template for implementing medical AI services with Taiwan localization

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import httpx
import asyncio
from datetime import datetime
import logging
import uuid
import re
from dataclasses import dataclass

# Taiwan-specific constants
TAIWAN_CONFIG = {
    "language": "zh-TW",
    "region": "TW",
    "emergency_numbers": {
        "119": "消防局救護車",
        "110": "警察局",
        "112": "行動電話國際緊急號碼",
        "113": "保護專線",
        "165": "反詐騙諮詢專線"
    },
    "timezone": "Asia/Taipei"
}

# Medical safety constants
EMERGENCY_KEYWORDS = [
    "胸痛", "呼吸困難", "麻痺", "劇烈頭痛", "意識不清",
    "大量出血", "嚴重外傷", "中毒", "過敏反應", "心悸"
]

MEDICAL_DISCLAIMER = """
⚠️ 重要聲明：
本系統僅提供一般健康資訊參考，不應視為專業醫療建議、診斷或治療。
如有緊急醫療狀況，請立即撥打119或前往就近急診室。
任何醫療決定應諮詢合格醫療專業人員。
"""

# Base models
class BaseResponse(BaseModel):
    """Base response model with Taiwan compliance"""
    status: str = "success"
    locale: str = "zh-TW"
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    disclaimer: str = MEDICAL_DISCLAIMER
    emergency_numbers: Dict[str, str] = TAIWAN_CONFIG["emergency_numbers"]

class SymptomRequest(BaseModel):
    """Symptom analysis request with privacy protection"""
    symptom_text: str = Field(..., min_length=1, max_length=1000)
    user_location: Optional[Dict[str, float]] = None
    age_range: Optional[str] = None
    urgency_level: Optional[str] = None

    @validator('symptom_text')
    def validate_symptom_text(cls, v):
        # Remove potential PII patterns
        v = re.sub(r'\b\d{4}-\d{4}-\d{4}-\d{4}\b', '[身分證號碼已遮罩]', v)
        v = re.sub(r'\b09\d{8}\b', '[電話號碼已遮罩]', v)
        return v

class TriageResponse(BaseResponse):
    """Triage response with medical safety"""
    level: str  # emergency, urgent, routine, self-care
    advice: str
    next_steps: List[str]
    should_call_119: bool = False
    nearest_hospitals: Optional[List[Dict[str, Any]]] = None

class HospitalSearchRequest(BaseModel):
    """Hospital search with location"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    radius_km: int = Field(default=5, ge=1, le=50)
    hospital_type: Optional[str] = "全部"

class HospitalResponse(BaseResponse):
    """Hospital search response"""
    hospitals: List[Dict[str, Any]]
    search_location: Dict[str, float]
    total_found: int

# Privacy middleware
class PrivacyMiddleware:
    """PDPA compliant privacy protection"""

    def __init__(self, app: FastAPI):
        self.app = app

    async def __call__(self, request: Request, call_next):
        # Generate request ID for audit trail
        request.state.request_id = str(uuid.uuid4())

        # Log minimal required information only
        logging.info(f"Request {request.state.request_id}: {request.method} {request.url.path}")

        response = await call_next(request)

        # Add privacy headers
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Privacy-Policy"] = "PDPA-compliant"

        return response

# Medical safety service
class MedicalSafetyService:
    """Medical safety validation service"""

    @staticmethod
    def check_emergency_keywords(text: str) -> bool:
        """Check for emergency keywords in symptom text"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in EMERGENCY_KEYWORDS)

    @staticmethod
    def get_emergency_response() -> TriageResponse:
        """Generate emergency response"""
        return TriageResponse(
            level="emergency",
            advice="您描述的症狀可能需要緊急醫療處理，請立即撥打119或前往就近急診室。",
            next_steps=[
                "立即撥打119",
                "前往最近的急診室",
                "保持冷靜並準備好身分證件",
                "如有藥物過敏史，請告知醫護人員"
            ],
            should_call_119=True
        )

    @staticmethod
    def validate_medical_response(response: TriageResponse) -> TriageResponse:
        """Validate medical response for safety"""
        # Ensure no definitive medical diagnosis
        response.advice = response.advice.replace("診斷", "建議")
        response.advice = response.advice.replace("確診", "可能")

        # Ensure disclaimer is present
        if not response.disclaimer:
            response.disclaimer = MEDICAL_DISCLAIMER

        return response

# Taiwan localization service
class TaiwanLocalizationService:
    """Taiwan-specific localization service"""

    @staticmethod
    async def geocode_taiwan_address(address: str) -> Optional[Dict[str, float]]:
        """Geocode Taiwan address using Google Maps API"""
        async with httpx.AsyncClient() as client:
            params = {
                "address": address,
                "region": "TW",
                "language": "zh-TW",
                "key": "YOUR_GOOGLE_API_KEY"  # Should be from environment
            }

            try:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    if data["results"]:
                        location = data["results"][0]["geometry"]["location"]
                        return {"latitude": location["lat"], "longitude": location["lng"]}

            except Exception as e:
                logging.error(f"Geocoding failed: {e}")

        return None

    @staticmethod
    async def find_nearby_hospitals(lat: float, lng: float, radius_km: int = 5) -> List[Dict[str, Any]]:
        """Find nearby hospitals using Google Places API"""
        async with httpx.AsyncClient() as client:
            params = {
                "location": f"{lat},{lng}",
                "radius": radius_km * 1000,  # Convert to meters
                "type": "hospital",
                "language": "zh-TW",
                "region": "TW",
                "key": "YOUR_GOOGLE_API_KEY"  # Should be from environment
            }

            try:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    hospitals = []

                    for place in data.get("results", []):
                        hospital = {
                            "name": place.get("name"),
                            "address": place.get("vicinity"),
                            "rating": place.get("rating"),
                            "is_open": place.get("opening_hours", {}).get("open_now"),
                            "phone": place.get("formatted_phone_number"),
                            "location": place.get("geometry", {}).get("location")
                        }
                        hospitals.append(hospital)

                    return hospitals

            except Exception as e:
                logging.error(f"Hospital search failed: {e}")

        return []

# FastAPI application with medical safety
def create_medical_app() -> FastAPI:
    """Create FastAPI application with medical AI configuration"""

    app = FastAPI(
        title="Taiwan Medical AI Assistant",
        description="醫療AI助理 - 症狀評估與就近醫療院所查詢",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add privacy middleware
    app.add_middleware(PrivacyMiddleware)

    # Initialize services
    safety_service = MedicalSafetyService()
    localization_service = TaiwanLocalizationService()

    @app.get("/healthz", response_model=BaseResponse)
    async def health_check():
        """Health check endpoint"""
        return BaseResponse(status="ok")

    @app.get("/v1/meta/emergency", response_model=BaseResponse)
    async def get_emergency_info():
        """Get Taiwan emergency contact information"""
        return BaseResponse(
            emergency_numbers=TAIWAN_CONFIG["emergency_numbers"]
        )

    @app.post("/v1/triage", response_model=TriageResponse)
    async def symptom_triage(request: SymptomRequest):
        """Symptom triage with medical safety checks"""

        # Check for emergency keywords first
        if safety_service.check_emergency_keywords(request.symptom_text):
            return safety_service.get_emergency_response()

        # Basic triage logic (should be enhanced with actual AI/rules)
        response = TriageResponse(
            level="routine",
            advice="根據您的症狀描述，建議您觀察症狀變化。如症狀持續或惡化，請諮詢醫療專業人員。",
            next_steps=[
                "觀察症狀變化",
                "保持充足休息",
                "如症狀惡化，請就醫",
                "緊急狀況請撥打119"
            ]
        )

        # Apply safety validation
        response = safety_service.validate_medical_response(response)

        return response

    @app.post("/v1/hospitals/nearby", response_model=HospitalResponse)
    async def find_nearby_hospitals(request: HospitalSearchRequest):
        """Find nearby hospitals"""

        # Determine search location
        if request.latitude and request.longitude:
            search_location = {"latitude": request.latitude, "longitude": request.longitude}
        elif request.address:
            search_location = await localization_service.geocode_taiwan_address(request.address)
            if not search_location:
                raise HTTPException(status_code=400, detail="無法定位指定地址")
        else:
            raise HTTPException(status_code=400, detail="請提供座標或地址")

        # Search for hospitals
        hospitals = await localization_service.find_nearby_hospitals(
            search_location["latitude"],
            search_location["longitude"],
            request.radius_km
        )

        return HospitalResponse(
            hospitals=hospitals,
            search_location=search_location,
            total_found=len(hospitals)
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Custom HTTP exception handler with privacy protection"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", str(uuid.uuid4())),
                "locale": "zh-TW",
                "disclaimer": MEDICAL_DISCLAIMER,
                "emergency_numbers": TAIWAN_CONFIG["emergency_numbers"]
            }
        )

    return app

# Test utilities
class TestHelpers:
    """Test utilities for medical AI components"""

    @staticmethod
    def create_test_symptom_request(symptom: str) -> SymptomRequest:
        """Create test symptom request"""
        return SymptomRequest(symptom_text=symptom)

    @staticmethod
    def create_test_hospital_request(lat: float = 25.0330, lng: float = 121.5654) -> HospitalSearchRequest:
        """Create test hospital request (defaults to Taipei)"""
        return HospitalSearchRequest(latitude=lat, longitude=lng)

    @staticmethod
    def assert_medical_safety(response: TriageResponse):
        """Assert medical safety requirements"""
        assert response.disclaimer == MEDICAL_DISCLAIMER
        assert response.emergency_numbers == TAIWAN_CONFIG["emergency_numbers"]
        assert response.locale == "zh-TW"

        # Check for no definitive diagnosis
        advice_lower = response.advice.lower()
        dangerous_words = ["確診", "診斷為", "患有", "罹患"]
        for word in dangerous_words:
            assert word not in advice_lower, f"Medical response contains dangerous word: {word}"

    @staticmethod
    def assert_taiwan_compliance(response: BaseResponse):
        """Assert Taiwan compliance requirements"""
        assert response.locale == "zh-TW"
        assert "119" in response.emergency_numbers
        assert "110" in response.emergency_numbers
        assert "112" in response.emergency_numbers

# Example usage
if __name__ == "__main__":
    import uvicorn

    app = create_medical_app()
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)