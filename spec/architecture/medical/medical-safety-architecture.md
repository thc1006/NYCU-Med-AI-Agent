# Medical Safety & Emergency Protocol Architecture

## Medical Safety Overview

The Taiwan Medical AI Agent implements a comprehensive medical safety architecture designed to prioritize patient safety, ensure appropriate emergency responses, and maintain the highest standards of medical guidance while strictly adhering to non-diagnostic principles.

## Core Medical Safety Principles

### 1. Safety-First Design
- **Emergency Override**: Critical symptoms trigger immediate emergency protocols
- **Fail-Safe Defaults**: System defaults to emergency guidance when uncertain
- **Non-Diagnostic Approach**: System provides guidance, never diagnoses
- **Professional Referral**: All responses direct to qualified medical professionals

### 2. Taiwan Medical Context
- **Local Emergency Services**: Integration with Taiwan's 119/112 emergency systems
- **Healthcare System Awareness**: Understanding of Taiwan's National Health Insurance system
- **Cultural Sensitivity**: Appropriate communication styles for Taiwan medical culture
- **Regulatory Compliance**: Adherence to Taiwan medical practice standards

### 3. Graduated Response System
- **Emergency**: Life-threatening symptoms requiring immediate medical attention
- **Urgent**: Serious symptoms requiring prompt medical evaluation
- **Routine**: Symptoms that can be evaluated during regular hours
- **Self-Care**: Minor symptoms manageable with self-care and monitoring

## Emergency Detection Architecture

