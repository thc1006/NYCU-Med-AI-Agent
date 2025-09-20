"""
路由器特定的 OpenAPI 文件增強
為每個 API 路由器添加台灣醫療特色的文件增強功能
"""

from typing import Dict, Any, List
from fastapi import APIRouter
from fastapi.openapi.models import Tag


# 台灣醫療專科對照表
TAIWAN_MEDICAL_SPECIALTIES = {
    "心臟內科": {
        "english": "Cardiology",
        "symptoms": ["胸痛", "胸悶", "心悸", "心跳異常", "高血壓"],
        "emergency_keywords": ["心肌梗塞", "心臟病發作", "胸痛"]
    },
    "胸腔內科": {
        "english": "Pulmonology",
        "symptoms": ["呼吸困難", "咳嗽", "氣喘", "胸部不適", "咳血"],
        "emergency_keywords": ["呼吸困難", "氣喘發作", "咳血"]
    },
    "神經內科": {
        "english": "Neurology",
        "symptoms": ["頭痛", "頭暈", "麻痺", "手腳無力", "記憶力減退"],
        "emergency_keywords": ["中風", "意識不清", "劇烈頭痛", "麻痺"]
    },
    "腸胃內科": {
        "english": "Gastroenterology",
        "symptoms": ["腹痛", "嘔吐", "腹瀉", "便秘", "消化不良"],
        "emergency_keywords": ["劇烈腹痛", "大量嘔吐", "便血"]
    },
    "急診科": {
        "english": "Emergency Medicine",
        "symptoms": ["創傷", "中毒", "急性病症", "意外傷害"],
        "emergency_keywords": ["所有緊急症狀"]
    }
}

# 台灣醫院層級說明
TAIWAN_HOSPITAL_LEVELS = {
    "醫學中心": {
        "description": "最高層級醫療院所，具備完整專科與急重症照護能力",
        "capabilities": ["複雜手術", "重症加護", "器官移植", "癌症治療"],
        "bed_count": "通常 > 500 床"
    },
    "區域醫院": {
        "description": "提供區域性醫療服務，具備多專科診療能力",
        "capabilities": ["專科診療", "急診服務", "住院治療", "健康檢查"],
        "bed_count": "通常 250-500 床"
    },
    "地區醫院": {
        "description": "社區型醫院，提供基本醫療與急診服務",
        "capabilities": ["基本診療", "急診服務", "住院觀察", "預防保健"],
        "bed_count": "通常 < 250 床"
    },
    "診所": {
        "description": "基層醫療院所，提供門診與預防保健服務",
        "capabilities": ["門診診療", "預防接種", "健康諮詢", "轉診服務"],
        "bed_count": "通常 < 20 床或無住院服務"
    }
}

# 緊急症狀分類與處理
EMERGENCY_SYMPTOM_CATEGORIES = {
    "立即危及生命": {
        "symptoms": ["心跳停止", "呼吸停止", "大量出血", "嚴重創傷"],
        "action": "立即撥打 119，進行 CPR 急救",
        "warning": "🆘 生命危險！立即急救！"
    },
    "緊急就醫": {
        "symptoms": ["胸痛", "呼吸困難", "意識模糊", "劇烈頭痛"],
        "action": "立即前往急診或撥打 119",
        "warning": "⚠️ 緊急！請立即就醫！"
    },
    "盡快就醫": {
        "symptoms": ["持續高燒", "劇烈腹痛", "嚴重嘔吐", "無法進食"],
        "action": "24小時內前往急診或門診",
        "warning": "⚡ 需要盡快就醫"
    },
    "安排就醫": {
        "symptoms": ["持續咳嗽", "關節疼痛", "皮膚問題", "消化不良"],
        "action": "1-3天內安排門診",
        "warning": "📅 建議安排就醫"
    }
}


