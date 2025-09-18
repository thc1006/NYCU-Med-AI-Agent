# Taiwan Localization Architecture

## Localization Overview

The Taiwan Medical AI Agent implements comprehensive localization specifically designed for the Taiwan healthcare ecosystem, cultural context, and regulatory environment. This architecture ensures culturally appropriate, linguistically accurate, and contextually relevant medical guidance services.

## Core Localization Principles

### 1. Language & Cultural Adaptation
- **Traditional Chinese (zh-TW)**: All user interfaces and communications in Traditional Chinese
- **Medical Terminology**: Taiwan-specific medical terminology and conventions
- **Cultural Sensitivity**: Appropriate communication styles for Taiwan medical culture
- **Respectful Language**: Formal and respectful tone appropriate for medical contexts

### 2. Healthcare System Integration
- **National Health Insurance (NHI)**: Integration with Taiwan's universal healthcare system
- **Medical Facility Classification**: Understanding of Taiwan's hospital classification system
- **Regional Healthcare**: Awareness of regional healthcare disparities and resources
- **Regulatory Compliance**: Adherence to Taiwan medical practice standards

### 3. Emergency Services Localization
- **Emergency Numbers**: Taiwan-specific emergency contact numbers and protocols
- **Service Availability**: Understanding of emergency service coverage and capabilities
- **Response Procedures**: Taiwan-appropriate emergency response guidance
- **Multilingual Support**: Emergency assistance for Taiwan's diverse population

## Language Architecture

