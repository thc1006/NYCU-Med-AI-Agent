"""
Health Information Models Extension
Extended Pydantic models for health information API responses
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


# Health Information Models

class HealthTopic(BaseModel):
    """健康主題模型"""
    id: str
    title: str
    summary: str
    url: str
    category: str
    priority: int
    last_updated: Optional[str] = None
    keywords: Optional[List[str]] = None
    content_points: Optional[List[str]] = None


class HealthResource(BaseModel):
    """健康資源模型"""
    id: str
    title: str
    description: str
    url: str
    type: str
    language: str
    category: str
    contact: Optional[Dict[str, str]] = None
    services: Optional[List[str]] = None


class VaccineInfo(BaseModel):
    """疫苗資訊模型"""
    name: str
    type: str
    dose: int
    required: bool
    route: Optional[str] = None
    site: Optional[str] = None
    notes: Optional[str] = None


class VaccinationSchedule(BaseModel):
    """疫苗接種時程模型"""
    age: str
    age_months: Optional[int] = None
    vaccines: List[VaccineInfo]
    notes: str
    location: Optional[str] = None


class VaccinationRecommendation(BaseModel):
    """疫苗接種建議模型"""
    vaccine: str
    type: str
    frequency: str
    target_group: str
    notes: str
    priority: str


class VaccinationInfo(BaseModel):
    """疫苗接種資訊模型"""
    title: str
    description: str
    schedule: Optional[List[VaccinationSchedule]] = None
    recommendations: Optional[List[VaccinationRecommendation]] = None
    source_url: str
    last_updated: str


class InsuranceCoverage(BaseModel):
    """健保給付項目模型"""
    name: str
    description: str
    included: bool


class InsuranceCopayment(BaseModel):
    """健保部分負擔模型"""
    description: str
    amount: str
    details: str


class InsuranceBasicInfo(BaseModel):
    """健保基本資訊模型"""
    title: str
    description: str
    coverage: Dict[str, InsuranceCoverage]
    copayment: Dict[str, InsuranceCopayment]


class InsuranceService(BaseModel):
    """健保服務模型"""
    id: str
    name: str
    description: str
    url: str
    contact: str
    online_service: bool


class EmergencyContact(BaseModel):
    """緊急聯絡電話模型"""
    number: str
    description: str


class InsuranceContact(BaseModel):
    """健保聯絡資訊模型"""
    number: str
    description: str
    hours: str


class InsuranceContacts(BaseModel):
    """健保聯絡方式模型"""
    nhi_hotline: InsuranceContact
    emergency_numbers: List[EmergencyContact]


class InsuranceInfo(BaseModel):
    """健保資訊模型"""
    basic_info: InsuranceBasicInfo
    services: List[InsuranceService]
    contacts: InsuranceContacts


# API Response Models

class HealthTopicsResponse(BaseModel):
    """健康主題回應模型"""
    topics: List[HealthTopic]
    total: int
    language: str = "zh-TW"
    last_updated: str


class HealthResourcesResponse(BaseModel):
    """健康資源回應模型"""
    resources: List[HealthResource]
    total: int
    language: str = "zh-TW"
    categories: List[str]


class VaccinationsResponse(BaseModel):
    """疫苗接種回應模型"""
    vaccinations: Dict[str, VaccinationInfo]
    language: str = "zh-TW"
    disclaimer: str


class InsuranceResponse(BaseModel):
    """健保資訊回應模型"""
    insurance: InsuranceInfo
    language: str = "zh-TW"
    last_updated: str