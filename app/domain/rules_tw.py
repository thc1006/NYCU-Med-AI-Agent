"""
台灣醫療安全規則定義
包含緊急症狀判斷、就醫建議級別等本地化規則
"""

from typing import List, Dict, Any, Optional
from app.domain.models import TriageLevel


# 緊急症狀關鍵字（需要立即撥打119）
EMERGENCY_KEYWORDS = [
    # 心血管系統
    "胸痛", "胸悶", "心臟", "心悸", "心跳", "胸口痛",

    # 呼吸系統
    "呼吸困難", "喘不過氣", "窒息", "呼吸急促", "喘",

    # 神經系統
    "昏迷", "意識不清", "意識喪失", "昏倒", "暈倒",
    "麻痺", "癱瘓", "半身不遂", "手腳無力",
    "劇烈頭痛", "爆炸性頭痛", "頭痛欲裂", "頭痛到快爆炸",
    "中風", "腦血管", "腦出血",

    # 創傷
    "大量出血", "大出血", "血流不止", "噴血",
    "骨折", "斷骨", "骨頭斷",
    "嚴重燒傷", "大面積燒傷", "燙傷",

    # 其他緊急
    "中毒", "過敏性休克", "休克",
    "抽搐", "痙攣", "癲癇",
    "自殺", "自殘"
]

# 輕微症狀關鍵字（可自我照護）
MILD_KEYWORDS = [
    "流鼻水", "鼻塞", "打噴嚏",
    "喉嚨痛", "喉嚨癢", "喉嚨不適", "喉嚨有點痛",
    "輕微咳嗽", "乾咳", "咳嗽", "有點咳嗽",
    "頭痛", "輕微頭痛", "頭暈",
    "疲倦", "疲勞", "沒精神",
    "肌肉痠痛", "全身痠痛",
    "輕微腹瀉", "拉肚子",
    "輕微發燒", "低燒"
]

# 中度症狀關鍵字（建議門診就醫）
MODERATE_KEYWORDS = [
    "高燒", "發高燒", "發燒",
    "持續頭痛", "頭痛加劇",
    "持續腹痛", "腹部疼痛",
    "嘔吐", "持續嘔吐", "噁心",
    "血尿", "血便", "吐血",
    "皮疹", "過敏", "蕁麻疹",
    "耳痛", "耳鳴",
    "視力模糊", "眼睛痛",
    "嚴重不適"  # 模糊但嚴重的描述
]


def get_emergency_keywords() -> List[str]:
    """取得緊急症狀關鍵字列表"""
    return EMERGENCY_KEYWORDS.copy()


def get_mild_keywords() -> List[str]:
    """取得輕微症狀關鍵字列表"""
    return MILD_KEYWORDS.copy()


def get_moderate_keywords() -> List[str]:
    """取得中度症狀關鍵字列表"""
    return MODERATE_KEYWORDS.copy()


def analyze_symptoms(symptom_text: str) -> List[str]:
    """
    分析症狀文字，提取關鍵症狀

    Args:
        symptom_text: 症狀描述文字

    Returns:
        List[str]: 檢測到的症狀列表
    """
    if not symptom_text:
        return []

    detected_symptoms = []
    text_lower = symptom_text

    # 檢查緊急症狀（優先級最高）
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in text_lower:
            detected_symptoms.append(keyword)

    # 特殊處理胸痛變體 (胸口痛、胸口很痛等)
    if "胸痛" not in detected_symptoms and "胸口" in text_lower and "痛" in text_lower:
        detected_symptoms.append("胸痛")

    # 檢查中度症狀 - 處理否定語句
    for keyword in MODERATE_KEYWORDS:
        if keyword in text_lower and keyword not in detected_symptoms:
            # 檢查是否是否定語句 (例如"沒有發燒")
            if keyword == "發燒" and "沒有發燒" in text_lower:
                continue  # 跳過這個關鍵字
            detected_symptoms.append(keyword)

    # 檢查輕微症狀 - 更寬鬆的比對
    for keyword in MILD_KEYWORDS:
        if keyword in text_lower and keyword not in detected_symptoms:
            detected_symptoms.append(keyword)

    # 特殊處理：部分匹配
    if not detected_symptoms:
        if "喉嚨" in text_lower and "痛" in text_lower:
            detected_symptoms.append("喉嚨痛")
        elif "咳" in text_lower:
            detected_symptoms.append("咳嗽")
        elif "胸" in text_lower and "痛" in text_lower:
            detected_symptoms.append("胸痛")

    return detected_symptoms


