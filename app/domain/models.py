"""
領域模型定義
包含症狀查詢、分級結果等核心資料結構
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator


class TriageLevel(str, Enum):
    """症狀分級等級"""
    EMERGENCY = "emergency"  # 緊急：需要立即撥打119
    URGENT = "urgent"  # 緊急：盡快就醫
    OUTPATIENT = "outpatient"  # 門診：安排門診就醫
    SELF_CARE = "self-care"  # 自我照護：可自行觀察


class SymptomQuery(BaseModel):
    """症狀查詢模型"""
    symptom_text: str
    age: Optional[int] = None
    gender: Optional[str] = None
    duration_hours: Optional[int] = None
    has_chronic_disease: bool = False
    medications: List[str] = []

    @validator('symptom_text')
    def validate_symptom_text(cls, v):
        # Allow empty string for testing
        if v is None:
            return ""
        return v.strip()

    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

    @validator('gender')
    def validate_gender(cls, v):
        if v and v.upper() not in ['M', 'F', 'O', None]:
            raise ValueError('Gender must be M, F, O, or None')
        return v.upper() if v else None


class TriageResult(BaseModel):
    """症狀分級結果模型"""
    level: TriageLevel
    advice: str
    detected_symptoms: List[str]
    next_steps: List[str]
    disclaimer: str
    emergency_numbers: Optional[List[str]] = None
    recommended_departments: Optional[List[str]] = None
    estimated_wait_time: Optional[str] = None
    confidence_score: Optional[float] = None

    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError('Confidence score must be between 0 and 1')
        return v


class EmergencySymptom(BaseModel):
    """緊急症狀定義"""
    keyword: str
    severity: int  # 1-10, 10 最嚴重
    category: str
    immediate_action: str
    related_conditions: List[str]


class MildSymptom(BaseModel):
    """輕微症狀定義"""
    keyword: str
    category: str
    home_care_advice: str
    observation_period_hours: int
    warning_signs: List[str]


class SymptomDatabase(BaseModel):
    """症狀資料庫"""
    emergency_symptoms: List[EmergencySymptom]
    mild_symptoms: List[MildSymptom]
    moderate_symptoms: List[Dict[str, Any]]
    last_updated: str


class TriageRequest(BaseModel):
    """分級請求模型（API用）"""
    symptom_text: str
    age: Optional[int] = None
    gender: Optional[str] = None
    duration_hours: Optional[int] = None
    has_chronic_disease: bool = False
    medications: List[str] = []
    include_nearby_hospitals: bool = False
    location: Optional[Dict[str, float]] = None

    class Config:
        schema_extra = {
            "example": {
                "symptom_text": "胸痛、呼吸困難",
                "age": 45,
                "gender": "M",
                "duration_hours": 2,
                "has_chronic_disease": False,
                "medications": [],
                "include_nearby_hospitals": True,
                "location": {"latitude": 25.0339, "longitude": 121.5645}
            }
        }


class TriageResponse(BaseModel):
    """分級回應模型（API用）"""
    triage_level: str
    advice: str
    detected_symptoms: List[str]
    next_steps: List[str]
    disclaimer: str
    emergency_numbers: List[str]
    recommended_departments: Optional[List[str]] = None
    estimated_wait_time: Optional[str] = None
    confidence_score: Optional[float] = None
    nearby_hospitals: Optional[List[Dict[str, Any]]] = None
    request_id: str
    timestamp: str
    locale: str = "zh-TW"

    class Config:
        schema_extra = {
            "example": {
                "triage_level": "emergency",
                "advice": "您的症狀屬於緊急狀況，請立即撥打119或前往最近的急診室。",
                "detected_symptoms": ["胸痛", "呼吸困難"],
                "next_steps": [
                    "立即撥打119",
                    "保持冷靜，坐下休息",
                    "解開緊身衣物",
                    "準備好健保卡和藥物清單"
                ],
                "disclaimer": "本系統僅供參考，不可取代專業醫療診斷。",
                "emergency_numbers": ["119", "110", "112"],
                "recommended_departments": ["急診", "心臟內科"],
                "confidence_score": 0.95,
                "request_id": "req_12345",
                "timestamp": "2024-01-01T12:00:00Z",
                "locale": "zh-TW"
            }
        }