### 1. Traditional Chinese Implementation
```python
from typing import Dict, List, Optional
import re
from dataclasses import dataclass
from enum import Enum

class LanguageVariant(Enum):
    TRADITIONAL_CHINESE = "zh-TW"
    SIMPLIFIED_CHINESE = "zh-CN"
    ENGLISH = "en-US"

@dataclass
class LocalizedText:
    zh_tw: str
    en_us: Optional[str] = None
    pronunciation: Optional[str] = None  # Bopomofo or Pinyin
    context_notes: Optional[str] = None

class TaiwanLanguageManager:
    def __init__(self):
        self.medical_terminology = self._load_medical_terminology()
        self.emergency_phrases = self._load_emergency_phrases()
        self.cultural_adaptations = self._load_cultural_adaptations()

    def _load_medical_terminology(self) -> Dict[str, LocalizedText]:
        """Load Taiwan-specific medical terminology"""
        return {
            # Cardiovascular terms
            "chest_pain": LocalizedText(
                zh_tw="胸痛",
                en_us="chest pain",
                pronunciation="ㄒㄩㄥ ㄊㄨㄥˋ",
                context_notes="Standard medical term used in Taiwan hospitals"
            ),
            "heart_attack": LocalizedText(
                zh_tw="心肌梗塞",
                en_us="myocardial infarction",
                pronunciation="ㄒㄧㄣ ㄐㄧ ㄍㄥˇ ㄙㄜˋ",
                context_notes="Preferred term over 心臟病發作 in medical contexts"
            ),

            # Respiratory terms
            "difficulty_breathing": LocalizedText(
                zh_tw="呼吸困難",
                en_us="difficulty breathing",
                pronunciation="ㄏㄨ ㄒㄧ ㄎㄨㄣˋ ㄋㄢˊ",
                context_notes="Standard terminology in Taiwan medical practice"
            ),
            "shortness_of_breath": LocalizedText(
                zh_tw="氣促",
                en_us="shortness of breath",
                pronunciation="ㄑㄧˋ ㄘㄨˋ",
                context_notes="Common clinical term"
            ),

            # Neurological terms
            "stroke": LocalizedText(
                zh_tw="中風",
                en_us="stroke",
                pronunciation="ㄓㄨㄥ ㄈㄥ",
                context_notes="Traditional term widely understood in Taiwan"
            ),
            "unconscious": LocalizedText(
                zh_tw="昏迷",
                en_us="unconscious",
                pronunciation="ㄏㄨㄣ ㄇㄧˊ",
                context_notes="Medical term for loss of consciousness"
            ),

            # Emergency services
            "ambulance": LocalizedText(
                zh_tw="救護車",
                en_us="ambulance",
                pronunciation="ㄐㄧㄡˋ ㄏㄨˋ ㄔㄜ",
                context_notes="Emergency medical transport"
            ),
            "emergency_room": LocalizedText(
                zh_tw="急診室",
                en_us="emergency room",
                pronunciation="ㄐㄧˊ ㄓㄣˇ ㄕˋ",
                context_notes="Standard term for ER in Taiwan hospitals"
            ),

            # Hospital classifications
            "medical_center": LocalizedText(
                zh_tw="醫學中心",
                en_us="medical center",
                pronunciation="ㄧ ㄒㄩㄝˊ ㄓㄨㄥ ㄒㄧㄣ",
                context_notes="Highest level hospital classification in Taiwan"
            ),
            "regional_hospital": LocalizedText(
                zh_tw="區域醫院",
                en_us="regional hospital",
                pronunciation="ㄑㄩ ㄩˋ ㄧ ㄩㄢˋ",
                context_notes="Mid-level hospital classification"
            ),
            "district_hospital": LocalizedText(
                zh_tw="地區醫院",
                en_us="district hospital",
                pronunciation="ㄉㄧˋ ㄑㄩ ㄧ ㄩㄢˋ",
                context_notes="Local community hospital level"
            )
        }

    def _load_emergency_phrases(self) -> Dict[str, LocalizedText]:
        """Load emergency communication phrases"""
        return {
            "call_119": LocalizedText(
                zh_tw="請立即撥打119",
                en_us="Please call 119 immediately",
                pronunciation="ㄑㄧㄥˇ ㄌㄧˋ ㄐㄧ ㄅㄛ ㄉㄚˇ ㄧ ㄧ ㄐㄧㄡˇ",
                context_notes="Standard emergency instruction"
            ),
            "go_to_er": LocalizedText(
                zh_tw="前往最近的急診室",
                en_us="Go to the nearest emergency room",
                pronunciation="ㄑㄧㄢˊ ㄨㄤˇ ㄗㄨㄟˋ ㄐㄧㄣˋ ㄉㄜ˙ ㄐㄧˊ ㄓㄣˇ ㄕˋ",
                context_notes="Emergency response instruction"
            ),
            "stay_calm": LocalizedText(
                zh_tw="保持冷靜",
                en_us="Stay calm",
                pronunciation="ㄅㄠˇ ㄔˊ ㄌㄥˇ ㄐㄧㄥˋ",
                context_notes="Common emergency advice"
            ),
            "prepare_documents": LocalizedText(
                zh_tw="準備健保卡和身分證件",
                en_us="Prepare your NHI card and identification",
                pronunciation="ㄓㄨㄣˇ ㄅㄟˋ ㄐㄧㄢˋ ㄅㄠˇ ㄎㄚˇ ㄏㄜˊ ㄕㄣ ㄈㄣˋ ㄓㄥˋ ㄐㄧㄢˋ",
                context_notes="Taiwan-specific healthcare requirement"
            )
        }

    def localize_medical_response(self,
                                response_template: str,
                                context: Dict) -> str:
        """Localize medical response for Taiwan context"""

        # Apply Taiwan medical terminology
        localized = self._apply_medical_terminology(response_template)

        # Add cultural context
        localized = self._add_cultural_context(localized, context)

        # Apply respectful language patterns
        localized = self._apply_respectful_language(localized)

        # Validate traditional Chinese usage
        localized = self._validate_traditional_chinese(localized)

        return localized

    def _apply_respectful_language(self, text: str) -> str:
        """Apply respectful language patterns appropriate for Taiwan medical context"""

        # Use respectful address forms
        respectful_replacements = {
            "你": "您",  # More respectful "you"
            "建議你": "建議您",
            "你的": "您的",
            "你需要": "您需要"
        }

        localized = text
        for informal, formal in respectful_replacements.items():
            localized = localized.replace(informal, formal)

        # Add appropriate honorifics for medical professionals
        medical_honorifics = {
            "醫生": "醫師",  # Preferred professional title
            "大夫": "醫師",
            "醫士": "醫師"
        }

        for informal, formal in medical_honorifics.items():
            localized = localized.replace(informal, formal)

        return localized

    def _validate_traditional_chinese(self, text: str) -> str:
        """Validate and correct traditional Chinese usage"""

        # Common simplified to traditional corrections
        corrections = {
            "医": "醫", "药": "藥", "疗": "療", "检": "檢",
            "诊": "診", "缓": "緩", "请": "請", "护": "護",
            "应": "應", "约": "約", "发": "發", "烧": "燒",
            "头": "頭", "经": "經", "过": "過", "问": "問"
        }

        corrected = text
        for simplified, traditional in corrections.items():
            corrected = corrected.replace(simplified, traditional)

        return corrected
```