def determine_triage_level(detected_symptoms: List[str]) -> TriageLevel:
    """
    根據檢測到的症狀判斷分級等級

    Args:
        detected_symptoms: 檢測到的症狀列表

    Returns:
        TriageLevel: 建議的分級等級
    """
    if not detected_symptoms:
        return TriageLevel.SELF_CARE

    # 檢查是否有緊急症狀
    for symptom in detected_symptoms:
        if symptom in EMERGENCY_KEYWORDS:
            return TriageLevel.EMERGENCY

    # 檢查是否有中度症狀
    for symptom in detected_symptoms:
        if symptom in MODERATE_KEYWORDS:
            return TriageLevel.OUTPATIENT

    # 檢查持續時間（如果症狀描述中提到）
    keywords_indicating_duration = ["三天", "好幾天", "一週", "很久", "持續"]
    symptom_text_combined = " ".join(detected_symptoms)
    for keyword in keywords_indicating_duration:
        if keyword in symptom_text_combined:
            return TriageLevel.OUTPATIENT

    # 預設為自我照護
    return TriageLevel.SELF_CARE


def get_emergency_advice() -> str:
    """取得緊急情況建議"""
    return (
        "您描述的症狀屬於緊急醫療狀況，請立即撥打 119 叫救護車，"
        "或儘速前往最近的急診室就醫。在等待救援期間，請保持冷靜。"
    )


def get_emergency_next_steps() -> List[str]:
    """取得緊急情況下一步指引"""
    return [
        "立即撥打 119 緊急醫療救護專線",
        "保持冷靜，找個安全的地方坐下或躺下",
        "解開緊身的衣物，保持呼吸道暢通",
        "準備好健保卡、身分證和目前服用的藥物清單",
        "如果可能，請家人或朋友陪同",
        "清楚告知救護人員您的症狀和位置"
    ]


def get_outpatient_advice() -> str:
    """取得門診就醫建議"""
    return (
        "您的症狀建議安排門診就醫評估。請儘快預約看診，"
        "或前往附近的診所、醫院門診部就醫。"
    )


def get_outpatient_next_steps() -> List[str]:
    """取得門診就醫下一步指引"""
    return [
        "預約門診看診或直接前往診所",
        "準備健保卡和身分證件",
        "記錄症狀發生的時間和變化",
        "列出目前服用的藥物",
        "充分休息，多喝水",
        "如果症狀突然惡化，請立即撥打 119"
    ]


def get_self_care_advice() -> str:
    """取得自我照護建議"""
    return (
        "您的症狀目前看起來較輕微，可以先自我觀察和照護。"
        "請多休息，保持充足的水分攝取。如果症狀持續或惡化，建議就醫。"
    )


def get_self_care_next_steps() -> List[str]:
    """取得自我照護下一步指引"""
    return [
        "多休息，避免過度勞累",
        "保持充足的水分攝取",
        "清淡飲食，避免刺激性食物",
        "觀察症狀變化並記錄",
        "如果症狀持續超過3天未改善，建議就醫",
        "如果出現發高燒、呼吸困難等嚴重症狀，請立即就醫"
    ]


def get_disclaimer() -> str:
    """取得醫療免責聲明"""
    return (
        "本系統僅供參考，非醫療診斷工具，不能取代專業醫療診斷、治療或建議。"
        "如有緊急醫療狀況，請立即撥打 119 或前往急診就醫。"
    )


def get_emergency_numbers() -> List[str]:
    """取得台灣緊急電話號碼"""
    return ["119", "110", "112"]


def get_recommended_departments(symptoms: List[str]) -> List[str]:
    """
    根據症狀推薦就診科別

    Args:
        symptoms: 症狀列表

    Returns:
        List[str]: 建議的就診科別
    """
    departments = set()

    # 症狀到科別的對應
    symptom_to_department = {
        # 心血管
        "胸痛": ["急診", "心臟內科"],
        "胸悶": ["急診", "心臟內科"],
        "心悸": ["心臟內科"],

        # 呼吸系統
        "呼吸困難": ["急診", "胸腔內科"],
        "咳嗽": ["家醫科", "胸腔內科"],
        "喘": ["急診", "胸腔內科"],

        # 神經系統
        "頭痛": ["神經內科", "家醫科"],
        "劇烈頭痛": ["急診", "神經內科"],
        "麻痺": ["急診", "神經內科"],
        "中風": ["急診", "神經內科"],

        # 腸胃系統
        "腹痛": ["腸胃內科", "家醫科"],
        "嘔吐": ["腸胃內科", "急診"],
        "腹瀉": ["腸胃內科", "家醫科"],

        # 一般症狀
        "發燒": ["家醫科", "感染科"],
        "流鼻水": ["耳鼻喉科", "家醫科"],
        "喉嚨痛": ["耳鼻喉科", "家醫科"]
    }

    for symptom in symptoms:
        for key, dept_list in symptom_to_department.items():
            if key in symptom:
                departments.update(dept_list)

    # 如果沒有找到對應科別，預設家醫科
    if not departments:
        departments.add("家醫科")

    return sorted(list(departments))