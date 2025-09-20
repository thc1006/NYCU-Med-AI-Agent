"""增強版症狀分級測試案例
符合台灣醫療規範與緊急號碼整合
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from app.domain.models import (
    SymptomQuery,
    TriageResult,
    TriageLevel,
    TriageRequest
)
from app.domain.enhanced_triage import (
    EnhancedTriageEngine,
    EmergencyIntegration,
    MultiLanguageProcessor,
    SymptomHistoryTracker,
    DepartmentRecommender
)


class TestEnhancedTriageEngine:
    """增強版症狀分級引擎測試"""

    @pytest.fixture
    def engine(self):
        return EnhancedTriageEngine()

    def test_red_flag_symptoms_trigger_emergency(self, engine):
        """測試：紅旗症狀必須立即觸發緊急等級"""
        # Given - 紅旗症狀輸入
        red_flag_symptoms = [
            "胸痛",
            "呼吸困難",
            "意識不清",
            "大量出血",
            "突然麻痺",
            "自殺意念"
        ]

        for symptom in red_flag_symptoms:
            query = SymptomQuery(symptom_text=symptom)

            # When - 執行分級
            result = engine.assess(query)

            # Then - 必須是緊急等級
            assert result.level == TriageLevel.EMERGENCY
            assert "119" in result.emergency_numbers
            assert "立即" in result.advice or "緊急" in result.advice
            assert result.confidence_score >= 0.8  # 紅旗高信心度

    def test_mild_symptoms_self_care(self, engine):
        """測試：輕微症狀應該分級為自我照護"""
        # Given - 輕微症狀
        mild_symptoms = [
            "流鼻水有點鼻塞",
            "喉嚨有點癢",
            "輕微頭痛",
            "有點疲倦"
        ]

        for symptom in mild_symptoms:
            query = SymptomQuery(symptom_text=symptom)
            
            # When
            result = engine.assess(query)
            
            # Then
            assert result.level == TriageLevel.SELF_CARE
            assert "自我照護" in result.advice or "休息" in result.advice
            assert result.emergency_numbers  # 始終提供緊急號碼

    def test_moderate_symptoms_outpatient(self, engine):
        """測試：中度症狀應建議門診就醫"""
        # Given
        moderate_symptoms = [
            "發高燒39度",
            "持續腹痛兩天",
            "反覆嘔吐",
            "血尿"
        ]

        for symptom in moderate_symptoms:
            query = SymptomQuery(symptom_text=symptom)
            
            # When
            result = engine.assess(query)
            
            # Then
            assert result.level == TriageLevel.OUTPATIENT
            assert "門診" in result.advice or "就醫" in result.advice

    def test_disclaimer_must_exist(self, engine):
        """測試：所有回應必須包含免責聲明"""
        # Given
        query = SymptomQuery(symptom_text="頭痛")
        
        # When
        result = engine.assess(query)
        
        # Then
        assert result.disclaimer
        assert "僅供參考" in result.disclaimer
        assert "非醫療診斷" in result.disclaimer
        assert "專業醫療" in result.disclaimer


class TestEmergencyIntegration:
    """緊急號碼整合測試"""

    @pytest.fixture
    def integration(self):
        return EmergencyIntegration()

    def test_taiwan_emergency_numbers(self, integration):
        """測試：必須包含正確的台灣緊急號碼"""
        # When
        numbers = integration.get_emergency_numbers()
        
        # Then
        assert "119" in numbers
        assert "110" in numbers
        assert "112" in numbers

    def test_emergency_numbers_with_description(self, integration):
        """測試：緊急號碼必須有中文說明"""
        # When
        info = integration.get_emergency_info()
        
        # Then
        assert info["119"]["description"] == "緊急醫療救護"
        assert info["110"]["description"] == "警察報案"
        assert info["112"]["description"] == "手機緊急號碼"

    def test_red_flag_triggers_emergency_guidance(self, integration):
        """測試：紅旗症狀必須觸發完整緊急指引"""
        # Given
        red_flag = "胸痛"
        
        # When
        guidance = integration.get_emergency_guidance(red_flag)
        
        # Then
        assert guidance["immediate_action"]  # 立即行動
        assert guidance["call_priority"] == "119"  # 優先撥打119
        assert guidance["pre_call_checklist"]  # 撥打前檢查清單
        assert "保持冷靜" in guidance["pre_call_checklist"]
        assert "準備健保卡" in guidance["pre_call_checklist"]


class TestMultiLanguageProcessor:
    """多語言處理測試"""

    @pytest.fixture
    def processor(self):
        return MultiLanguageProcessor()

    def test_traditional_chinese_symptom_recognition(self, processor):
        """測試：正確識別繁體中文症狀"""
        # Given
        text = "我胸口很痛而且呼吸困難"
        
        # When
        symptoms = processor.extract_symptoms(text)
        
        # Then
        assert "胸痛" in symptoms
        assert "呼吸困難" in symptoms

    def test_simplified_chinese_conversion(self, processor):
        """測試：簡體中文自動轉換為繁體"""
        # Given
        simplified = "头痛发烧"
        
        # When
        converted = processor.convert_to_traditional(simplified)
        symptoms = processor.extract_symptoms(converted)
        
        # Then
        assert "頭痛" in symptoms
        assert "發燒" in symptoms

    def test_english_symptom_recognition(self, processor):
        """測試：識別英文症狀描述"""
        # Given
        text = "chest pain and difficulty breathing"
        
        # When
        symptoms = processor.extract_symptoms(text)
        
        # Then
        assert "chest pain" in symptoms or "胸痛" in symptoms
        assert "difficulty breathing" in symptoms or "呼吸困難" in symptoms

    def test_mixed_language_processing(self, processor):
        """測試：處理中英混合輸入"""
        # Given
        mixed = "我有chest pain還有發燒fever"
        
        # When
        symptoms = processor.extract_symptoms(mixed)
        
        # Then
        assert len(symptoms) >= 2
        assert any("chest" in s or "胸" in s for s in symptoms)
        assert any("燒" in s or "fever" in s for s in symptoms)


class TestSymptomHistoryTracker:
    """症狀歷史追蹤測試"""

    @pytest.fixture
    def tracker(self):
        return SymptomHistoryTracker()

    def test_symptom_record_storage(self, tracker):
        """測試：正確存儲症狀評估記錄"""
        # Given
        assessment = {
            "timestamp": datetime.now(timezone.utc),
            "symptoms": ["頭痛", "發燒"],
            "level": TriageLevel.OUTPATIENT,
            "session_id": "test-123"
        }
        
        # When
        tracker.add_assessment(assessment)
        history = tracker.get_history("test-123")
        
        # Then
        assert len(history) == 1
        assert history[0]["symptoms"] == ["頭痛", "發燒"]

    def test_symptom_worsening_detection(self, tracker):
        """測試：偵測症狀惡化模式"""
        # Given - 症狀逐漸惡化
        tracker.add_assessment({
            "timestamp": datetime.now(timezone.utc),
            "symptoms": ["輕微頭痛"],
            "level": TriageLevel.SELF_CARE,
            "session_id": "test-456"
        })
        
        tracker.add_assessment({
            "timestamp": datetime.now(timezone.utc),
            "symptoms": ["劇烈頭痛", "嘔吐"],
            "level": TriageLevel.EMERGENCY,
            "session_id": "test-456"
        })
        
        # When
        pattern = tracker.detect_pattern("test-456")
        
        # Then
        assert pattern["trend"] == "worsening"
        assert pattern["alert"] == True
        assert "症狀惡化" in pattern["message"]

    def test_recurring_symptom_pattern(self, tracker):
        """測試：識別重複出現的症狀"""
        # Given - 重複的症狀
        for i in range(3):
            tracker.add_assessment({
                "timestamp": datetime.now(timezone.utc),
                "symptoms": ["偏頭痛"],
                "level": TriageLevel.OUTPATIENT,
                "session_id": "test-789"
            })
        
        # When
        pattern = tracker.detect_pattern("test-789")
        
        # Then
        assert pattern["recurring"] == True
        assert "偏頭痛" in pattern["recurring_symptoms"]
        assert pattern["recommendation"] == "建議神經內科檢查"


class TestDepartmentRecommender:
    """科別推薦測試"""

    @pytest.fixture
    def recommender(self):
        return DepartmentRecommender()

    def test_symptom_to_department_mapping(self, recommender):
        """測試：症狀正確對應到醫療科別"""
        # Test cases
        test_cases = [
            (["胸痛", "心悸"], ["急診", "心臟內科"]),
            (["咳嗽", "呼吸困難"], ["胸腔內科", "急診"]),
            (["頭痛", "暈眩"], ["神經內科", "家醫科"]),
            (["腹痛", "腹瀉"], ["腸胃內科", "家醫科"]),
            (["發燒", "喉嚨痛"], ["耳鼻喉科", "家醫科", "感染科"])
        ]
        
        for symptoms, expected_depts in test_cases:
            # When
            recommendations = recommender.recommend_departments(symptoms)
            
            # Then
            assert any(dept in recommendations for dept in expected_depts)

    def test_emergency_symptoms_priority(self, recommender):
        """測試：緊急症狀必須優先推薦急診"""
        # Given
        emergency_symptoms = ["胸痛", "意識不清"]
        
        # When
        recommendations = recommender.recommend_departments(
            emergency_symptoms,
            is_emergency=True
        )
        
        # Then
        assert recommendations[0] == "急診"

    def test_department_recommendation_priority(self, recommender):
        """測試：科別推薦必須有優先順序"""
        # Given
        symptoms = ["頭痛", "發燒", "咳嗽"]
        
        # When
        recommendations = recommender.recommend_with_priority(symptoms)
        
        # Then
        assert all("priority" in r for r in recommendations)
        assert all("department" in r for r in recommendations)
        assert all("reason" in r for r in recommendations)
        # 確認按優先級排序
        priorities = [r["priority"] for r in recommendations]
        assert priorities == sorted(priorities, reverse=True)

    def test_taiwan_medical_department_names(self, recommender):
        """測試：使用台灣醫療體系的科別命名"""
        # When
        all_departments = recommender.get_all_departments()
        
        # Then - 確認使用繁體中文台灣慣用名稱
        taiwan_departments = [
            "家醫科", "內科", "外科", "婦產科", "小兒科",
            "急診", "心臟內科", "胸腔內科", "腸胃內科",
            "神經內科", "耳鼻喉科", "眼科", "皮膚科",
            "精神科", "復健科", "骨科"
        ]
        
        for dept in taiwan_departments:
            assert dept in all_departments