### 2. Taiwan Healthcare System Integration
```python
class TaiwanHealthcareSystem:
    def __init__(self):
        self.nhi_system = self._initialize_nhi_system()
        self.hospital_classifications = self._load_hospital_classifications()
        self.regional_healthcare = self._load_regional_healthcare_data()

    def _initialize_nhi_system(self) -> Dict:
        """Initialize National Health Insurance system information"""
        return {
            "coverage": {
                "population_coverage": "99.9%",
                "services_covered": [
                    "門診醫療", "住院醫療", "牙科醫療", "中醫醫療",
                    "復健治療", "預防保健", "居家照護"
                ],
                "copayment_info": {
                    "outpatient": "掛號費 + 部分負擔",
                    "emergency": "急診部分負擔",
                    "inpatient": "住院部分負擔"
                }
            },
            "card_info": {
                "name": "健保卡",
                "features": [
                    "晶片卡設計", "照片識別", "就醫記錄",
                    "藥物過敏記錄", "器官捐贈意願"
                ],
                "validity": "需定期更新",
                "replacement": "遺失可申請補發"
            },
            "hospitals": {
                "contracted_facilities": "特約醫療院所",
                "verification": "可透過健保署網站查詢",
                "quality_indicators": "醫療品質資訊公開"
            }
        }

    def _load_hospital_classifications(self) -> Dict:
        """Load Taiwan hospital classification system"""
        return {
            "醫學中心": {
                "description": "最高等級醫療機構",
                "capabilities": [
                    "急重症醫療", "疑難雜症診治", "醫學研究",
                    "醫學教育", "轉診支援"
                ],
                "bed_count": "500床以上",
                "specialties": "完整專科醫療",
                "emergency_level": "24小時急診",
                "examples": [
                    "台大醫院", "榮總", "長庚醫院", "馬偕醫院"
                ]
            },
            "區域醫院": {
                "description": "區域性醫療中心",
                "capabilities": [
                    "一般急症處理", "常見疾病診治",
                    "健康檢查", "專科門診"
                ],
                "bed_count": "250-499床",
                "specialties": "主要專科醫療",
                "emergency_level": "急診服務",
                "referral_role": "轉診中心功能"
            },
            "地區醫院": {
                "description": "社區醫療服務",
                "capabilities": [
                    "基本醫療服務", "常見疾病診治",
                    "預防保健", "慢性病管理"
                ],
                "bed_count": "20-249床",
                "specialties": "基本專科醫療",
                "emergency_level": "基本急診",
                "community_role": "社區健康中心"
            },
            "診所": {
                "description": "基層醫療機構",
                "capabilities": [
                    "門診醫療", "基本檢查", "預防接種",
                    "健康諮詢", "慢性病追蹤"
                ],
                "bed_count": "19床以下",
                "specialties": "專科或家醫科",
                "accessibility": "就近醫療服務",
                "role": "初級醫療照護"
            }
        }

    def get_healthcare_guidance(self,
                              symptom_severity: str,
                              location: Dict,
                              time_of_day: str) -> Dict:
        """Get Taiwan healthcare system guidance"""

        guidance = {
            "recommended_facility_type": self._get_recommended_facility(symptom_severity),
            "nhi_coverage": self._get_nhi_coverage_info(symptom_severity),
            "cost_information": self._get_cost_information(symptom_severity),
            "accessibility": self._get_accessibility_info(location, time_of_day)
        }

        return guidance

    def _get_recommended_facility(self, severity: str) -> Dict:
        """Get recommended healthcare facility based on severity"""

        facility_recommendations = {
            "critical": {
                "primary": "醫學中心急診",
                "alternative": "區域醫院急診",
                "reason": "需要最高等級醫療資源",
                "action": "立即前往或撥打119"
            },
            "urgent": {
                "primary": "區域醫院急診",
                "alternative": "醫學中心急診",
                "reason": "需要及時專業醫療處理",
                "action": "盡快前往急診"
            },
            "routine": {
                "primary": "地區醫院門診",
                "alternative": "診所",
                "reason": "一般醫療服務即可處理",
                "action": "預約門診時間"
            },
            "minor": {
                "primary": "診所",
                "alternative": "地區醫院門診",
                "reason": "基層醫療服務適合",
                "action": "就近醫療諮詢"
            }
        }

        return facility_recommendations.get(severity, facility_recommendations["routine"])
```

