"""
台灣醫療 AI 助理 - 設定管理模組
負責載入和管理應用程式的所有設定，包括環境變數和預設值
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic import validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class Settings(BaseSettings):
    """應用程式設定類別"""

    # Google Places API 設定 (必填)
    google_places_api_key: str

    # 台灣在地化設定
    default_lang: str = "zh-TW"  # 預設繁體中文
    region: str = "TW"           # 預設台灣地區

    # 應用程式基本設定
    app_name: str = "台灣醫療 AI 助理"
    app_version: str = "0.1.0"
    debug: bool = False

    # API 設定
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # 醫療安全設定
    emergency_numbers: list = ["119", "112", "110", "113", "165"]
    medical_disclaimer_required: bool = True

    # 台灣急救熱線詳細資訊
    # 資料來源：台北市政府英文網頁、NCC 公告、內政部警政署
    @property
    def emergency_numbers_detail(self) -> list:
        """取得台灣急救熱線詳細資訊"""
        return [
            {
                "code": "119",
                "description": "消防救護專線（火災、救護車、緊急救助）",
                "category": "消防救護",
                "available": "24小時",
                "coverage": "全台灣"
            },
            {
                "code": "110",
                "description": "警察報案專線（治安、交通、刑案報案）",
                "category": "警政治安",
                "available": "24小時",
                "coverage": "全台灣"
            },
            {
                "code": "112",
                "description": "行動電話國際緊急號碼（無卡、無訊號時可撥）",
                "category": "通訊緊急",
                "available": "24小時",
                "coverage": "全台灣（GSM網路）"
            },
            {
                "code": "113",
                "description": "婦幼保護專線（家暴、性侵、兒少保護）",
                "category": "社會保護",
                "available": "24小時",
                "coverage": "全台灣"
            },
            {
                "code": "165",
                "description": "反詐騙諮詢專線（詐騙防制、通報）",
                "category": "防詐反詐",
                "available": "24小時",
                "coverage": "全台灣"
            }
        ]

    @validator("google_places_api_key")
    def validate_google_places_api_key(cls, v):
        """驗證 Google Places API Key"""
        if not v:
            raise ValueError(
                "GOOGLE_PLACES_API_KEY is required for Taiwan medical AI assistant. "
                "Please set this environment variable with your Google Places API key."
            )
        if not v.strip():
            raise ValueError(
                "GOOGLE_PLACES_API_KEY cannot be empty or blank. "
                "Please provide a valid Google Places API key."
            )
        return v.strip()

    @validator("default_lang")
    def validate_default_lang(cls, v):
        """驗證預設語言格式"""
        if not v:
            return "zh-TW"  # 台灣醫療系統預設繁體中文
        return v.strip()

    @validator("region")
    def validate_region(cls, v):
        """驗證地區設定"""
        if not v:
            return "TW"  # 台灣醫療系統預設台灣地區
        return v.strip().upper()

    class Config:
        """Pydantic 設定"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        # 環境變數對應
        fields = {
            "google_places_api_key": {"env": "GOOGLE_PLACES_API_KEY"},
            "default_lang": {"env": "DEFAULT_LANG"},
            "region": {"env": "REGION"},
            "app_name": {"env": "APP_NAME"},
            "app_version": {"env": "APP_VERSION"},
            "debug": {"env": "DEBUG"},
            "api_host": {"env": "API_HOST"},
            "api_port": {"env": "API_PORT"},
        }


@lru_cache()
def get_settings() -> Settings:
    """
    取得應用程式設定的單例函數
    使用 lru_cache 確保設定只載入一次

    Returns:
        Settings: 應用程式設定實例
    """
    # 載入 .env 檔案（如果存在）
    load_dotenv()

    return Settings()


def load_taiwan_medical_config() -> Settings:
    """
    載入台灣醫療特化的設定
    確保所有台灣醫療相關的設定都正確載入

    Returns:
        Settings: 台灣醫療設定實例
    """
    settings = get_settings()

    # 驗證台灣醫療必要設定
    if settings.default_lang != "zh-TW":
        # 警告：不是使用繁體中文
        import warnings
        warnings.warn(
            f"Current language setting is '{settings.default_lang}', "
            "but 'zh-TW' is recommended for Taiwan medical system.",
            UserWarning
        )

    if settings.region != "TW":
        # 警告：不是台灣地區
        import warnings
        warnings.warn(
            f"Current region setting is '{settings.region}', "
            "but 'TW' is recommended for Taiwan medical system.",
            UserWarning
        )

    return settings


# 全域設定實例（用於導入時的便利性）
# 註：僅在需要時才載入設定，避免導入時的驗證錯誤
def _get_global_settings():
    """延遲載入全域設定"""
    try:
        return get_settings()
    except Exception:
        # 在測試或開發環境中可能沒有設定環境變數
        return None

# 使用函數而非直接實例化，避免導入時錯誤
def get_global_settings():
    """取得全域設定實例"""
    return _get_global_settings()