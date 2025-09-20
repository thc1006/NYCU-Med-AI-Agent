"""
台灣醫療 AI 助理 OpenAPI 文件配置
自定義 FastAPI OpenAPI 生成，增加台灣特色與醫療合規資訊
"""

from typing import Dict, Any, Optional
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import yaml
import os

# 台灣醫療相關的標籤與描述
TAIWAN_MEDICAL_TAGS = [
    {
        "name": "症狀分級",
        "description": "智能症狀評估與分級系統，提供就醫建議與緊急警示",
        "externalDocs": {
            "description": "台灣分級醫療制度說明",
            "url": "https://www.mohw.gov.tw/cp-16-33202-1.html"
        }
    },
    {
        "name": "醫院搜尋",
        "description": "就近醫療院所搜尋服務，整合健保特約資訊",
        "externalDocs": {
            "description": "健保特約醫事機構查詢",
            "url": "https://www.nhi.gov.tw/QueryII/"
        }
    },
    {
        "name": "元數據",
        "description": "台灣急救熱線與系統基本資訊",
        "externalDocs": {
            "description": "台灣緊急救援體系",
            "url": "https://www.nfa.gov.tw/"
        }
    },
    {
        "name": "健康資訊",
        "description": "衛教資源、疫苗接種與健保資訊",
        "externalDocs": {
            "description": "衛生福利部資源",
            "url": "https://www.mohw.gov.tw/"
        }
    },
    {
        "name": "系統監控",
        "description": "API 健康狀態與效能監控",
    }
]

# 醫療免責聲明與合規資訊
MEDICAL_DISCLAIMERS = {
    "legal": """
    ## 法律聲明與免責條款

    ### 醫療免責聲明
    - 本服務僅供參考，**不能取代專業醫療診斷**
    - 任何醫療決定都應諮詢合格醫療專業人員
    - 緊急狀況請立即撥打 **119**（消防救護）

    ### 個人資料保護（PDPA 合規）
    - 不收集或儲存個人醫療資料
    - 位置資訊僅用於搜尋，不會被保存
    - 符合台灣個人資料保護法規範

    ### 緊急聯絡資訊
    - **119**: 消防救護專線（火災、救護車、緊急救助）
    - **110**: 警察報案專線（治安、交通事故）
    - **112**: 手機緊急撥號（無卡、無訊號時使用）
    - **113**: 婦幼保護專線（家暴、性侵、兒少保護）
    """,

    "usage": """
    ## API 使用規範

    ### 速率限制
    - 一般 API：每分鐘 100 次請求
    - 症狀評估：每分鐘 20 次請求（防止濫用）
    - 超出限制回傳 HTTP 429 狀態碼

    ### 資料格式
    - 所有文字均使用**繁體中文**
    - 日期時間採用 ISO 8601 格式
    - 座標使用 WGS84 座標系統

    ### 錯誤處理
    - 所有錯誤回應包含詳細錯誤訊息
    - 緊急症狀會觸發特殊警告機制
    - 系統會自動記錄審計軌跡
    """,

    "emergency": """
    ## 緊急處理機制

    ### 紅旗症狀自動偵測
    系統會自動識別以下緊急症狀：
    - 胸痛、胸悶、心悸
    - 呼吸困難、氣喘
    - 意識不清、昏迷
    - 大量出血、嚴重外傷
    - 劇烈頭痛、麻痺
    - 中毒、過敏反應

    ### 緊急回應流程
    1. **立即警告**：顯示緊急訊息與聯絡電話
    2. **醫院搜尋**：自動限制搜尋範圍至 3 公里內
    3. **優先排序**：急診醫院優先顯示
    4. **追蹤記錄**：記錄緊急案例供品質改善
    """
}

# 台灣特色範例
TAIWAN_EXAMPLES = {
    "addresses": [
        "台北市大安區忠孝東路四段1號",
        "新北市板橋區縣民大道二段7號",
        "桃園市桃園區縣府路1號",
        "台中市西屯區台灣大道三段99號",
        "台南市安平區永華路二段6號",
        "高雄市苓雅區四維三路2號"
    ],
    "symptoms": {
        "emergency": [
            "胸部劇痛，有壓迫感，冒冷汗",
            "突然呼吸困難，喘不過氣",
            "意識模糊，頭暈想吐",
            "大量出血，傷口很深"
        ],
        "urgent": [
            "持續高燒39度，頭痛欲裂",
            "劇烈腹痛，無法站立",
            "嚴重嘔吐，完全無法進食"
        ],
        "outpatient": [
            "咳嗽兩週，有黃痰",
            "關節疼痛，活動受限",
            "皮膚紅疹，搔癢難耐"
        ],
        "self_care": [
            "輕微頭痛，精神疲倦",
            "流鼻水，喉嚨有點痛",
            "肌肉痠痛，可能感冒了"
        ]
    },
    "coordinates": {
        "taipei": {"lat": 25.0330, "lng": 121.5654},
        "taichung": {"lat": 24.1477, "lng": 120.6736},
        "kaohsiung": {"lat": 22.6273, "lng": 120.3014},
        "tainan": {"lat": 22.9999, "lng": 120.2269}
    }
}


