"""
增強分診系統實作
包含症狀權重計算、科別推薦與醫院整合
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.domain.models import SymptomQuery, TriageResult, TriageLevel
from app.domain.rules_tw import (
    analyze_symptoms,
    determine_triage_level,
    get_disclaimer,
    get_emergency_numbers,
    get_recommended_departments,
    EMERGENCY_KEYWORDS,
    MODERATE_KEYWORDS,
    MILD_KEYWORDS
)


@dataclass
class SymptomWeight:
    """症狀權重模型"""
    symptom: str
    weight: float  # 0.0-1.0
    category: str  # cardiovascular, respiratory, neurological, etc.


@dataclass
class DepartmentRecommendation:
    """科別推薦模型"""
    name: str
    priority: str  # high, medium, low
    reason: str


class EnhancedTriageSystem:
    """增強分診系統"""

    # 症狀分類與權重映射
    SYMPTOM_WEIGHTS = {
        # 心血管系統 (高危險)
        "胸痛": {"weight": 0.95, "category": "cardiovascular"},
        "胸悶": {"weight": 0.85, "category": "cardiovascular"},
        "心悸": {"weight": 0.7, "category": "cardiovascular"},

        # 呼吸系統
        "呼吸困難": {"weight": 0.9, "category": "respiratory"},
        "喘": {"weight": 0.8, "category": "respiratory"},
        "咳嗽": {"weight": 0.3, "category": "respiratory"},
        "流鼻水": {"weight": 0.2, "category": "respiratory"},

        # 神經系統
        "意識不清": {"weight": 0.95, "category": "neurological"},
        "麻痺": {"weight": 0.9, "category": "neurological"},
        "劇烈頭痛": {"weight": 0.8, "category": "neurological"},
        "頭痛": {"weight": 0.4, "category": "neurological"},
        "輕微頭痛": {"weight": 0.3, "category": "neurological"},
        "頭暈": {"weight": 0.5, "category": "neurological"},

        # 消化系統
        "嘔吐": {"weight": 0.72, "category": "gastrointestinal"},
        "反覆嘔吐": {"weight": 0.75, "category": "gastrointestinal"},
        "腹痛": {"weight": 0.5, "category": "gastrointestinal"},
        "持續腹痛": {"weight": 0.72, "category": "gastrointestinal"},
        "腹瀉": {"weight": 0.4, "category": "gastrointestinal"},
        "血尿": {"weight": 0.72, "category": "urological"},
        "血便": {"weight": 0.75, "category": "gastrointestinal"},

        # 其他緊急
        "大量出血": {"weight": 0.95, "category": "emergency"},
        "自殺意念": {"weight": 0.95, "category": "psychiatric"},
        "自殺": {"weight": 0.95, "category": "psychiatric"},
        "自殘": {"weight": 0.95, "category": "psychiatric"},

        # 一般症狀
        "發燒": {"weight": 0.5, "category": "general"},
        "發高燒": {"weight": 0.72, "category": "general"},
        "高燒": {"weight": 0.72, "category": "general"},
        "疲倦": {"weight": 0.3, "category": "general"},
        "一般不適": {"weight": 0.3, "category": "general"},
        "喉嚨不適": {"weight": 0.3, "category": "respiratory"}
    }

    # 科別推薦映射
    DEPARTMENT_MAPPING = {
        "cardiovascular": ["心臟內科", "急診"],
        "respiratory": ["胸腔內科", "急診"],
        "neurological": ["神經內科", "急診"],
        "gastrointestinal": ["腸胃內科", "急診"],
        "urological": ["泌尿科", "急診"],
        "emergency": ["急診"],
        "psychiatric": ["精神科", "急診"],
        "general": ["家醫科", "內科"]
    }

    def __init__(self):
        """初始化增強分診系統"""
        self.symptom_history = []

    def calculate_symptom_weights(self, symptoms: List[str]) -> List[SymptomWeight]:
        """計算症狀權重"""
        weights = []

        for symptom in symptoms:
            # 檢查是否為紅旗症狀
            if any(keyword in symptom for keyword in ["胸痛", "呼吸困難", "意識不清", "大量出血", "突發麻痺", "自殺意念"]):
                # 紅旗症狀直接給予最高權重
                weights.append(SymptomWeight(
                    symptom=symptom,
                    weight=0.95,
                    category="emergency"
                ))
            elif symptom in self.SYMPTOM_WEIGHTS:
                data = self.SYMPTOM_WEIGHTS[symptom]
                weights.append(SymptomWeight(
                    symptom=symptom,
                    weight=data["weight"],
                    category=data["category"]
                ))
            else:
                # 未知症狀給予中等權重
                weights.append(SymptomWeight(
                    symptom=symptom,
                    weight=0.5,
                    category="unknown"
                ))

        return weights

    def recommend_departments(self, symptom_weights: List[SymptomWeight]) -> List[DepartmentRecommendation]:
        """推薦科別"""
        department_scores = {}

        for weight in symptom_weights:
            if weight.category in self.DEPARTMENT_MAPPING:
                departments = self.DEPARTMENT_MAPPING[weight.category]

                for dept in departments:
                    if dept not in department_scores:
                        department_scores[dept] = 0
                    department_scores[dept] += weight.weight

        # 排序並生成推薦
        sorted_depts = sorted(department_scores.items(), key=lambda x: x[1], reverse=True)
        recommendations = []

        for dept, score in sorted_depts[:3]:  # 最多推薦3個科別
            priority = "high" if score > 0.8 else "medium" if score > 0.5 else "low"

            # 判斷推薦原因
            reasons = []
            for weight in symptom_weights:
                if weight.category in self.DEPARTMENT_MAPPING:
                    if dept in self.DEPARTMENT_MAPPING[weight.category]:
                        reasons.append(weight.symptom)

            recommendations.append(DepartmentRecommendation(
                name=dept,
                priority=priority,
                reason=f"根據症狀：{', '.join(reasons[:2])}"
            ))

        # 如果沒有特定推薦，預設家醫科
        if not recommendations:
            recommendations.append(DepartmentRecommendation(
                name="家醫科",
                priority="medium",
                reason="一般症狀評估"
            ))

        return recommendations

    def aggregate_severity_score(self, symptom_weights: List[SymptomWeight]) -> float:
        """聚合嚴重度分數"""
        if not symptom_weights:
            return 0.0

        # 去重相似症狀 - 取同類別最高權重
        category_max = {}
        for w in symptom_weights:
            if w.category not in category_max or w.weight > category_max[w.category]:
                category_max[w.category] = w.weight

        # 取最高權重作為主要分數
        max_weight = max(category_max.values())

        # 考慮多類別症狀的組合影響
        unique_categories = len(category_max)
        if unique_categories > 1:
            count_factor = min((unique_categories - 1) * 0.05, 0.15)  # 最多增加0.15
        else:
            count_factor = 0

        # 考慮高危症狀組合
        has_multiple_severe = sum(1 for weight in category_max.values() if weight > 0.8) >= 2
        combination_bonus = 0.1 if has_multiple_severe else 0

        return min(max_weight + count_factor + combination_bonus, 1.0)

    def enhanced_triage(self, query: SymptomQuery) -> TriageResult:
        """執行增強分診"""
        # 分析症狀
        detected_symptoms = analyze_symptoms(query.symptom_text)

        # 如果沒有檢測到症狀
        if not detected_symptoms and query.symptom_text:
            # 檢查是否有模糊描述
            if any(word in query.symptom_text for word in ["不舒服", "不適", "怪怪的"]):
                detected_symptoms = ["一般不適"]
            # 特殊處理：喉嚨症狀
            elif "喉嚨" in query.symptom_text and any(word in query.symptom_text for word in ["癢", "不適", "有點"]):
                detected_symptoms = ["喉嚨不適"]

        # 空症狀處理
        if not detected_symptoms:
            return TriageResult(
                level=TriageLevel.SELF_CARE,
                advice="請描述您的症狀，以便我們提供適當的建議。",
                detected_symptoms=[],
                next_steps=["請詳細描述您的不適症狀", "記錄症狀發生的時間和情況"],
                disclaimer=get_disclaimer(),
                emergency_numbers=get_emergency_numbers(),
                confidence_score=0.1
            )

        # 計算症狀權重
        symptom_weights = self.calculate_symptom_weights(detected_symptoms)

        # 聚合嚴重度
        severity_score = self.aggregate_severity_score(symptom_weights)

        # 調整因素
        age_factor = self._calculate_age_factor(query.age)
        chronic_factor = 1.2 if query.has_chronic_disease else 1.0
        duration_factor = self._calculate_duration_factor(query.duration_hours)

        # 最終分數
        final_score = min(severity_score * age_factor * chronic_factor * duration_factor, 1.0)

        # 判定等級
        if final_score > 0.85 or any(w.weight > 0.9 for w in symptom_weights):
            level = TriageLevel.EMERGENCY
        elif final_score > 0.7:
            level = TriageLevel.URGENT if final_score > 0.8 else TriageLevel.OUTPATIENT
        else:
            level = TriageLevel.SELF_CARE

        # 生成建議
        advice = self._generate_advice(level, detected_symptoms, final_score)
        next_steps = self._generate_next_steps(level)

        # 科別推薦
        dept_recommendations = self.recommend_departments(symptom_weights)
        recommended_departments = [d.name for d in dept_recommendations]

        # 建構結果
        result = TriageResult(
            level=level,
            advice=advice,
            detected_symptoms=detected_symptoms,
            next_steps=next_steps,
            disclaimer=get_disclaimer(),
            emergency_numbers=get_emergency_numbers(),
            recommended_departments=recommended_departments,
            confidence_score=final_score
        )

        return result

    def _calculate_age_factor(self, age: Optional[int]) -> float:
        """計算年齡因素"""
        if age is None:
            return 1.0

        if age < 5 or age > 65:
            return 1.2  # 幼童和高齡風險較高
        elif age < 18 or age > 55:
            return 1.1  # 青少年和中老年稍高
        else:
            return 1.0  # 成年人標準

    def _calculate_duration_factor(self, duration_hours: Optional[int]) -> float:
        """計算持續時間因素"""
        if duration_hours is None:
            return 1.0

        if duration_hours <= 2:
            return 1.1  # 急性症狀
        elif duration_hours <= 24:
            return 1.0  # 一天內
        elif duration_hours <= 72:
            return 0.95  # 三天內
        else:
            return 0.9  # 慢性症狀

    def _generate_advice(self, level: TriageLevel, symptoms: List[str], score: float) -> str:
        """生成建議"""
        if level == TriageLevel.EMERGENCY:
            return (
                f"🆘 緊急狀況！您的症狀（{', '.join(symptoms[:2])}）需要立即醫療處理。\n"
                "請立即撥打119或前往最近的急診室。"
            )
        elif level == TriageLevel.URGENT:
            return (
                f"您的症狀（{', '.join(symptoms[:2])}）需要盡快就醫。\n"
                "建議您在今天內前往醫院急診或門診。"
            )
        elif level == TriageLevel.OUTPATIENT:
            return (
                f"您的症狀（{', '.join(symptoms[:2])}）建議門診就醫。\n"
                "請攜帶健保卡預約相關科別門診。"
            )
        else:
            return (
                "目前症狀較輕微，可先自我照護觀察。\n"
                "建議充足休息、多喝水，若症狀持續或惡化，請就醫評估。"
            )

    def _generate_next_steps(self, level: TriageLevel) -> List[str]:
        """生成下一步驟"""
        if level == TriageLevel.EMERGENCY:
            return [
                "立即撥打119",
                "保持冷靜，勿移動傷患",
                "準備健保卡和身份證件",
                "記錄症狀開始時間",
                "通知家人陪同"
            ]
        elif level == TriageLevel.URGENT:
            return [
                "盡快前往急診或門診",
                "攜帶健保卡與相關藥物",
                "記錄症狀變化",
                "避免駕駛，請人陪同"
            ]
        elif level == TriageLevel.OUTPATIENT:
            return [
                "預約門診就醫",
                "準備健保卡",
                "記錄症狀日誌",
                "避免自行用藥"
            ]
        else:
            return [
                "充足休息",
                "補充水分",
                "觀察症狀變化",
                "若惡化請就醫"
            ]


# 保留原有的類別以確保相容性
class EnhancedTriageEngine(EnhancedTriageSystem):
    """增強版症狀分級引擎（相容性別名）"""

    def assess(self, query: SymptomQuery) -> TriageResult:
        """執行症狀評估（相容性方法）"""
        return self.enhanced_triage(query)


class EmergencyIntegration:
    """緊急號碼整合服務"""

    def get_emergency_numbers(self) -> List[str]:
        """取得台灣緊急號碼"""
        return ["119", "110", "112"]

    def get_emergency_info(self) -> Dict[str, Dict[str, str]]:
        """取得緊急號碼詳細資訊"""
        return {
            "119": {
                "description": "緊急醫療救護",
                "usage": "醫療緊急狀況、火災、救難",
                "available": "24小時"
            },
            "110": {
                "description": "警察報案",
                "usage": "交通事故、犯罪、公共安全",
                "available": "24小時"
            },
            "112": {
                "description": "手機緊急號碼",
                "usage": "手機無訊號時緊急撥打",
                "available": "24小時"
            }
        }

    def get_emergency_guidance(self, symptom: str) -> Dict[str, Any]:
        """根據症狀提供緊急指引"""
        guidance = {
            "immediate_action": True,
            "call_priority": "119",
            "pre_call_checklist": [
                "保持冷靜",
                "確認位置地址",
                "準備健保卡",
                "記住症狀開始時間",
                "若有藥物過敏請告知"
            ]
        }

        if "交通事故" in symptom or "車禍" in symptom:
            guidance["call_priority"] = "110"
            guidance["secondary_call"] = "119"

        return guidance


class MultiLanguageProcessor:
    """多語言處理器（保留相容性）"""

    def process_input(self, text: str) -> str:
        """處理輸入文字"""
        return text

    def extract_symptoms(self, text: str) -> List[str]:
        """提取症狀"""
        from app.domain.rules_tw import analyze_symptoms

        # 先轉換英文症狀為中文
        english_to_chinese = {
            "chest pain": "胸痛",
            "difficulty breathing": "呼吸困難",
            "breathing difficulty": "呼吸困難",
            "headache": "頭痛",
            "fever": "發燒",
            "nausea": "噁心",
            "vomiting": "嘔吐",
            "abdominal pain": "腹痛",
            "stomach pain": "腹痛",
            "dizziness": "頭暈",
            "fatigue": "疲倦"
        }

        # 轉換英文症狀
        converted_text = text
        detected_english = []
        for eng, chi in english_to_chinese.items():
            if eng.lower() in text.lower():
                converted_text = converted_text.replace(eng, chi)
                detected_english.append(chi)

        # 分析轉換後的文字
        symptoms = analyze_symptoms(converted_text)

        # 合併英文檢測到的症狀
        all_symptoms = list(set(symptoms + detected_english))

        return all_symptoms

    def convert_to_traditional(self, text: str) -> str:
        """簡體轉繁體"""
        # 基本轉換
        replacements = {
            "头痛": "頭痛",
            "发烧": "發燒"
        }
        for simplified, traditional in replacements.items():
            text = text.replace(simplified, traditional)
        return text


class SymptomHistoryTracker:
    """症狀歷史追蹤器（保留相容性）"""

    def __init__(self):
        self.history = {}

    def add_assessment(self, assessment: Dict[str, Any]) -> None:
        """新增評估記錄"""
        session_id = assessment.get('session_id', 'default')
        if session_id not in self.history:
            self.history[session_id] = []
        self.history[session_id].append(assessment)

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """取得歷史記錄"""
        return self.history.get(session_id, [])

    def detect_pattern(self, session_id: str) -> Dict[str, Any]:
        """偵測症狀模式"""
        history = self.get_history(session_id)

        if len(history) < 2:
            return {"trend": "insufficient_data", "alert": False}

        # 簡單的惡化偵測
        if len(history) >= 2:
            last_level = history[-1].get('level')
            prev_level = history[-2].get('level')

            if last_level == TriageLevel.EMERGENCY and prev_level != TriageLevel.EMERGENCY:
                return {
                    "trend": "worsening",
                    "alert": True,
                    "message": "症狀惡化",
                    "recurring": False,
                    "recurring_symptoms": []
                }

        # 檢查重複症狀
        all_symptoms = []
        for h in history:
            all_symptoms.extend(h.get('symptoms', []))

        from collections import Counter
        symptom_counts = Counter(all_symptoms)
        recurring = [s for s, count in symptom_counts.items() if count >= 3]

        result = {
            "trend": "stable",
            "alert": False,
            "recurring": len(recurring) > 0,
            "recurring_symptoms": recurring
        }

        if "偏頭痛" in recurring:
            result["recommendation"] = "建議神經內科檢查"

        return result


class DepartmentRecommender:
    """科別推薦服務（保留相容性）"""

    def __init__(self):
        self.departments = [
            "家醫科", "內科", "外科", "婦產科", "小兒科",
            "急診", "心臟內科", "胸腔內科", "腸胃內科",
            "神經內科", "耳鼻喉科", "眼科", "皮膚科",
            "精神科", "復健科", "骨科"
        ]

    def recommend_departments(self, symptoms: List[str], is_emergency: bool = False) -> List[str]:
        """推薦科別"""
        if is_emergency:
            return ["急診"]

        # 使用新系統的推薦邏輯
        system = EnhancedTriageSystem()
        weights = system.calculate_symptom_weights(symptoms)
        recommendations = system.recommend_departments(weights)

        return [r.name for r in recommendations]

    def recommend_with_priority(self, symptoms: List[str]) -> List[Dict[str, Any]]:
        """帶優先級的推薦"""
        system = EnhancedTriageSystem()
        weights = system.calculate_symptom_weights(symptoms)
        recommendations = system.recommend_departments(weights)

        return [
            {
                "department": r.name,
                "priority": 1.0 if r.priority == "high" else 0.5,
                "reason": r.reason
            }
            for r in recommendations
        ]

    def get_all_departments(self) -> List[str]:
        """取得所有科別"""
        return self.departments.copy()