### 1. Critical Symptom Detection Engine
```python
from typing import List, Dict, Optional, Tuple
from enum import Enum
import re
from dataclasses import dataclass

class EmergencyLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"

class SymptomCategory(Enum):
    CARDIOVASCULAR = "cardiovascular"
    RESPIRATORY = "respiratory"
    NEUROLOGICAL = "neurological"
    TRAUMA = "trauma"
    PSYCHIATRIC = "psychiatric"
    GASTROINTESTINAL = "gastrointestinal"
    OTHER = "other"

@dataclass
class EmergencyKeyword:
    term: str
    category: SymptomCategory
    level: EmergencyLevel
    context_required: bool = False
    age_specific: Optional[Tuple[int, int]] = None  # (min_age, max_age)
    additional_indicators: Optional[List[str]] = None

class EmergencyDetectionEngine:
    def __init__(self):
        self.emergency_keywords = self._load_emergency_keywords()
        self.context_patterns = self._load_context_patterns()
        self.exclusion_patterns = self._load_exclusion_patterns()

    def _load_emergency_keywords(self) -> List[EmergencyKeyword]:
        """Load Taiwan-specific emergency medical keywords"""
        return [
            # Critical Cardiovascular
            EmergencyKeyword("胸痛", SymptomCategory.CARDIOVASCULAR, EmergencyLevel.CRITICAL),
            EmergencyKeyword("心肌梗塞", SymptomCategory.CARDIOVASCULAR, EmergencyLevel.CRITICAL),
            EmergencyKeyword("心臟病發作", SymptomCategory.CARDIOVASCULAR, EmergencyLevel.CRITICAL),
            EmergencyKeyword("胸悶", SymptomCategory.CARDIOVASCULAR, EmergencyLevel.HIGH,
                           context_required=True, additional_indicators=["呼吸困難", "冒冷汗", "噁心"]),

            # Critical Respiratory
            EmergencyKeyword("呼吸困難", SymptomCategory.RESPIRATORY, EmergencyLevel.CRITICAL),
            EmergencyKeyword("窒息", SymptomCategory.RESPIRATORY, EmergencyLevel.CRITICAL),
            EmergencyKeyword("無法呼吸", SymptomCategory.RESPIRATORY, EmergencyLevel.CRITICAL),
            EmergencyKeyword("哮喘發作", SymptomCategory.RESPIRATORY, EmergencyLevel.HIGH),

            # Critical Neurological
            EmergencyKeyword("中風", SymptomCategory.NEUROLOGICAL, EmergencyLevel.CRITICAL),
            EmergencyKeyword("昏迷", SymptomCategory.NEUROLOGICAL, EmergencyLevel.CRITICAL),
            EmergencyKeyword("意識不清", SymptomCategory.NEUROLOGICAL, EmergencyLevel.CRITICAL),
            EmergencyKeyword("抽搐", SymptomCategory.NEUROLOGICAL, EmergencyLevel.HIGH),
            EmergencyKeyword("癲癇", SymptomCategory.NEUROLOGICAL, EmergencyLevel.HIGH),

            # Critical Trauma
            EmergencyKeyword("大量出血", SymptomCategory.TRAUMA, EmergencyLevel.CRITICAL),
            EmergencyKeyword("嚴重外傷", SymptomCategory.TRAUMA, EmergencyLevel.CRITICAL),
            EmergencyKeyword("骨折", SymptomCategory.TRAUMA, EmergencyLevel.HIGH,
                           context_required=True, additional_indicators=["開放性", "複合性", "移位"]),

            # High Priority
            EmergencyKeyword("劇烈頭痛", SymptomCategory.NEUROLOGICAL, EmergencyLevel.HIGH),
            EmergencyKeyword("高燒", SymptomCategory.OTHER, EmergencyLevel.HIGH,
                           context_required=True, additional_indicators=["39", "40", "持續"]),
            EmergencyKeyword("嚴重腹痛", SymptomCategory.GASTROINTESTINAL, EmergencyLevel.HIGH),

            # Psychiatric Emergencies
            EmergencyKeyword("自殺", SymptomCategory.PSYCHIATRIC, EmergencyLevel.CRITICAL),
            EmergencyKeyword("想死", SymptomCategory.PSYCHIATRIC, EmergencyLevel.CRITICAL),
            EmergencyKeyword("自殘", SymptomCategory.PSYCHIATRIC, EmergencyLevel.HIGH),
        ]

    def analyze_symptom_urgency(self,
                               symptom_text: str,
                               patient_age: Optional[int] = None) -> Dict:
        """Analyze symptom text for emergency indicators"""

        # Clean and normalize text
        normalized_text = self._normalize_text(symptom_text)

        # Detect emergency keywords
        detected_keywords = []
        highest_level = EmergencyLevel.LOW

        for keyword in self.emergency_keywords:
            if self._keyword_matches(normalized_text, keyword, patient_age):
                detected_keywords.append(keyword)

                # Update highest emergency level
                if keyword.level.value == "critical":
                    highest_level = EmergencyLevel.CRITICAL
                elif keyword.level.value == "high" and highest_level != EmergencyLevel.CRITICAL:
                    highest_level = EmergencyLevel.HIGH
                elif keyword.level.value == "moderate" and highest_level not in [EmergencyLevel.CRITICAL, EmergencyLevel.HIGH]:
                    highest_level = EmergencyLevel.MODERATE

        # Context analysis for ambiguous symptoms
        context_score = self._analyze_context(normalized_text, detected_keywords)

        # Generate emergency response
        return self._generate_emergency_response(
            symptom_text,
            detected_keywords,
            highest_level,
            context_score
        )

    def _keyword_matches(self,
                        text: str,
                        keyword: EmergencyKeyword,
                        patient_age: Optional[int]) -> bool:
        """Check if keyword matches with context validation"""

        # Basic keyword match
        if keyword.term not in text:
            return False

        # Age-specific validation
        if keyword.age_specific and patient_age:
            min_age, max_age = keyword.age_specific
            if not (min_age <= patient_age <= max_age):
                return False

        # Context validation for ambiguous terms
        if keyword.context_required and keyword.additional_indicators:
            has_context = any(
                indicator in text for indicator in keyword.additional_indicators
            )
            if not has_context:
                return False

        # Check exclusion patterns
        if self._has_exclusion_context(text, keyword):
            return False

        return True

    def _generate_emergency_response(self,
                                   original_text: str,
                                   keywords: List[EmergencyKeyword],
                                   level: EmergencyLevel,
                                   context_score: float) -> Dict:
        """Generate appropriate emergency response"""

        if level == EmergencyLevel.CRITICAL:
            return self._generate_critical_response(keywords)
        elif level == EmergencyLevel.HIGH:
            return self._generate_high_priority_response(keywords, context_score)
        elif level == EmergencyLevel.MODERATE:
            return self._generate_moderate_response(keywords)
        else:
            return self._generate_routine_response()

    def _generate_critical_response(self, keywords: List[EmergencyKeyword]) -> Dict:
        """Generate critical emergency response"""
        return {
            "emergency_level": "critical",
            "immediate_action": "立即撥打119",
            "advice": "您描述的症狀可能為緊急醫療狀況，請立即撥打119或前往最近的急診室。",
            "next_steps": [
                "立即撥打119（消防救護車）",
                "如無法撥打119，請撥打112（國際緊急號碼）",
                "前往最近的急診室",
                "保持冷靜，避免不必要的移動",
                "準備身分證件和健保卡",
                "如有隨身藥物，請一併攜帶"
            ],
            "emergency_contacts": ["119", "112"],
            "hospital_search_priority": "emergency_only",
            "keywords_detected": [kw.term for kw in keywords],
            "bypass_normal_triage": True
        }
```