def create_custom_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    建立自訂的 OpenAPI 3.0 結構描述

    Args:
        app: FastAPI 應用程式實例

    Returns:
        Dict: 自訂的 OpenAPI 結構描述
    """
    if app.openapi_schema:
        return app.openapi_schema

    # 生成基本 OpenAPI 結構描述
    openapi_schema = get_openapi(
        title="台灣醫療 AI 助理 API",
        version="1.0.0",
        description="專為台灣醫療環境設計的 AI 助理系統",
        routes=app.routes,
    )

    # 加入自訂資訊
    openapi_schema["info"].update({
        "description": f"""
        專為台灣醫療環境設計的 AI 助理系統，提供症狀分析、醫院搜尋與緊急醫療指引服務。

        {MEDICAL_DISCLAIMERS['legal']}

        {MEDICAL_DISCLAIMERS['usage']}

        {MEDICAL_DISCLAIMERS['emergency']}
        """,
        "contact": {
            "name": "Taiwan Medical AI Assistant Support",
            "email": "support@taiwan-med-ai.tw",
            "url": "https://taiwan-med-ai.tw/support"
        },
        "license": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "termsOfService": "https://taiwan-med-ai.tw/terms",
        "x-logo": {
            "url": "https://taiwan-med-ai.tw/logo.png",
            "altText": "Taiwan Medical AI Assistant"
        }
    })

    # 加入伺服器資訊
    openapi_schema["servers"] = [
        {
            "url": "https://api.taiwan-med-ai.tw",
            "description": "正式環境"
        },
        {
            "url": "https://staging-api.taiwan-med-ai.tw",
            "description": "測試環境"
        },
        {
            "url": "http://localhost:8000",
            "description": "開發環境"
        }
    ]

    # 更新標籤資訊
    openapi_schema["tags"] = TAIWAN_MEDICAL_TAGS

    # 加入全域安全性設定
    openapi_schema["security"] = [{"RateLimiting": []}]

    # 加入安全性結構描述
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = {
        "RateLimiting": {
            "type": "apiKey",
            "description": """
            API 速率限制機制：
            - 預設限制：每分鐘 100 次請求
            - 症狀評估：每分鐘 20 次請求
            - 超出限制將回傳 429 狀態碼
            """,
            "name": "X-RateLimit-Limit",
            "in": "header"
        }
    }

    # 加入全域回應標頭
    if "headers" not in openapi_schema["components"]:
        openapi_schema["components"]["headers"] = {}

    openapi_schema["components"]["headers"].update({
        "X-Request-Id": {
            "description": "請求唯一識別碼，用於追蹤和除錯",
            "schema": {
                "type": "string",
                "example": "req_abc123def456"
            }
        },
        "X-RateLimit-Limit": {
            "description": "速率限制上限",
            "schema": {
                "type": "integer",
                "example": 100
            }
        },
        "X-RateLimit-Remaining": {
            "description": "剩餘請求次數",
            "schema": {
                "type": "integer",
                "example": 95
            }
        },
        "X-Response-Time": {
            "description": "回應時間（毫秒）",
            "schema": {
                "type": "number",
                "example": 250.5
            }
        }
    })

    # 加入外部文件連結
    openapi_schema["externalDocs"] = {
        "description": "台灣醫療 AI 助理完整文件",
        "url": "https://docs.taiwan-med-ai.tw"
    }

    # 加入台灣特色擴充屬性
    openapi_schema["x-taiwan-medical"] = {
        "emergency_numbers": ["119", "110", "112", "113"],
        "supported_regions": ["台北市", "新北市", "桃園市", "台中市", "台南市", "高雄市"],
        "medical_levels": ["醫學中心", "區域醫院", "地區醫院", "診所"],
        "compliance": ["PDPA", "醫療法", "緊急醫療救護法"]
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def load_external_openapi_spec() -> Optional[Dict[str, Any]]:
    """
    載入外部 OpenAPI 規格檔案

    Returns:
        Dict: 外部 OpenAPI 規格，如果檔案不存在則返回 None
    """
    spec_path = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.yaml")

    try:
        with open(spec_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return None
    except yaml.YAMLError as e:
        print(f"Error loading OpenAPI spec: {e}")
        return None


def enhance_fastapi_docs(app: FastAPI) -> None:
    """
    增強 FastAPI 應用程式的文件功能

    Args:
        app: FastAPI 應用程式實例
    """
    # 設定自訂 OpenAPI 結構描述生成器
    app.openapi = lambda: create_custom_openapi_schema(app)

    # 嘗試載入外部規格檔案
    external_spec = load_external_openapi_spec()
    if external_spec:
        print("Loaded external OpenAPI specification")

    # 加入中介軟體來處理 CORS 和文件存取
    @app.middleware("http")
    async def add_docs_headers(request, call_next):
        """為文件頁面加入額外的 HTTP 標頭"""
        response = await call_next(request)

        # 為 API 文件頁面加入快取標頭
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            response.headers["Cache-Control"] = "public, max-age=300"
            response.headers["X-API-Version"] = "1.0.0"
            response.headers["X-Taiwan-Medical-API"] = "true"

        return response


def get_taiwan_medical_openapi_config() -> Dict[str, Any]:
    """
    取得台灣醫療 AI 助理的 OpenAPI 設定

    Returns:
        Dict: OpenAPI 設定字典
    """
    return {
        "title": "台灣醫療 AI 助理 API",
        "description": "專為台灣醫療環境設計的 AI 助理系統，具備完整監控與合規功能",
        "version": "1.0.0",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "tags_metadata": TAIWAN_MEDICAL_TAGS,
        "contact": {
            "name": "Taiwan Medical AI Assistant Support",
            "email": "support@taiwan-med-ai.tw"
        },
        "license_info": {
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT"
        },
        "terms_of_service": "https://taiwan-med-ai.tw/terms"
    }