def enhance_triage_router_docs(router: APIRouter) -> Dict[str, Any]:
    """
    增強症狀分級路由器的文件

    Args:
        router: 症狀分級 APIRouter 實例

    Returns:
        Dict: 增強的文件資訊
    """
    enhanced_docs = {
        "description": """
        ## 台灣醫療症狀分級系統

        ### 分級標準
        本系統採用四級分級制度：
        - **🆘 emergency**: 緊急狀況，立即撥打119
        - **⚡ urgent**: 緊急，盡快就醫（24小時內）
        - **📅 outpatient**: 安排門診就醫（1-3天內）
        - **🏠 self-care**: 可自我照護觀察

        ### 紅旗症狀自動偵測
        系統會自動識別以下緊急症狀：
        """,
        "examples": {
            "emergency_chest_pain": {
                "summary": "急性胸痛 - 疑似心肌梗塞",
                "description": "男性55歲，突發胸痛伴冷汗",
                "value": {
                    "symptom_text": "胸部劇痛，有壓迫感，冷汗直流，痛到後背",
                    "age": 55,
                    "gender": "M",
                    "duration_hours": 1,
                    "has_chronic_disease": True,
                    "medications": ["降血壓藥"]
                }
            },
            "mild_cold": {
                "summary": "一般感冒症狀",
                "description": "輕微感冒，可自我照護",
                "value": {
                    "symptom_text": "流鼻水、輕微頭痛、有點疲倦",
                    "age": 30,
                    "gender": "F",
                    "duration_hours": 12
                }
            }
        },
        "emergency_categories": EMERGENCY_SYMPTOM_CATEGORIES,
        "specialties": TAIWAN_MEDICAL_SPECIALTIES
    }

    return enhanced_docs


def enhance_hospitals_router_docs(router: APIRouter) -> Dict[str, Any]:
    """
    增強醫院搜尋路由器的文件

    Args:
        router: 醫院搜尋 APIRouter 實例

    Returns:
        Dict: 增強的文件資訊
    """
    enhanced_docs = {
        "description": """
        ## 台灣醫療院所搜尋系統

        ### 定位方式
        支援三種定位方式，按優先級排序：
        1. **精確座標** (latitude + longitude) - 誤差 < 10公尺
        2. **地址解析** (address) - 支援台灣地址格式
        3. **IP定位** (use_ip=true) - 誤差約 1-5 公里

        ### 台灣醫院分級制度
        """,
        "examples": {
            "taipei_search": {
                "summary": "台北市中心醫院搜尋",
                "description": "搜尋台北車站附近醫院",
                "parameters": {
                    "latitude": 25.0478,
                    "longitude": 121.5170,
                    "radius": 2000,
                    "max_results": 10
                }
            },
            "address_search": {
                "summary": "地址搜尋範例",
                "description": "使用台灣地址搜尋附近醫院",
                "parameters": {
                    "address": "台北市大安區忠孝東路四段1號",
                    "radius": 3000,
                    "include_nhia": True
                }
            },
            "emergency_search": {
                "summary": "緊急醫院搜尋",
                "description": "搭配症狀的緊急醫院搜尋",
                "parameters": {
                    "latitude": 25.0330,
                    "longitude": 121.5654,
                    "symptoms": ["胸痛", "呼吸困難"],
                    "radius": 3000
                }
            }
        },
        "hospital_levels": TAIWAN_HOSPITAL_LEVELS,
        "taiwan_addresses": [
            "台北市中正區中山南路7號（台大醫院）",
            "台北市內湖區成功路二段325號（三總內湖院區）",
            "台中市西屯區台灣大道四段1650號（中國醫藥大學附醫）",
            "高雄市三民區自由一路100號（高醫附醫）"
        ]
    }

    return enhanced_docs


def enhance_meta_router_docs(router: APIRouter) -> Dict[str, Any]:
    """
    增強元數據路由器的文件

    Args:
        router: 元數據 APIRouter 實例

    Returns:
        Dict: 增強的文件資訊
    """
    enhanced_docs = {
        "description": """
        ## 台灣急救與緊急聯絡系統

        ### 緊急聯絡電話
        - **119**: 消防救護專線（火災、救護車、緊急救助）
        - **110**: 警察報案專線（治安、交通事故、刑案報案）
        - **112**: 手機緊急撥號（無卡、無訊號時的緊急號碼）
        - **113**: 婦幼保護專線（家暴、性侵、兒少保護）

        ### 何時撥打 119
        """,
        "emergency_guidelines": {
            "when_to_call_119": [
                "呼吸困難或停止呼吸",
                "胸痛或心臟病發作徵象",
                "嚴重外傷或大量出血",
                "意識不清或昏迷",
                "嚴重燒燙傷",
                "中毒或嚴重過敏反應",
                "骨折或脊椎受傷"
            ],
            "how_to_call": [
                "保持冷靜，清楚說明現場狀況",
                "提供精確的地點資訊（地址、路口、地標）",
                "說明傷者數量與傷勢",
                "配合指示進行初步急救",
                "確保現場安全，等待救援人員"
            ]
        }
    }

    return enhanced_docs


