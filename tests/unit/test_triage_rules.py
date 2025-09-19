"""
症狀分級規則測試
測試重點：
- 關鍵症狀（胸痛、呼吸困難、麻痺、劇烈頭痛）→ level="emergency" + 119指引
- 輕症（喉嚨痛、流鼻水）→ level="self-care" + 觀察期指引
- 所有輸出必須為繁體中文
- 必須包含免責聲明與急救提醒
"""

import pytest
from app.domain.models import SymptomQuery, TriageResult, TriageLevel
from app.domain.rules_tw import analyze_symptoms, get_emergency_keywords, get_mild_keywords
from app.domain.triage import rule_triage


class TestTriageRules:
    """症狀分級規則測試類別"""

    def test_emergency_chest_pain(self):
        """測試胸痛緊急症狀"""
        query = SymptomQuery(symptom_text="我胸口很痛，喘不過氣")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert "急診" in result.advice
        assert "胸痛" in result.detected_symptoms
        assert result.disclaimer is not None
        assert "本系統僅" in result.disclaimer

    def test_emergency_breathing_difficulty(self):
        """測試呼吸困難緊急症狀"""
        query = SymptomQuery(symptom_text="呼吸困難，快喘不過氣了")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert "呼吸困難" in result.detected_symptoms
        assert len(result.next_steps) > 0
        assert any("保持冷靜" in step for step in result.next_steps)

    def test_emergency_paralysis(self):
        """測試麻痺症狀"""
        query = SymptomQuery(symptom_text="左半邊身體突然麻痺無力")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert "麻痺" in result.detected_symptoms

    def test_emergency_severe_headache(self):
        """測試劇烈頭痛"""
        query = SymptomQuery(symptom_text="頭痛到快爆炸了，從來沒這麼痛過")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        # 檢查是否有頭痛相關症狀
        assert any("頭痛" in s for s in result.detected_symptoms)

    def test_emergency_unconscious(self):
        """測試意識不清"""
        query = SymptomQuery(symptom_text="家人昏迷不醒")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert "昏迷" in result.detected_symptoms

    def test_emergency_severe_bleeding(self):
        """測試大量出血"""
        query = SymptomQuery(symptom_text="手臂受傷大量出血")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert "大量出血" in result.detected_symptoms

    def test_mild_sore_throat(self):
        """測試輕症喉嚨痛"""
        query = SymptomQuery(symptom_text="喉嚨有點痛，吞口水不舒服")
        result = rule_triage(query)

        assert result.level == TriageLevel.SELF_CARE
        # 檢查是否有喉嚨痛相關症狀（可能是"喉嚨痛"或"喉嚨有點痛"）
        assert any("喉嚨" in symptom and "痛" in symptom for symptom in result.detected_symptoms)
        assert "休息" in result.advice or "觀察" in result.advice
        assert any("如果症狀" in step for step in result.next_steps)

    def test_mild_runny_nose(self):
        """測試輕症流鼻水"""
        query = SymptomQuery(symptom_text="流鼻水，有點鼻塞")
        result = rule_triage(query)

        assert result.level == TriageLevel.SELF_CARE
        assert "流鼻水" in result.detected_symptoms or "鼻塞" in result.detected_symptoms
        assert "休息" in result.advice
        assert result.disclaimer is not None

    def test_mild_cough(self):
        """測試輕症咳嗽"""
        query = SymptomQuery(symptom_text="有點咳嗽，沒有發燒")
        result = rule_triage(query)

        assert result.level == TriageLevel.SELF_CARE
        assert "咳嗽" in result.detected_symptoms
        assert any("觀察" in text for text in [result.advice] + result.next_steps)

    def test_moderate_fever(self):
        """測試中度症狀發燒"""
        query = SymptomQuery(symptom_text="發燒38.5度，全身痠痛")
        result = rule_triage(query)

        assert result.level == TriageLevel.OUTPATIENT
        assert "發燒" in result.detected_symptoms
        assert "門診" in result.advice or "就醫" in result.advice

    def test_moderate_persistent_symptoms(self):
        """測試持續性症狀"""
        query = SymptomQuery(symptom_text="頭痛三天了，吃藥沒改善")
        result = rule_triage(query)

        # 因為有"三天"關鍵字，應該建議就醫
        assert result.level in [TriageLevel.OUTPATIENT, TriageLevel.SELF_CARE]
        assert "頭痛" in result.detected_symptoms

    def test_multiple_emergency_symptoms(self):
        """測試多重緊急症狀"""
        query = SymptomQuery(symptom_text="胸痛又呼吸困難，冒冷汗")
        result = rule_triage(query)

        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice
        assert len(result.detected_symptoms) >= 2
        assert "胸痛" in result.detected_symptoms
        assert "呼吸困難" in result.detected_symptoms

    def test_mixed_symptoms_emergency_priority(self):
        """測試混合症狀時緊急優先"""
        query = SymptomQuery(symptom_text="喉嚨痛、流鼻水，還有胸痛")
        result = rule_triage(query)

        # 即使有輕症，但有胸痛應該是緊急
        assert result.level == TriageLevel.EMERGENCY
        assert "119" in result.advice

    def test_all_results_have_disclaimer(self):
        """測試所有結果都有免責聲明"""
        test_cases = [
            "胸痛",
            "流鼻水",
            "發燒",
            "頭暈"
        ]

        for symptom in test_cases:
            query = SymptomQuery(symptom_text=symptom)
            result = rule_triage(query)

            assert result.disclaimer is not None
            assert len(result.disclaimer) > 0
            assert "參考" in result.disclaimer or "不能取代" in result.disclaimer

    def test_all_emergency_have_119_reminder(self):
        """測試所有緊急狀況都有119提醒"""
        emergency_symptoms = [
            "胸痛", "呼吸困難", "昏迷", "大量出血",
            "麻痺", "劇烈頭痛", "中風"
        ]

        for symptom in emergency_symptoms:
            query = SymptomQuery(symptom_text=symptom)
            result = rule_triage(query)

            if result.level == TriageLevel.EMERGENCY:
                assert "119" in result.advice
                assert result.emergency_numbers is not None
                assert "119" in result.emergency_numbers

    def test_get_emergency_keywords(self):
        """測試緊急關鍵字列表"""
        keywords = get_emergency_keywords()

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "胸痛" in keywords
        assert "呼吸困難" in keywords
        assert "昏迷" in keywords

    def test_get_mild_keywords(self):
        """測試輕症關鍵字列表"""
        keywords = get_mild_keywords()

        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert "流鼻水" in keywords
        assert "喉嚨痛" in keywords

    def test_analyze_symptoms_function(self):
        """測試症狀分析函數"""
        detected = analyze_symptoms("我胸口痛，還有點咳嗽")

        assert isinstance(detected, list)
        assert len(detected) > 0
        assert any("胸" in s for s in detected)
        assert "咳嗽" in detected

    def test_empty_symptom_text(self):
        """測試空症狀文字"""
        query = SymptomQuery(symptom_text=" ")  # 空白字串
        result = rule_triage(query)

        assert result.level == TriageLevel.SELF_CARE
        assert "請描述" in result.advice
        assert result.disclaimer is not None

    def test_vague_symptoms(self):
        """測試模糊症狀描述"""
        query = SymptomQuery(symptom_text="不舒服")
        result = rule_triage(query)

        assert result.level == TriageLevel.SELF_CARE
        assert "觀察" in result.advice or "休息" in result.advice
        assert len(result.next_steps) > 0

    def test_recommended_departments(self):
        """測試推薦科別"""
        query = SymptomQuery(symptom_text="胸痛")
        result = rule_triage(query)

        assert result.recommended_departments is not None
        assert len(result.recommended_departments) > 0
        assert "急診" in result.recommended_departments or "心臟內科" in result.recommended_departments

    def test_confidence_score(self):
        """測試信心分數"""
        query = SymptomQuery(symptom_text="發燒")
        result = rule_triage(query)

        assert result.confidence_score is not None
        assert 0.0 <= result.confidence_score <= 1.0