### 2. Taiwan Emergency Services Integration
```python
class TaiwanEmergencyServices:
    def __init__(self):
        self.emergency_services = {
            "119": {
                "name": "消防救護車",
                "description": "火災、救護車、緊急救助",
                "availability": "24小時",
                "languages": ["中文"],
                "scope": "全台灣",
                "response_time": "平均8-12分鐘（都市區域）",
                "when_to_call": [
                    "生命危險的緊急醫療狀況",
                    "嚴重外傷或意外事故",
                    "心肌梗塞、中風等急性疾病",
                    "呼吸困難、昏迷等危急症狀"
                ]
            },
            "110": {
                "name": "警察局",
                "description": "治安、交通、刑事案件",
                "availability": "24小時",
                "languages": ["中文", "英文（部分地區）"],
                "scope": "全台灣",
                "when_to_call": [
                    "治安事件",
                    "交通事故（有人員傷亡）",
                    "家庭暴力",
                    "其他需要警方協助的緊急狀況"
                ]
            },
            "112": {
                "name": "行動電話國際緊急號碼",
                "description": "GSM行動電話緊急求救",
                "availability": "24小時",
                "languages": ["多語言支援"],
                "scope": "行動電話涵蓋區域",
                "special_features": [
                    "無SIM卡也能撥打",
                    "自動定位功能",
                    "國際標準緊急號碼",
                    "轉接至適當的緊急服務"
                ],
                "when_to_call": [
                    "手機無訊號但有緊急狀況",
                    "不確定應撥打哪個緊急號碼",
                    "外籍人士緊急求助",
                    "119或110無法接通時"
                ]
            },
            "113": {
                "name": "婦幼保護專線",
                "description": "家庭暴力、性侵害、兒童保護",
                "availability": "24小時",
                "languages": ["中文", "英文", "越南語", "印尼語", "泰語"],
                "scope": "全台灣",
                "when_to_call": [
                    "家庭暴力事件",
                    "兒童虐待或疏忽",
                    "性侵害事件",
                    "其他婦幼保護相關問題"
                ]
            },
            "165": {
                "name": "反詐騙諮詢專線",
                "description": "詐騙案件預防與諮詢",
                "availability": "24小時",
                "languages": ["中文"],
                "scope": "全台灣",
                "when_to_call": [
                    "疑似詐騙電話或簡訊",
                    "網路詐騙諮詢",
                    "投資詐騙預防",
                    "其他詐騙相關問題"
                ]
            }
        }

    def get_appropriate_emergency_service(self,
                                        emergency_type: str,
                                        symptom_category: SymptomCategory) -> List[str]:
        """Get appropriate emergency service based on situation"""

        if emergency_type == "critical_medical":
            return ["119", "112"]
        elif emergency_type == "psychiatric_emergency":
            if symptom_category == SymptomCategory.PSYCHIATRIC:
                return ["119", "113"]  # Medical + protection if needed
            return ["119"]
        elif emergency_type == "trauma":
            return ["119", "110"]  # Medical + police if accident
        else:
            return ["119"]

    def format_emergency_guidance(self,
                                emergency_services: List[str],
                                context: str = "") -> Dict:
        """Format emergency service guidance for response"""

        guidance = {
            "primary_contacts": [],
            "secondary_contacts": [],
            "instructions": [],
            "preparation": []
        }

        for service_code in emergency_services:
            if service_code in self.emergency_services:
                service = self.emergency_services[service_code]

                contact_info = {
                    "number": service_code,
                    "name": service["name"],
                    "description": service["description"],
                    "availability": service["availability"]
                }

                if service_code in ["119", "112"]:
                    guidance["primary_contacts"].append(contact_info)
                else:
                    guidance["secondary_contacts"].append(contact_info)

        # Add general emergency instructions
        guidance["instructions"] = [
            "保持冷靜，清楚說明狀況",
            "提供正確的地址或位置資訊",
            "說明患者的症狀和意識狀態",
            "告知是否有慢性疾病或用藥",
            "保持電話暢通以接受進一步指示"
        ]

        guidance["preparation"] = [
            "準備健保卡和身分證件",
            "收集患者的用藥清單",
            "記錄症狀開始的時間",
            "清理通往急救車的路徑"
        ]

        return guidance
```

