"""
症狀分級主要邏輯
整合規則引擎與（可選）LLM增強
"""

from typing import Optional, List, Dict, Any
from app.domain.models import SymptomQuery, TriageResult, TriageLevel
from app.domain.rules_tw import (
    analyze_symptoms,
    determine_triage_level,
    get_emergency_advice,
    get_emergency_next_steps,
    get_outpatient_advice,
    get_outpatient_next_steps,
    get_self_care_advice,
    get_self_care_next_steps,
    get_disclaimer,
    get_emergency_numbers,
    get_recommended_departments
)


def rule_triage(query: SymptomQuery) -> TriageResult:
    """
    基於規則的症狀分級

    Args:
        query: 症狀查詢

    Returns:
        TriageResult: 分級結果
    """
    # 處理空症狀文字
    if not query.symptom_text or not query.symptom_text.strip():
        return TriageResult(
            level=TriageLevel.SELF_CARE,
            advice="請描述您的症狀，以便我們提供適當的建議。",
            detected_symptoms=[],
            next_steps=["請詳細描述您的不適症狀", "記錄症狀發生的時間和情況"],
            disclaimer=get_disclaimer(),
            emergency_numbers=get_emergency_numbers()
        )

    # 分析症狀
    detected_symptoms = analyze_symptoms(query.symptom_text)

    # 如果沒有檢測到已知症狀，但有描述
    if not detected_symptoms and len(query.symptom_text) > 0:
        # 檢查是否有模糊但可能重要的描述
        vague_emergency_words = ["很痛", "很不舒服", "很嚴重", "受不了", "快死"]
        text_lower = query.symptom_text.lower()

        for word in vague_emergency_words:
            if word in text_lower:
                detected_symptoms.append("嚴重不適")
                break

        if not detected_symptoms:
            detected_symptoms.append("一般不適")

    # 判斷分級等級
    level = determine_triage_level(detected_symptoms)

    # 根據等級生成建議
    if level == TriageLevel.EMERGENCY:
        advice = get_emergency_advice()
        next_steps = get_emergency_next_steps()
        emergency_numbers = get_emergency_numbers()
    elif level == TriageLevel.OUTPATIENT:
        advice = get_outpatient_advice()
        next_steps = get_outpatient_next_steps()
        emergency_numbers = get_emergency_numbers()
    else:  # SELF_CARE
        advice = get_self_care_advice()
        next_steps = get_self_care_next_steps()
        emergency_numbers = get_emergency_numbers()

    # 取得推薦科別
    recommended_departments = get_recommended_departments(detected_symptoms)

    # 建構結果
    result = TriageResult(
        level=level,
        advice=advice,
        detected_symptoms=detected_symptoms,
        next_steps=next_steps,
        disclaimer=get_disclaimer(),
        emergency_numbers=emergency_numbers,
        recommended_departments=recommended_departments,
        confidence_score=0.8  # 規則基礎的信心分數
    )

    return result


def combine_with_llm(rule_result: TriageResult, llm_result: Optional[TriageResult]) -> TriageResult:
    """
    結合規則結果與LLM結果

    Args:
        rule_result: 規則引擎的結果
        llm_result: LLM的結果（可選）

    Returns:
        TriageResult: 合併後的結果

    Note:
        - 緊急等級以較高者為準（安全優先）
        - 建議內容結合兩者
        - 症狀列表合併去重
    """
    if not llm_result:
        return rule_result

    # 安全優先：選擇較高的緊急等級
    level_priority = {
        TriageLevel.EMERGENCY: 4,
        TriageLevel.URGENT: 3,
        TriageLevel.OUTPATIENT: 2,
        TriageLevel.SELF_CARE: 1
    }

    final_level = rule_result.level
    if level_priority.get(llm_result.level, 0) > level_priority.get(rule_result.level, 0):
        final_level = llm_result.level

    # 如果LLM判斷為緊急但規則沒有，採用規則的緊急建議
    if final_level == TriageLevel.EMERGENCY:
        advice = get_emergency_advice()
        next_steps = get_emergency_next_steps()
    else:
        # 結合建議（優先顯示規則建議）
        advice = rule_result.advice
        if llm_result.advice and llm_result.advice != rule_result.advice:
            advice += f"\n\n額外建議：{llm_result.advice}"

        # 合併下一步驟
        next_steps = list(rule_result.next_steps)
        if llm_result.next_steps:
            for step in llm_result.next_steps:
                if step not in next_steps:
                    next_steps.append(step)

    # 合併檢測到的症狀
    all_symptoms = list(set(rule_result.detected_symptoms + (llm_result.detected_symptoms or [])))

    # 合併推薦科別
    all_departments = list(set(
        (rule_result.recommended_departments or []) +
        (llm_result.recommended_departments or [])
    ))

    # 計算綜合信心分數
    rule_confidence = rule_result.confidence_score or 0.8
    llm_confidence = llm_result.confidence_score or 0.7
    combined_confidence = (rule_confidence * 0.6 + llm_confidence * 0.4)

    return TriageResult(
        level=final_level,
        advice=advice,
        detected_symptoms=all_symptoms,
        next_steps=next_steps[:6],  # 限制步驟數量
        disclaimer=get_disclaimer(),
        emergency_numbers=get_emergency_numbers(),
        recommended_departments=all_departments[:3],  # 限制推薦科別數量
        confidence_score=combined_confidence
    )


def triage_with_fallback(query: SymptomQuery) -> Dict[str, Any]:
    """
    症狀分級（含降級機制）

    始終返回結果，即使 LLM 失敗也能提供基本規則判斷

    Args:
        query: 症狀查詢

    Returns:
        包含分級結果與狀態的字典
    """
    try:
        # 嘗試完整分級（含可能的 LLM 增強）
        result = rule_triage(query)
        return {
            "status": "ok",
            "analysis_mode": "rules_only",  # 目前只有規則
            "triage_result": result
        }
    except Exception as e:
        # 降級為最基本的規則判斷
        detected = analyze_symptoms(query.symptom_text)
        level = determine_triage_level(detected)

        # 建立最小可用回應
        basic_result = TriageResult(
            level=level,
            advice=get_advice_for_level(level),
            detected_symptoms=detected,
            next_steps=["如症狀持續或惡化請就醫"],
            disclaimer=get_disclaimer(),
            emergency_numbers=get_emergency_numbers() if level == TriageLevel.EMERGENCY else [],
            confidence_score=0.5  # 低信心分數
        )

        return {
            "status": "degraded",
            "analysis_mode": "basic_rules",
            "service_notice": "服務降級，僅提供基本判斷",
            "triage_result": basic_result
        }