def enhance_monitoring_router_docs(router: APIRouter) -> Dict[str, Any]:
    """
    增強監控路由器的文件

    Args:
        router: 監控 APIRouter 實例

    Returns:
        Dict: 增強的文件資訊
    """
    enhanced_docs = {
        "description": """
        ## 系統監控與健康檢查

        ### PDPA 合規監控
        - 不記錄個人醫療資料
        - 審計軌跡加密儲存
        - 資料保留期限管理

        ### 效能監控指標
        - API 回應時間
        - 錯誤率統計
        - 使用量分析
        """,
        "compliance_features": {
            "privacy_protection": [
                "症狀描述不與個人身份連結",
                "位置資訊僅用於搜尋，不保存",
                "審計紀錄去識別化處理"
            ],
            "data_retention": [
                "系統日誌保留 30 天",
                "效能指標保留 90 天",
                "審計軌跡保留 1 年"
            ]
        }
    }

    return enhanced_docs


def create_enhanced_router_docs() -> Dict[str, Any]:
    """
    建立所有路由器的增強文件

    Returns:
        Dict: 完整的增強文件字典
    """
    return {
        "triage": enhance_triage_router_docs(None),
        "hospitals": enhance_hospitals_router_docs(None),
        "meta": enhance_meta_router_docs(None),
        "monitoring": enhance_monitoring_router_docs(None),
        "global_features": {
            "taiwan_localization": {
                "language": "繁體中文 (Traditional Chinese)",
                "region": "台灣 (Taiwan)",
                "address_format": "台灣地址格式支援",
                "phone_format": "台灣電話號碼格式"
            },
            "medical_compliance": {
                "regulatory_framework": [
                    "醫療法",
                    "緊急醫療救護法",
                    "個人資料保護法 (PDPA)"
                ],
                "safety_features": [
                    "紅旗症狀自動偵測",
                    "緊急聯絡資訊自動提供",
                    "醫療免責聲明強制顯示"
                ]
            },
            "technical_features": {
                "rate_limiting": "防止API濫用",
                "audit_trail": "完整操作記錄",
                "error_handling": "詳細錯誤訊息",
                "monitoring": "即時系統監控"
            }
        }
    }


# 台灣特色的 OpenAPI 範例生成器
class TaiwanMedicalExampleGenerator:
    """台灣醫療 API 範例生成器"""

    @staticmethod
    def generate_symptom_examples() -> Dict[str, Any]:
        """生成症狀評估範例"""
        return {
            "emergency_examples": [
                {
                    "scenario": "急性心肌梗塞",
                    "symptoms": "胸部劇痛，痛到左手臂，冷汗直流",
                    "expected_level": "emergency",
                    "expected_actions": ["立即撥打119", "含服硝化甘油", "平躺休息"]
                },
                {
                    "scenario": "嚴重氣喘發作",
                    "symptoms": "呼吸困難，喘不過氣，嘴唇發紫",
                    "expected_level": "emergency",
                    "expected_actions": ["立即撥打119", "使用急救吸入器", "坐直身體"]
                }
            ],
            "self_care_examples": [
                {
                    "scenario": "一般感冒",
                    "symptoms": "流鼻水，輕微頭痛，有點疲倦",
                    "expected_level": "self-care",
                    "expected_actions": ["多休息", "多喝水", "觀察症狀變化"]
                }
            ]
        }

    @staticmethod
    def generate_hospital_examples() -> Dict[str, Any]:
        """生成醫院搜尋範例"""
        return {
            "major_cities": {
                "台北市": {"lat": 25.0330, "lng": 121.5654, "famous_hospitals": ["台大醫院", "榮總", "馬偕醫院"]},
                "新北市": {"lat": 25.0173, "lng": 121.4665, "famous_hospitals": ["亞東醫院", "雙和醫院", "慈濟醫院"]},
                "桃園市": {"lat": 24.9936, "lng": 121.3010, "famous_hospitals": ["林口長庚", "桃園醫院", "聖保祿醫院"]},
                "台中市": {"lat": 24.1477, "lng": 120.6736, "famous_hospitals": ["中國醫藥大學附醫", "台中榮總", "澄清醫院"]},
                "台南市": {"lat": 22.9999, "lng": 120.2269, "famous_hospitals": ["成大醫院", "奇美醫院", "台南醫院"]},
                "高雄市": {"lat": 22.6273, "lng": 120.3014, "famous_hospitals": ["高醫附醫", "高雄榮總", "義大醫院"]}
            }
        }