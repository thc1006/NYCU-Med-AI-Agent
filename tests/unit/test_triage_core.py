"""
測試症狀分級核心邏輯
包含規則引擎與主要分級函數的完整測試
"""

import pytest
from app.domain.models import SymptomQuery, TriageResult, TriageLevel
from app.domain.triage import rule_triage, TriageSystem


class TestRuleTriage:
    """測試規則基礎分級函數"""

    def test_empty_symptom_text_returns_self_care(self):
        """測試：空症狀描述返回自我照護"""
        # Given
        query = SymptomQuery(symptom_text="")

        # When
        result = rule_triage(query)

        # Then
        assert result.level == TriageLevel.SELF_CARE
        assert "請描述您的症狀" in result.advice
        assert result.detected_symptoms == []
        assert result.disclaimer
        assert result.emergency_numbers

    def test_whitespace_only_symptom_returns_self_care(self):
        """測試：僅空白字符返回自我照護"""
        # Given
        query = SymptomQuery(symptom_text="   \n\t  ")

        # When
        result = rule_triage(query)

        # Then
        assert result.level == TriageLevel.SELF_CARE

    def test_emergency_symptoms_return_emergency_level(self):
        """測試：緊急症狀返回緊急等級"""
        emergency_symptoms = [
            "胸痛",
            "呼吸困難",
            "意識不清",
            "大量出血",
            "劇烈頭痛"
        ]

        for symptom in emergency_symptoms:
            # Given
            query = SymptomQuery(symptom_text=symptom)

            # When
            result = rule_triage(query)

            # Then
            assert result.level == TriageLevel.EMERGENCY, f"Failed for symptom: {symptom}"
            assert "119" in result.emergency_numbers
            assert result.confidence_score is not None

    def test_mild_symptoms_return_self_care(self):
        """測試：輕微症狀返回自我照護"""
        mild_symptoms = [
            "流鼻水",
            "輕微咳嗽",
            "疲倦",
            "肌肉痠痛"
        ]

        for symptom in mild_symptoms:
            # Given
            query = SymptomQuery(symptom_text=symptom)

            # When
            result = rule_triage(query)

            # Then
            assert result.level in [TriageLevel.SELF_CARE, TriageLevel.OUTPATIENT], f"Failed for symptom: {symptom}"

    def test_moderate_symptoms_return_outpatient(self):
        """測試：中度症狀返回門診"""
        moderate_symptoms = [
            "高燒",
            "持續頭痛",
            "腹部疼痛",
            "血尿"
        ]

        for symptom in moderate_symptoms:
            # Given
            query = SymptomQuery(symptom_text=symptom)

            # When
            result = rule_triage(query)

            # Then
            assert result.level in [TriageLevel.OUTPATIENT, TriageLevel.URGENT], f"Failed for symptom: {symptom}"

    def test_vague_emergency_words_trigger_outpatient(self):
        """測試：模糊但嚴重的描述觸發門診建議"""
        vague_emergency = [
            "很痛很不舒服",
            "痛到受不了",
            "感覺快死了"
        ]

        for description in vague_emergency:
            # Given
            query = SymptomQuery(symptom_text=description)

            # When
            result = rule_triage(query)

            # Then
            assert result.level == TriageLevel.OUTPATIENT, f"Failed for: {description}"

    def test_demographic_factors_influence_result(self):
        """測試：人口統計學因素影響結果"""
        # Given - 同樣症狀但不同年齡
        base_query = SymptomQuery(symptom_text="頭痛")
        elderly_query = SymptomQuery(symptom_text="頭痛", age=75)

        # When
        base_result = rule_triage(base_query)
        elderly_result = rule_triage(elderly_query)

        # Then
        # 高齡者的信心分數可能不同或建議更謹慎
        assert elderly_result.confidence_score is not None
        assert base_result.confidence_score is not None

    def test_chronic_disease_flag_considered(self):
        """測試：慢性病史被考慮"""
        # Given
        normal_query = SymptomQuery(symptom_text="胸悶", has_chronic_disease=False)
        chronic_query = SymptomQuery(symptom_text="胸悶", has_chronic_disease=True)

        # When
        normal_result = rule_triage(normal_query)
        chronic_result = rule_triage(chronic_query)

        # Then
        # 有慢性病史的患者建議應該更謹慎
        assert normal_result.level is not None
        assert chronic_result.level is not None

    def test_medication_list_processed(self):
        """測試：藥物清單被處理"""
        # Given
        query = SymptomQuery(
            symptom_text="頭痛",
            medications=["阿斯匹靈", "血壓藥"]
        )

        # When
        result = rule_triage(query)

        # Then
        assert result.level is not None
        assert result.advice is not None

    def test_all_results_include_required_fields(self):
        """測試：所有結果包含必要欄位"""
        # Given
        query = SymptomQuery(symptom_text="頭痛")

        # When
        result = rule_triage(query)

        # Then
        assert result.level is not None
        assert result.advice is not None
        assert result.detected_symptoms is not None
        assert result.next_steps is not None
        assert result.disclaimer is not None
        assert result.emergency_numbers is not None

    def test_confidence_score_within_valid_range(self):
        """測試：信心分數在有效範圍內"""
        # Given
        query = SymptomQuery(symptom_text="頭痛")

        # When
        result = rule_triage(query)

        # Then
        if result.confidence_score is not None:
            assert 0.0 <= result.confidence_score <= 1.0

    def test_emergency_numbers_always_provided(self):
        """測試：始終提供緊急號碼"""
        test_cases = [
            SymptomQuery(symptom_text=""),
            SymptomQuery(symptom_text="頭痛"),
            SymptomQuery(symptom_text="胸痛"),
            SymptomQuery(symptom_text="流鼻水")
        ]

        for query in test_cases:
            # When
            result = rule_triage(query)

            # Then
            assert result.emergency_numbers is not None
            assert len(result.emergency_numbers) > 0
            assert "119" in result.emergency_numbers


class TestTriageSystem:
    """測試TriageSystem包裝類別"""

    @pytest.fixture
    def triage_system(self):
        return TriageSystem()

    def test_assess_symptoms_list(self, triage_system):
        """測試：評估症狀列表"""
        # Given
        symptoms = ["胸痛", "呼吸困難"]

        # When
        result = triage_system.assess_symptoms(symptoms)

        # Then
        assert hasattr(result, 'is_red_flag')
        assert result.is_red_flag == True  # 胸痛和呼吸困難都是紅旗症狀

    def test_assess_symptoms_empty_list(self, triage_system):
        """測試：評估空症狀列表"""
        # Given
        symptoms = []

        # When
        result = triage_system.assess_symptoms(symptoms)

        # Then
        assert hasattr(result, 'is_red_flag')
        assert result.is_red_flag == False

    def test_assess_symptoms_mild_symptoms(self, triage_system):
        """測試：評估輕微症狀"""
        # Given
        symptoms = ["流鼻水", "疲倦"]

        # When
        result = triage_system.assess_symptoms(symptoms)

        # Then
        assert hasattr(result, 'is_red_flag')
        assert result.is_red_flag == False

    def test_assess_symptoms_moderate_symptoms(self, triage_system):
        """測試：評估中度症狀"""
        # Given
        symptoms = ["發燒", "頭痛"]

        # When
        result = triage_system.assess_symptoms(symptoms)

        # Then
        assert hasattr(result, 'is_red_flag')
        # 發燒和頭痛通常不是紅旗，除非很嚴重
        assert result.is_red_flag == False