### 3. Regional and Cultural Context
```python
class TaiwanRegionalContext:
    def __init__(self):
        self.regions = self._load_regional_data()
        self.cultural_factors = self._load_cultural_factors()
        self.linguistic_variations = self._load_linguistic_variations()

    def _load_regional_data(self) -> Dict:
        """Load Taiwan regional healthcare data"""
        return {
            "北部": {
                "cities": ["台北市", "新北市", "桃園市", "基隆市", "新竹市", "新竹縣"],
                "medical_resources": "豐富",
                "medical_centers": ["台大醫院", "榮總", "馬偕", "長庚"],
                "characteristics": [
                    "醫療資源集中", "交通便利", "多語言服務",
                    "國際醫療服務", "高科技醫療設備"
                ],
                "emergency_coverage": "完整",
                "transport": "捷運、公車、計程車充足"
            },
            "中部": {
                "cities": ["台中市", "彰化縣", "南投縣", "苗栗縣", "雲林縣"],
                "medical_resources": "充足",
                "medical_centers": ["中國醫藥大學附醫", "台中榮總", "彰基"],
                "characteristics": [
                    "醫療網絡完善", "中部醫療中心", "傳統與現代並重"
                ],
                "emergency_coverage": "良好",
                "transport": "公共運輸系統發達"
            },
            "南部": {
                "cities": ["台南市", "高雄市", "嘉義市", "嘉義縣", "屏東縣"],
                "medical_resources": "充足",
                "medical_centers": ["成大醫院", "高雄榮總", "長庚高雄"],
                "characteristics": [
                    "南部醫療重鎮", "研究型醫院", "熱帶醫學特色"
                ],
                "emergency_coverage": "完整",
                "cultural_notes": "重視傳統醫療文化"
            },
            "東部": {
                "cities": ["花蓮縣", "台東縣"],
                "medical_resources": "相對有限",
                "medical_centers": ["花蓮慈濟", "台東馬偕"],
                "characteristics": [
                    "地理隔離", "原住民族群多", "醫療可及性挑戰"
                ],
                "emergency_coverage": "基本覆蓋",
                "special_considerations": [
                    "可能需要空中救護", "轉診距離較遠",
                    "多元文化醫療需求"
                ]
            },
            "離島": {
                "areas": ["澎湖縣", "金門縣", "連江縣"],
                "medical_resources": "有限",
                "medical_facilities": ["澎湖醫院", "金門醫院", "連江縣立醫院"],
                "characteristics": [
                    "資源有限", "後送機制重要", "社區醫療模式"
                ],
                "emergency_coverage": "基本服務",
                "special_procedures": [
                    "緊急空中後送", "視訊診療", "定期醫療團巡診"
                ]
            }
        }

    def _load_cultural_factors(self) -> Dict:
        """Load Taiwan cultural factors affecting healthcare"""
        return {
            "family_involvement": {
                "description": "家庭參與醫療決策",
                "implications": [
                    "重視家屬意見", "集體決策模式",
                    "照護責任分擊", "情感支持重要"
                ],
                "communication_style": "尊重長者意見，重視家庭和諧"
            },
            "traditional_medicine": {
                "description": "中醫傳統醫學融合",
                "acceptance": "廣泛接受和使用",
                "integration": [
                    "中西醫整合", "草藥使用普遍",
                    "養生觀念", "預防保健"
                ],
                "considerations": "需注意中西藥交互作用"
            },
            "religious_beliefs": {
                "description": "宗教信仰對醫療的影響",
                "common_beliefs": [
                    "佛教", "道教", "基督教", "民間信仰"
                ],
                "medical_implications": [
                    "器官捐贈觀念", "安寧療護接受度",
                    "醫療倫理考量", "祈福與醫療並重"
                ]
            },
            "language_preferences": {
                "description": "語言使用偏好",
                "primary": "國語（中文）",
                "regional": ["台語", "客語", "原住民語"],
                "elderly_considerations": "可能較習慣台語或方言",
                "medical_communication": "重要醫療資訊需多語言支援"
            }
        }

    def get_regional_healthcare_guidance(self,
                                       location: Dict,
                                       symptom_severity: str) -> Dict:
        """Get region-specific healthcare guidance"""

        region = self._identify_region(location)
        regional_data = self.regions.get(region, {})

        guidance = {
            "region": region,
            "medical_resources": regional_data.get("medical_resources", "unknown"),
            "recommended_facilities": self._get_regional_facilities(region, symptom_severity),
            "transport_options": regional_data.get("transport", "standard"),
            "special_considerations": regional_data.get("special_considerations", []),
            "cultural_context": self._get_cultural_guidance(region)
        }

        # Add region-specific emergency protocols
        if region == "離島" and symptom_severity == "critical":
            guidance["emergency_protocols"] = [
                "立即聯絡當地醫院",
                "評估空中後送需求",
                "聯繫海巡署或空勤總隊",
                "準備後送相關文件"
            ]
        elif region == "東部" and symptom_severity in ["critical", "urgent"]:
            guidance["emergency_protocols"] = [
                "考慮直升機後送",
                "聯絡花蓮或台東主要醫院",
                "評估轉診需求"
            ]

        return guidance
```