### 3. Medical Guidance Validation System
```python
class MedicalGuidanceValidator:
    def __init__(self):
        self.prohibited_statements = self._load_prohibited_statements()
        self.required_disclaimers = self._load_required_disclaimers()
        self.safe_language_patterns = self._load_safe_patterns()

    def _load_prohibited_statements(self) -> Dict[str, List[str]]:
        """Load prohibited diagnostic and treatment statements"""
        return {
            "diagnostic_claims": [
                "診斷為", "確定是", "一定是", "絕對是",
                "患有", "罹患", "得了", "病因是"
            ],
            "treatment_recommendations": [
                "建議服用", "需要手術", "應該開刀",
                "處方", "藥物治療", "劑量"
            ],
            "prognosis_statements": [
                "會好轉", "不會有事", "沒有危險",
                "預後良好", "不用擔心", "沒關係"
            ],
            "dismissive_language": [
                "只是", "不過是", "沒什麼大不了",
                "小問題", "不嚴重", "常見的"
            ]
        }

    def validate_medical_response(self, response: Dict) -> Tuple[bool, List[str]]:
        """Validate medical response for safety and compliance"""

        validation_errors = []

        # Check for prohibited language
        advice_text = response.get("advice", "")
        for category, phrases in self.prohibited_statements.items():
            for phrase in phrases:
                if phrase in advice_text:
                    validation_errors.append(
                        f"禁用語句檢測: '{phrase}' 屬於 {category}"
                    )

        # Validate disclaimer presence
        disclaimer = response.get("disclaimer", "")
        if not self._validate_disclaimer(disclaimer):
            validation_errors.append("醫療免責聲明不完整或遺失")

        # Check emergency contact inclusion
        if response.get("emergency_level") in ["critical", "high"]:
            emergency_contacts = response.get("emergency_contacts", [])
            if "119" not in emergency_contacts:
                validation_errors.append("緊急狀況必須包含119聯絡資訊")

        # Validate guidance language
        if not self._validate_guidance_language(advice_text):
            validation_errors.append("建議語言不符合醫療指導原則")

        return len(validation_errors) == 0, validation_errors

    def _validate_disclaimer(self, disclaimer: str) -> bool:
        """Validate medical disclaimer completeness"""
        required_elements = [
            "不能取代專業醫療",
            "緊急狀況請撥打119",
            "一般資訊參考"
        ]

        return all(element in disclaimer for element in required_elements)

    def sanitize_medical_advice(self, advice: str) -> str:
        """Sanitize medical advice to ensure safety"""

        sanitized = advice

        # Replace prohibited diagnostic language
        diagnostic_replacements = {
            "診斷為": "可能與以下情況有關",
            "確定是": "症狀可能指向",
            "一定是": "建議考慮",
            "患有": "可能存在"
        }

        for prohibited, replacement in diagnostic_replacements.items():
            sanitized = sanitized.replace(prohibited, replacement)

        # Add cautionary language if missing
        if not any(cautious in sanitized for cautious in ["建議", "可能", "請"]):
            sanitized = f"建議{sanitized}"

        # Ensure professional referral language
        if "醫師" not in sanitized and "醫療專業" not in sanitized:
            sanitized += "，請諮詢合格醫療專業人員。"

        return sanitized

    def enforce_safety_protocols(self, response: Dict) -> Dict:
        """Enforce mandatory safety protocols in response"""

        # Ensure emergency protocols for critical cases
        if response.get("emergency_level") == "critical":
            response["immediate_action"] = "立即撥打119"
            response["bypass_normal_triage"] = True

            # Override any non-emergency advice
            response["advice"] = (
                "您描述的症狀可能為緊急醫療狀況，"
                "請立即撥打119或前往最近的急診室。"
            )

        # Ensure complete disclaimer
        if not response.get("disclaimer"):
            response["disclaimer"] = self._get_standard_disclaimer()

        # Add emergency contacts if missing
        if not response.get("emergency_contacts"):
            response["emergency_contacts"] = ["119", "112"]

        return response

    def _get_standard_disclaimer(self) -> str:
        """Get comprehensive medical disclaimer"""
        return (
            "本系統僅提供一般健康資訊參考，不能取代專業醫療診斷或治療。"
            "所提供的資訊不應用於診斷或治療任何疾病。"
            "如有醫療需求，請諮詢合格醫療專業人員。"
            "緊急狀況請立即撥打119或112。"
            "對於因使用本資訊而產生的任何後果，本系統不承擔責任。"
        )
```

