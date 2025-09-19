"""
設定管理與環境變數的單元測試
測試重點：
- GOOGLE_PLACES_API_KEY 必填驗證
- 預設值 DEFAULT_LANG=zh-TW, REGION=TW
- 使用 monkeypatch 測試環境變數設定
- 嚴禁使用 pytest.skip
- 所有功能必須完整實作
"""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError
from app.config import Settings, get_settings


class TestConfigurationSettings:
    """設定管理測試類別"""

    def test_missing_google_places_api_key_raises_exception(self, monkeypatch):
        """測試缺少 GOOGLE_PLACES_API_KEY 時拋出明確例外"""
        # 清除可能存在的環境變數
        monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)

        # 驗證缺少必要的 API KEY 時會拋出例外
        with pytest.raises(ValidationError) as exc_info:
            Settings()

        # 驗證例外訊息內容
        error_str = str(exc_info.value)
        assert "google_places_api_key" in error_str
        assert "required" in error_str.lower() or "missing" in error_str.lower()

    def test_valid_google_places_api_key_loads_successfully(self, monkeypatch):
        """測試提供有效的 GOOGLE_PLACES_API_KEY 時能成功載入"""
        # 設定有效的 API KEY
        test_api_key = "test_google_places_api_key_12345"
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", test_api_key)

        settings = Settings()
        assert settings.google_places_api_key == test_api_key

    def test_default_language_is_traditional_chinese(self, monkeypatch):
        """測試預設語言為繁體中文 (zh-TW)"""
        # 設定必要的 API KEY
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_key")
        # 確保沒有覆寫預設語言
        monkeypatch.delenv("DEFAULT_LANG", raising=False)

        settings = Settings()
        assert settings.default_lang == "zh-TW"

    def test_default_region_is_taiwan(self, monkeypatch):
        """測試預設地區為台灣 (TW)"""
        # 設定必要的 API KEY
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_key")
        # 確保沒有覆寫預設地區
        monkeypatch.delenv("REGION", raising=False)

        settings = Settings()
        assert settings.region == "TW"

    def test_custom_language_override(self, monkeypatch):
        """測試可以覆寫預設語言設定"""
        # 設定必要的 API KEY 和自訂語言
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_key")
        monkeypatch.setenv("DEFAULT_LANG", "en-US")

        settings = Settings()
        assert settings.default_lang == "en-US"

    def test_custom_region_override(self, monkeypatch):
        """測試可以覆寫預設地區設定"""
        # 設定必要的 API KEY 和自訂地區
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_key")
        monkeypatch.setenv("REGION", "US")

        settings = Settings()
        assert settings.region == "US"

    def test_environment_variable_precedence(self, monkeypatch):
        """測試環境變數優先於預設值"""
        # 設定所有環境變數
        test_values = {
            "GOOGLE_PLACES_API_KEY": "env_api_key_123",
            "DEFAULT_LANG": "ja-JP",
            "REGION": "JP"
        }

        for key, value in test_values.items():
            monkeypatch.setenv(key, value)

        settings = Settings()
        assert settings.google_places_api_key == test_values["GOOGLE_PLACES_API_KEY"]
        assert settings.default_lang == test_values["DEFAULT_LANG"]
        assert settings.region == test_values["REGION"]

    def test_settings_singleton_behavior(self, monkeypatch):
        """測試 get_settings 函數的單例行為"""
        # 清除 lru_cache 快取
        get_settings.cache_clear()

        # 設定必要的環境變數
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_singleton_key")

        # 取得兩次設定實例
        settings1 = get_settings()
        settings2 = get_settings()

        # 驗證是同一個實例
        assert settings1 is settings2

        # 驗證 API key (可能已被其他測試設定，所以只檢查存在)
        assert settings1.google_places_api_key is not None
        assert len(settings1.google_places_api_key) > 0

    def test_dotenv_file_loading(self, monkeypatch, tmp_path):
        """測試從 .env 檔案載入環境變數"""
        # 創建臨時 .env 檔案
        env_file = tmp_path / ".env"
        env_content = """
GOOGLE_PLACES_API_KEY=dotenv_test_key
DEFAULT_LANG=ko-KR
REGION=KR
"""
        env_file.write_text(env_content.strip())

        # 切換到臨時目錄
        monkeypatch.chdir(tmp_path)

        # 清除環境變數，確保從 .env 讀取
        monkeypatch.delenv("GOOGLE_PLACES_API_KEY", raising=False)
        monkeypatch.delenv("DEFAULT_LANG", raising=False)
        monkeypatch.delenv("REGION", raising=False)

        settings = Settings()
        assert settings.google_places_api_key == "dotenv_test_key"
        assert settings.default_lang == "ko-KR"
        assert settings.region == "KR"

    def test_invalid_api_key_format_validation(self, monkeypatch):
        """測試 API KEY 格式驗證（如果有的話）"""
        # 設定空字串的 API KEY
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "")

        with pytest.raises(ValueError) as exc_info:
            Settings()

        # 驗證會拋出關於空值的錯誤
        error_message = str(exc_info.value).lower()
        assert "empty" in error_message or "blank" in error_message or "required" in error_message

    def test_all_taiwan_medical_defaults(self, monkeypatch):
        """測試所有台灣醫療相關的預設值"""
        # 僅設定必要的 API KEY
        monkeypatch.setenv("GOOGLE_PLACES_API_KEY", "test_medical_key")

        # 清除其他可能的環境變數
        env_vars_to_clear = ["DEFAULT_LANG", "REGION"]
        for var in env_vars_to_clear:
            monkeypatch.delenv(var, raising=False)

        settings = Settings()

        # 驗證台灣醫療系統的預設值
        assert settings.default_lang == "zh-TW"  # 繁體中文
        assert settings.region == "TW"           # 台灣地區
        assert settings.google_places_api_key == "test_medical_key"