### 4. Accessibility and Inclusivity Features
```python
class TaiwanAccessibilityFeatures:
    def __init__(self):
        self.language_support = self._initialize_language_support()
        self.accessibility_features = self._load_accessibility_features()
        self.special_populations = self._load_special_population_support()

    def _initialize_language_support(self) -> Dict:
        """Initialize multi-language support for Taiwan"""
        return {
            "primary": {
                "language": "繁體中文",
                "code": "zh-TW",
                "script": "Traditional Chinese",
                "coverage": "100%"
            },
            "secondary_languages": {
                "台語": {
                    "code": "nan-TW",
                    "script": "Traditional Chinese with phonetic",
                    "coverage": "Emergency phrases",
                    "target_population": "Elderly, southern Taiwan"
                },
                "客語": {
                    "code": "hak-TW",
                    "script": "Traditional Chinese with phonetic",
                    "coverage": "Emergency phrases",
                    "target_population": "Hakka communities"
                },
                "原住民語": {
                    "variants": ["阿美語", "泰雅語", "排灣語", "布農語"],
                    "coverage": "Basic emergency phrases",
                    "target_population": "Indigenous communities"
                }
            },
            "international_support": {
                "English": {
                    "code": "en-US",
                    "coverage": "Full emergency support",
                    "target_population": "Foreign residents, tourists"
                },
                "Vietnamese": {
                    "code": "vi-VN",
                    "coverage": "Basic emergency phrases",
                    "target_population": "Migrant workers"
                },
                "Indonesian": {
                    "code": "id-ID",
                    "coverage": "Basic emergency phrases",
                    "target_population": "Migrant workers"
                },
                "Thai": {
                    "code": "th-TH",
                    "coverage": "Basic emergency phrases",
                    "target_population": "Migrant workers"
                }
            }
        }

    def _load_accessibility_features(self) -> Dict:
        """Load accessibility features for diverse populations"""
        return {
            "visual_impairment": {
                "screen_reader_support": True,
                "high_contrast_mode": True,
                "large_text_option": True,
                "audio_responses": True,
                "braille_output": "External device support"
            },
            "hearing_impairment": {
                "text_based_interface": True,
                "visual_alerts": True,
                "sign_language_support": "Video relay planned",
                "vibration_alerts": "Mobile device support"
            },
            "cognitive_accessibility": {
                "simple_language_mode": True,
                "visual_symbols": True,
                "step_by_step_guidance": True,
                "repetition_options": True,
                "clear_navigation": True
            },
            "motor_disabilities": {
                "voice_input": True,
                "switch_navigation": True,
                "eye_tracking": "External device support",
                "simplified_interface": True
            },
            "elderly_users": {
                "larger_buttons": True,
                "simplified_navigation": True,
                "familiar_terminology": True,
                "patient_pace": True,
                "family_assistance_mode": True
            }
        }

    def adapt_interface_for_user(self,
                               user_profile: Dict,
                               preferences: Dict) -> Dict:
        """Adapt interface based on user needs and preferences"""

        adaptations = {
            "language": self._select_appropriate_language(user_profile),
            "accessibility": self._apply_accessibility_features(preferences),
            "cultural_context": self._apply_cultural_adaptations(user_profile),
            "medical_communication": self._adapt_medical_communication(user_profile)
        }

        return adaptations

    def _select_appropriate_language(self, user_profile: Dict) -> Dict:
        """Select appropriate language based on user profile"""

        age = user_profile.get("age", 30)
        region = user_profile.get("region", "台北市")
        ethnicity = user_profile.get("ethnicity", "漢族")

        # Language selection logic
        if age >= 70 and region in ["雲林縣", "嘉義縣", "台南市"]:
            # Elderly in southern Taiwan may prefer Taiwanese
            return {
                "primary": "zh-TW",
                "secondary": "nan-TW",
                "emergency_phrases": "台語",
                "medical_terms": "中文為主，台語輔助"
            }
        elif ethnicity.startswith("原住民"):
            # Indigenous population
            indigenous_language = self._detect_indigenous_language(user_profile)
            return {
                "primary": "zh-TW",
                "secondary": indigenous_language,
                "emergency_phrases": f"{indigenous_language} + 中文",
                "cultural_adaptations": True
            }
        else:
            # Standard Traditional Chinese
            return {
                "primary": "zh-TW",
                "secondary": None,
                "emergency_phrases": "繁體中文",
                "medical_terms": "標準醫學用語"
            }

    def generate_localized_emergency_guidance(self,
                                            emergency_type: str,
                                            user_context: Dict) -> Dict:
        """Generate culturally and linguistically appropriate emergency guidance"""

        base_guidance = self._get_base_emergency_guidance(emergency_type)

        # Apply localization
        localized_guidance = {
            "instructions": self._localize_instructions(
                base_guidance["instructions"],
                user_context
            ),
            "emergency_contacts": self._localize_emergency_contacts(user_context),
            "cultural_considerations": self._add_cultural_considerations(
                emergency_type,
                user_context
            ),
            "language_adaptations": self._apply_language_adaptations(
                base_guidance,
                user_context
            )
        }

        return localized_guidance
```

