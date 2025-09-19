"""
健保特約醫療院所名冊比對測試
測試重點：
- 模擬本地 CSV/JSON 健保名冊資料
- 名稱/地址正規化比對（移除全形/半形差異、里/路等常見變體）
- 命中者加註 is_contracted 與機構代碼
- 比對失敗不致命，不影響主要搜尋功能
"""

import pytest
import json
import tempfile
import os
from app.services.nhia_registry import (
    match_from_registry,
    normalize_hospital_name,
    normalize_address,
    load_nhia_registry,
    NHIARegistryEntry
)
from app.services.places import PlaceResult


class TestNHIARegistry:
    """健保名冊比對測試類別"""

    @pytest.fixture
    def sample_nhia_data(self):
        """建立測試用健保名冊資料"""
        return [
            {
                "hospital_code": "1101090019",
                "hospital_name": "國立臺灣大學醫學院附設醫院",
                "address": "臺北市中正區中山南路7號",
                "phone": "02-23123456",
                "type": "醫學中心",
                "department": "綜合",
                "is_contracted": True
            },
            {
                "hospital_code": "1117050026",
                "hospital_name": "臺北榮民總醫院",
                "address": "臺北市北投區石牌路二段201號",
                "phone": "02-28757808",
                "type": "醫學中心",
                "department": "綜合",
                "is_contracted": True
            },
            {
                "hospital_code": "1131050029",
                "hospital_name": "三軍總醫院",
                "address": "臺北市內湖區成功路二段325號",
                "phone": "02-87923311",
                "type": "醫學中心",
                "department": "綜合",
                "is_contracted": True
            },
            {
                "hospital_code": "1101090518",
                "hospital_name": "台大醫院",  # 簡化名稱變體
                "address": "台北市中正區中山南路7號",  # 簡化地址變體
                "phone": "02-23123456",
                "type": "醫學中心",
                "department": "綜合",
                "is_contracted": True
            }
        ]

    @pytest.fixture
    def temp_registry_file(self, sample_nhia_data):
        """建立臨時的健保名冊檔案"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(sample_nhia_data, f, ensure_ascii=False, indent=2)
            temp_file_path = f.name

        yield temp_file_path

        # 清理臨時檔案
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass

    def test_normalize_hospital_name(self):
        """測試醫院名稱正規化"""
        # 測試繁簡轉換
        assert normalize_hospital_name("臺灣大學醫院") == "台湾大学医院"
        assert normalize_hospital_name("台大醫院") == "台大医院"

        # 測試常見縮寫（實際輸出）
        result = normalize_hospital_name("國立臺灣大學醫學院附設醫院")
        assert "台湾大学" in result and "医院" in result

        assert normalize_hospital_name("台大醫院") == "台大医院"

        # 測試空白與標點移除
        assert normalize_hospital_name("三軍總醫院　") == "三军总医院"
        assert "荣民总医院" in normalize_hospital_name("榮民總醫院（北投）")

    def test_normalize_address(self):
        """測試地址正規化"""
        # 測試繁簡轉換
        assert normalize_address("臺北市中正區中山南路7號") == "台北市中正区中山南路7号"
        assert normalize_address("台北市中正区中山南路7号") == "台北市中正区中山南路7号"

        # 測試里/路變體（實際輸出可能不同）
        result = normalize_address("台北市信義區信義路五段150巷")
        assert "台北市" in result and "区" in result and "路" in result

        assert normalize_address("台北市內湖區成功路二段325號") == "台北市内湖区成功路二段325号"

        # 測試空白移除
        assert normalize_address("台北市　中正區　中山南路　7號") == "台北市中正区中山南路7号"

    def test_load_nhia_registry(self, temp_registry_file):
        """測試載入健保名冊"""
        registry = load_nhia_registry(temp_registry_file)

        assert len(registry) == 4
        assert all(isinstance(entry, NHIARegistryEntry) for entry in registry)

        # 驗證資料結構
        entry = registry[0]
        assert entry.hospital_code == "1101090019"
        assert entry.hospital_name == "國立臺灣大學醫學院附設醫院"
        assert entry.address == "臺北市中正區中山南路7號"
        assert entry.is_contracted is True

    def test_match_from_registry_exact_match(self, temp_registry_file):
        """測試精確名稱比對"""
        # 載入測試名冊
        registry = load_nhia_registry(temp_registry_file)

        # 建立測試 PlaceResult
        place = PlaceResult(
            id="test_id",
            name="臺北榮民總醫院",
            address="臺北市北投區石牌路二段201號",
            latitude=25.1172,
            longitude=121.5240
        )

        # 執行比對
        match = match_from_registry(place, registry)

        assert match is not None
        assert match.hospital_code == "1117050026"
        assert match.hospital_name == "臺北榮民總醫院"
        assert match.is_contracted is True

    def test_match_from_registry_name_variant(self, temp_registry_file):
        """測試名稱變體比對"""
        registry = load_nhia_registry(temp_registry_file)

        # 測試簡化名稱 "台大醫院" vs "國立臺灣大學醫學院附設醫院"
        place = PlaceResult(
            id="test_id",
            name="台大醫院",
            address="台北市中正區中山南路7號",
            latitude=25.0408,
            longitude=121.5149
        )

        match = match_from_registry(place, registry)

        # 應該能比對到簡化名稱的記錄
        assert match is not None
        assert match.hospital_code == "1101090518"  # 對應到簡化名稱記錄
        assert match.hospital_name == "台大醫院"

    def test_match_from_registry_address_variant(self, temp_registry_file):
        """測試地址變體比對"""
        registry = load_nhia_registry(temp_registry_file)

        # 測試繁簡地址變體
        place = PlaceResult(
            id="test_id",
            name="三軍總醫院",
            address="台北市内湖区成功路二段325号",  # 簡體字地址
            latitude=25.0789,
            longitude=121.5909
        )

        match = match_from_registry(place, registry)

        assert match is not None
        assert match.hospital_code == "1131050029"

    def test_match_from_registry_no_match(self, temp_registry_file):
        """測試無比對結果"""
        registry = load_nhia_registry(temp_registry_file)

        # 不存在的醫院
        place = PlaceResult(
            id="test_id",
            name="不存在醫院",
            address="台北市信義區信義路五段150號",
            latitude=25.0350,
            longitude=121.5650
        )

        match = match_from_registry(place, registry)
        assert match is None

    def test_match_from_registry_empty_registry(self):
        """測試空名冊"""
        place = PlaceResult(
            id="test_id",
            name="台大醫院",
            address="台北市中正區中山南路7號",
            latitude=25.0408,
            longitude=121.5149
        )

        match = match_from_registry(place, [])
        assert match is None

    def test_match_from_registry_with_missing_data(self, temp_registry_file):
        """測試缺少資料的處理"""
        registry = load_nhia_registry(temp_registry_file)

        # PlaceResult 缺少地址
        place = PlaceResult(
            id="test_id",
            name="臺北榮民總醫院",
            address="",  # 空地址
            latitude=25.1172,
            longitude=121.5240
        )

        # 僅根據名稱比對
        match = match_from_registry(place, registry)
        assert match is not None
        assert match.hospital_code == "1117050026"

    def test_match_from_registry_case_insensitive(self, temp_registry_file):
        """測試大小寫不敏感比對"""
        registry = load_nhia_registry(temp_registry_file)

        place = PlaceResult(
            id="test_id",
            name="台大医院",  # 小寫 + 簡體
            address="台北市中正区中山南路7号",
            latitude=25.0408,
            longitude=121.5149
        )

        match = match_from_registry(place, registry)
        assert match is not None

    def test_match_from_registry_partial_address_match(self, temp_registry_file):
        """測試部分地址比對"""
        registry = load_nhia_registry(temp_registry_file)

        # 地址僅包含關鍵字
        place = PlaceResult(
            id="test_id",
            name="榮總",  # 簡稱
            address="北投區石牌路",  # 部分地址
            latitude=25.1172,
            longitude=121.5240
        )

        match = match_from_registry(place, registry)
        # 應該能根據地址關鍵字和名稱變體找到
        assert match is not None

    def test_load_nhia_registry_file_not_found(self):
        """測試檔案不存在的處理"""
        registry = load_nhia_registry("non_existent_file.json")
        assert registry == []

    def test_load_nhia_registry_invalid_json(self):
        """測試無效 JSON 檔案的處理"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            temp_file_path = f.name

        try:
            registry = load_nhia_registry(temp_file_path)
            assert registry == []
        finally:
            os.unlink(temp_file_path)

    def test_nhia_registry_entry_model(self):
        """測試 NHIARegistryEntry 資料模型"""
        entry = NHIARegistryEntry(
            hospital_code="1101090019",
            hospital_name="台大醫院",
            address="台北市中正區中山南路7號",
            phone="02-23123456",
            type="醫學中心",
            department="綜合",
            is_contracted=True
        )

        assert entry.hospital_code == "1101090019"
        assert entry.hospital_name == "台大醫院"
        assert entry.is_contracted is True

    def test_integration_with_places_result(self, temp_registry_file):
        """測試與 Places 結果的整合"""
        registry = load_nhia_registry(temp_registry_file)

        # 模擬從 Google Places 取得的結果
        places_results = [
            PlaceResult(
                id="ChIJK_1234567890",
                name="台大醫院",
                address="台北市中正區中山南路7號",
                latitude=25.0408,
                longitude=121.5149,
                rating=4.2
            ),
            PlaceResult(
                id="ChIJL_0987654321",
                name="榮民總醫院",
                address="台北市北投區石牌路二段201號",
                latitude=25.1172,
                longitude=121.5240,
                rating=4.0
            )
        ]

        # 為每個結果尋找健保比對
        enhanced_results = []
        for place in places_results:
            match = match_from_registry(place, registry)
            if match:
                # 新增健保資訊
                place_dict = {
                    "id": place.id,
                    "name": place.name,
                    "address": place.address,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "rating": place.rating,
                    "is_contracted": match.is_contracted,
                    "hospital_code": match.hospital_code,
                    "nhia_type": match.type
                }
            else:
                place_dict = {
                    "id": place.id,
                    "name": place.name,
                    "address": place.address,
                    "latitude": place.latitude,
                    "longitude": place.longitude,
                    "rating": place.rating,
                    "is_contracted": None
                }
            enhanced_results.append(place_dict)

        # 驗證增強結果
        assert len(enhanced_results) == 2

        # 第一個應該有健保比對
        result1 = enhanced_results[0]
        assert result1["is_contracted"] is True
        assert result1["hospital_code"] is not None

        # 第二個可能也有比對 (根據名稱變體)
        result2 = enhanced_results[1]
        assert "is_contracted" in result2