### 4. Medical Safety Monitoring
```python
class MedicalSafetyMonitoring:
    def __init__(self):
        self.safety_metrics = {
            "emergency_detection_rate": 0.0,
            "false_positive_rate": 0.0,
            "response_validation_failures": 0,
            "disclaimer_compliance": 0.0,
            "emergency_bypass_attempts": 0
        }

    async def monitor_safety_events(self):
        """Continuous monitoring of medical safety events"""

        # Monitor emergency detection accuracy
        await self._monitor_emergency_detection()

        # Monitor response validation
        await self._monitor_response_validation()

        # Monitor compliance metrics
        await self._monitor_compliance_metrics()

        # Check for safety protocol bypasses
        await self._monitor_bypass_attempts()

    async def _monitor_emergency_detection(self):
        """Monitor emergency detection accuracy and response times"""

        recent_emergency_cases = await self._get_recent_emergency_cases()

        for case in recent_emergency_cases:
            # Validate emergency detection was appropriate
            if not self._validate_emergency_classification(case):
                await self._log_safety_concern(
                    "EMERGENCY_DETECTION_ERROR",
                    f"Potentially inappropriate emergency classification: {case['case_id']}"
                )

            # Check response time compliance
            if case.get("response_time_ms", 0) > 500:  # 500ms limit for emergency cases
                await self._log_performance_concern(
                    "EMERGENCY_RESPONSE_SLOW",
                    f"Emergency response time exceeded limit: {case['response_time_ms']}ms"
                )

    async def _monitor_response_validation(self):
        """Monitor medical response validation failures"""

        validation_failures = await self._get_validation_failures()

        if len(validation_failures) > 0:
            await self._trigger_safety_alert(
                "RESPONSE_VALIDATION_FAILURES",
                f"Detected {len(validation_failures)} response validation failures",
                validation_failures
            )

    async def validate_medical_safety_protocols(self) -> Dict:
        """Comprehensive validation of medical safety protocols"""

        validation_results = {
            "emergency_detection": await self._test_emergency_detection(),
            "response_validation": await self._test_response_validation(),
            "disclaimer_enforcement": await self._test_disclaimer_enforcement(),
            "safety_monitoring": await self._test_safety_monitoring(),
            "compliance_tracking": await self._test_compliance_tracking()
        }

        overall_safety_score = self._calculate_safety_score(validation_results)

        return {
            "safety_score": overall_safety_score,
            "validation_results": validation_results,
            "recommendations": self._generate_safety_recommendations(validation_results),
            "compliance_status": "compliant" if overall_safety_score >= 0.95 else "needs_attention"
        }

    async def _test_emergency_detection(self) -> Dict:
        """Test emergency detection accuracy with known cases"""

        test_cases = [
            {"text": "胸痛且呼吸困難", "expected": "critical"},
            {"text": "輕微頭痛", "expected": "low"},
            {"text": "中風症狀", "expected": "critical"},
            {"text": "感冒症狀", "expected": "low"}
        ]

        results = {"passed": 0, "failed": 0, "details": []}

        for case in test_cases:
            detection_result = await self._run_emergency_detection(case["text"])
            expected_level = case["expected"]
            actual_level = detection_result.get("emergency_level", "unknown")

            if actual_level == expected_level:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["details"].append({
                    "case": case["text"],
                    "expected": expected_level,
                    "actual": actual_level
                })

        results["accuracy"] = results["passed"] / len(test_cases)
        return results
```