### 5. Taiwan Medical Context Database
```python
class TaiwanMedicalContextDB:
    def __init__(self):
        self.medical_facilities = self._load_medical_facilities()
        self.health_policies = self._load_health_policies()
        self.seasonal_health = self._load_seasonal_health_info()
        self.public_health = self._load_public_health_data()

    def _load_seasonal_health_info(self) -> Dict:
        """Load Taiwan seasonal health considerations"""
        return {
            "春季": {
                "months": ["3月", "4月", "5月"],
                "common_conditions": [
                    "過敏性鼻炎", "氣喘發作", "花粉症",
                    "濕疹", "春季感冒"
                ],
                "preventive_measures": [
                    "注意花粉指數", "維持室內空氣品質",
                    "適度運動", "充足睡眠"
                ],
                "health_alerts": [
                    "梅雨季節防潮濕", "注意氣溫變化",
                    "流感疫苗接種"
                ]
            },
            "夏季": {
                "months": ["6月", "7月", "8月"],
                "common_conditions": [
                    "熱衰竭", "中暑", "腸胃炎",
                    "皮膚炎", "登革熱"
                ],
                "preventive_measures": [
                    "防曬措施", "充足水分攝取",
                    "避免戶外高溫時段", "注意食物保鮮"
                ],
                "health_alerts": [
                    "颱風季節準備", "登革熱防治",
                    "空污指數關注"
                ]
            },
            "秋季": {
                "months": ["9月", "10月", "11月"],
                "common_conditions": [
                    "秋燥症狀", "過敏復發", "感冒",
                    "關節不適", "皮膚乾燥"
                ],
                "preventive_measures": [
                    "保持皮膚濕潤", "適度進補",
                    "規律作息", "漸進式運動"
                ],
                "health_alerts": [
                    "流感疫苗接種", "東北季風空污",
                    "氣溫變化適應"
                ]
            },
            "冬季": {
                "months": ["12月", "1月", "2月"],
                "common_conditions": [
                    "流感", "心血管疾病", "關節炎",
                    "憂鬱症狀", "呼吸道疾病"
                ],
                "preventive_measures": [
                    "保暖措施", "適量運動",
                    "均衡營養", "充足日照"
                ],
                "health_alerts": [
                    "一氧化碳中毒預防", "心血管疾病注意",
                    "年節飲食節制"
                ]
            }
        }

    def get_contextual_health_guidance(self,
                                     user_location: Dict,
                                     current_season: str,
                                     symptom_context: Dict) -> Dict:
        """Get contextual health guidance based on Taiwan context"""

        seasonal_info = self.seasonal_health.get(current_season, {})
        regional_context = self._get_regional_context(user_location)

        guidance = {
            "seasonal_considerations": seasonal_info.get("common_conditions", []),
            "regional_factors": regional_context,
            "preventive_measures": seasonal_info.get("preventive_measures", []),
            "health_alerts": seasonal_info.get("health_alerts", []),
            "cultural_health_practices": self._get_cultural_health_practices(current_season)
        }

        return guidance

    def _get_cultural_health_practices(self, season: str) -> List[str]:
        """Get traditional Taiwan health practices by season"""

        practices = {
            "春季": [
                "春季養肝", "早睡早起", "適度運動",
                "飲食清淡", "情志調養"
            ],
            "夏季": [
                "夏季養心", "避暑降溫", "清熱解毒",
                "少食生冷", "充足睡眠"
            ],
            "秋季": [
                "秋季養肺", "滋陰潤燥", "適度進補",
                "情緒調節", "預防感冒"
            ],
            "冬季": [
                "冬季養腎", "溫補陽氣", "早睡晚起",
                "避風寒", "適量進補"
            ]
        }

        return practices.get(season, [])
```

This Taiwan localization architecture ensures that the Medical AI Agent provides culturally appropriate, linguistically accurate, and contextually relevant services that align with Taiwan's healthcare system, cultural values, and regulatory requirements. The comprehensive localization approach addresses language needs, cultural sensitivities, regional variations, and accessibility requirements for Taiwan's diverse population.