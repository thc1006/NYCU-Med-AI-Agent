"""
領域層套件
包含核心業務邏輯、模型和規則
"""

from .models import (
    TriageLevel,
    SymptomQuery,
    TriageResult,
    TriageRequest,
    TriageResponse,
    EmergencySymptom,
    MildSymptom
)
from .triage import rule_triage, combine_with_llm
from .rules_tw import (
    analyze_symptoms,
    get_emergency_keywords,
    get_mild_keywords,
    get_moderate_keywords,
    get_disclaimer,
    get_emergency_numbers
)

__all__ = [
    "TriageLevel",
    "SymptomQuery",
    "TriageResult",
    "TriageRequest",
    "TriageResponse",
    "EmergencySymptom",
    "MildSymptom",
    "rule_triage",
    "combine_with_llm",
    "analyze_symptoms",
    "get_emergency_keywords",
    "get_mild_keywords",
    "get_moderate_keywords",
    "get_disclaimer",
    "get_emergency_numbers"
]