### 5. Medical Knowledge Integration
```python
class MedicalKnowledgeBase:
    def __init__(self):
        self.symptom_categories = self._load_symptom_categories()
        self.red_flag_symptoms = self._load_red_flag_symptoms()
        self.triage_guidelines = self._load_triage_guidelines()

    def _load_red_flag_symptoms(self) -> Dict:
        """Load red flag symptoms requiring immediate attention"""
        return {
            "cardiovascular": {
                "symptoms": [
                    "胸痛伴隨輻射至左臂或下顎",
                    "突發性劇烈胸痛",
                    "胸痛伴隨呼吸困難和冒冷汗",
                    "心悸伴隨暈厥"
                ],
                "immediate_action": "立即撥打119",
                "considerations": [
                    "心肌梗塞可能",
                    "主動脈剝離風險",
                    "肺栓塞可能性"
                ]
            },
            "neurological": {
                "symptoms": [
                    "突發性嚴重頭痛（有生以來最痛）",
                    "意識狀態改變",
                    "單側肢體無力或麻痺",
                    "言語困難或理解障礙",
                    "突發性視力喪失"
                ],
                "immediate_action": "立即撥打119",
                "considerations": [
                    "腦中風可能",
                    "腦出血風險",
                    "腦膜炎可能性"
                ]
            },
            "respiratory": {
                "symptoms": [
                    "嚴重呼吸困難或窒息感",
                    "胸痛伴隨呼吸困難",
                    "咳血或大量血痰",
                    "發紺（嘴唇或指甲變藍）"
                ],
                "immediate_action": "立即撥打119",
                "considerations": [
                    "肺栓塞可能",
                    "氣胸風險",
                    "嚴重哮喘發作"
                ]
            }
        }

    def get_triage_recommendation(self,
                                symptom_text: str,
                                patient_context: Dict) -> Dict:
        """Get evidence-based triage recommendation"""

        # Analyze symptoms against medical knowledge
        symptom_analysis = self._analyze_symptoms(symptom_text)

        # Check for red flag symptoms
        red_flags = self._check_red_flags(symptom_text, symptom_analysis)

        # Generate recommendation based on clinical guidelines
        recommendation = self._generate_clinical_recommendation(
            symptom_analysis,
            red_flags,
            patient_context
        )

        return recommendation

    def _generate_clinical_recommendation(self,
                                        symptom_analysis: Dict,
                                        red_flags: List[str],
                                        patient_context: Dict) -> Dict:
        """Generate clinical recommendation based on analysis"""

        if red_flags:
            return {
                "urgency": "emergency",
                "action": "immediate_medical_attention",
                "reasoning": f"檢測到警示症狀: {', '.join(red_flags)}",
                "next_steps": [
                    "立即撥打119",
                    "前往急診室",
                    "攜帶所有相關藥物和醫療記錄"
                ]
            }

        # Age-specific considerations
        age = patient_context.get("age", 0)
        if age >= 65:
            return self._get_elderly_specific_recommendation(symptom_analysis)
        elif age <= 18:
            return self._get_pediatric_specific_recommendation(symptom_analysis)

        # Standard adult recommendation
        return self._get_standard_recommendation(symptom_analysis)
```

This medical safety architecture ensures that the Taiwan Medical AI Agent maintains the highest standards of medical safety while providing appropriate guidance that directs users to qualified medical professionals and emergency services when needed. The system is designed to err on the side of caution and never provide diagnostic conclusions, focusing instead on safety-first guidance and appropriate medical referrals.