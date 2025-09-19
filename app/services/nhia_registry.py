"""
健保特約醫療院所名冊比對服務
提供醫院名稱與地址的正規化比對功能
用於驗證 Google Places 結果是否為健保特約院所
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class NHIARegistryEntry:
    """健保特約醫療院所記錄"""
    hospital_code: str
    hospital_name: str
    address: str
    phone: str
    type: str  # 醫學中心、區域醫院、地區醫院、診所
    department: str
    is_contracted: bool = True


def normalize_text(text: str) -> str:
    """
    文字正規化處理
    - 繁簡轉換
    - 全形半形轉換
    - 移除空白與標點
    - 統一大小寫
    """
    if not text:
        return ""

    # 移除多餘空白
    text = re.sub(r'\s+', '', text)

    # 移除常見標點符號和括號內容
    text = re.sub(r'[（）()【】\[\]「」""''、，。！？：；]', '', text)

    # 轉為小寫
    text = text.lower()

    # Unicode 正規化 (NFD -> NFC)
    text = unicodedata.normalize('NFC', text)

    # 簡化的繁簡轉換對應表
    traditional_to_simplified = {
        '臺': '台', '醫': '医', '學': '学', '國': '国', '總': '总',
        '區': '区', '號': '号', '榮': '荣', '軍': '军', '湖': '湖',
        '內': '内', '灣': '湾', '診': '诊', '療': '疗', '院': '院',
        '民': '民', '路': '路', '段': '段', '巷': '巷', '弄': '弄',
        '市': '市', '縣': '县', '鄉': '乡', '鎮': '镇', '村': '村',
        '義': '义', '設': '设', '附': '附', '立': '立', '灣': '湾'
    }

    for trad, simp in traditional_to_simplified.items():
        text = text.replace(trad, simp)

    return text


def normalize_hospital_name(name: str) -> str:
    """
    醫院名稱正規化
    處理常見的醫院名稱變體和縮寫
    """
    if not name:
        return ""

    # 基本正規化
    normalized = normalize_text(name)

    # 醫院名稱特定轉換規則（完整比對）
    name_mappings = {
        '国立台湾大学医学院附设医院': '台湾大学医院',
        '台湾大学医学院附设医院': '台湾大学医院',
        '台大医学院附设医院': '台大医院',
        '台北荣民总医院': '荣民总医院',
        '台北荣总': '荣民总医院',
        '荣总': '荣民总医院',
        '三军总医院': '三军总医院',
        '三总': '三军总医院'
    }

    # 檢查完整匹配
    if normalized in name_mappings:
        return name_mappings[normalized]

    # 檢查是否包含對應的標準化名稱
    for variant, standard in name_mappings.items():
        if variant in normalized:
            return standard

    return normalized


def normalize_address(address: str) -> str:
    """
    地址正規化
    處理常見的地址變體
    """
    if not address:
        return ""

    # 基本正規化
    normalized = normalize_text(address)

    # 地址特定轉換
    address_mappings = {
        '台北市': '台北市',
        '新北市': '新北市',
        '桃园市': '桃园市',
        '台中市': '台中市',
        '台南市': '台南市',
        '高雄市': '高雄市'
    }

    for variant, standard in address_mappings.items():
        normalized = normalized.replace(variant, standard)

    return normalized


def extract_address_keywords(address: str) -> List[str]:
    """
    提取地址關鍵字用於比對
    """
    normalized = normalize_address(address)

    # 提取關鍵詞：區域、路名、段號等
    keywords = []

    # 區域名稱 (XX區、XX市)
    area_match = re.search(r'([\u4e00-\u9fff]+[区市])', normalized)
    if area_match:
        keywords.append(area_match.group(1))

    # 路名 (XX路、XX街)
    road_matches = re.findall(r'([\u4e00-\u9fff]+[路街道巷弄])', normalized)
    keywords.extend(road_matches)

    # 段號
    section_matches = re.findall(r'([一二三四五六七八九十\d]+段)', normalized)
    keywords.extend(section_matches)

    return keywords


def calculate_match_score(place_name: str, place_address: str,
                         registry_name: str, registry_address: str) -> float:
    """
    計算比對分數 (0.0 - 1.0)

    Args:
        place_name: Google Places 醫院名稱
        place_address: Google Places 地址
        registry_name: 健保名冊醫院名稱
        registry_address: 健保名冊地址

    Returns:
        float: 比對分數，1.0 為完全符合
    """
    score = 0.0

    # 名稱比對 (權重 0.6)
    norm_place_name = normalize_hospital_name(place_name)
    norm_registry_name = normalize_hospital_name(registry_name)

    if norm_place_name == norm_registry_name:
        score += 0.6  # 完全符合
    elif norm_place_name in norm_registry_name or norm_registry_name in norm_place_name:
        score += 0.4  # 部分符合
    elif any(word in norm_registry_name for word in norm_place_name.split() if len(word) > 1):
        score += 0.2  # 關鍵字符合

    # 地址比對 (權重 0.4)
    if place_address and registry_address:
        norm_place_addr = normalize_address(place_address)
        norm_registry_addr = normalize_address(registry_address)

        if norm_place_addr == norm_registry_addr:
            score += 0.4  # 完全符合
        else:
            # 檢查關鍵字符合
            place_keywords = extract_address_keywords(place_address)
            registry_keywords = extract_address_keywords(registry_address)

            if place_keywords and registry_keywords:
                common_keywords = set(place_keywords) & set(registry_keywords)
                keyword_ratio = len(common_keywords) / max(len(place_keywords), len(registry_keywords))
                score += 0.4 * keyword_ratio

    return score


def load_nhia_registry(file_path: str) -> List[NHIARegistryEntry]:
    """
    載入健保特約醫療院所名冊

    Args:
        file_path: JSON 格式的名冊檔案路徑

    Returns:
        List[NHIARegistryEntry]: 健保院所記錄列表
    """
    try:
        if not Path(file_path).exists():
            return []

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        registry = []
        for item in data:
            try:
                entry = NHIARegistryEntry(
                    hospital_code=item.get('hospital_code', ''),
                    hospital_name=item.get('hospital_name', ''),
                    address=item.get('address', ''),
                    phone=item.get('phone', ''),
                    type=item.get('type', ''),
                    department=item.get('department', ''),
                    is_contracted=item.get('is_contracted', True)
                )
                registry.append(entry)
            except (KeyError, TypeError):
                # 跳過格式錯誤的記錄
                continue

        return registry

    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        # 檔案不存在、JSON 格式錯誤或編碼錯誤時返回空列表
        return []


def match_from_registry(place: 'PlaceResult', registry: List[NHIARegistryEntry],
                       threshold: float = 0.5) -> Optional[NHIARegistryEntry]:
    """
    從健保名冊中查找比對結果

    Args:
        place: Google Places 搜尋結果
        registry: 健保院所名冊
        threshold: 比對門檻值 (0.0-1.0)

    Returns:
        Optional[NHIARegistryEntry]: 比對到的健保院所記錄，無比對時返回 None
    """
    if not registry:
        return None

    best_match = None
    best_score = 0.0

    for entry in registry:
        score = calculate_match_score(
            place.name,
            place.address,
            entry.hospital_name,
            entry.address
        )

        if score > best_score and score >= threshold:
            best_score = score
            best_match = entry

    return best_match


def enhance_places_with_nhia_info(places: List['PlaceResult'],
                                 registry_file_path: str = None) -> List[Dict[str, Any]]:
    """
    為 Google Places 結果增加健保資訊

    Args:
        places: Google Places 搜尋結果列表
        registry_file_path: 健保名冊檔案路徑，若為 None 則使用預設路徑

    Returns:
        List[Dict]: 增強後的醫院資訊列表
    """
    # 載入健保名冊
    if registry_file_path is None:
        # 使用預設的健保名冊檔案路徑
        registry_file_path = "data/nhia_registry.json"

    registry = load_nhia_registry(registry_file_path)

    enhanced_results = []
    for place in places:
        # 基本場所資訊
        result = {
            "id": place.id,
            "name": place.name,
            "address": place.address,
            "latitude": place.latitude,
            "longitude": place.longitude,
            "distance_meters": place.distance_meters
        }

        # 可選欄位
        if place.phone:
            result["phone"] = place.phone
        if place.rating is not None:
            result["rating"] = place.rating
        if place.is_open_now is not None:
            result["is_open_now"] = place.is_open_now
        if place.opening_hours:
            result["opening_hours"] = place.opening_hours
        if place.business_status != "UNKNOWN":
            result["business_status"] = place.business_status

        # 嘗試健保比對
        try:
            nhia_match = match_from_registry(place, registry)
            if nhia_match:
                result["is_contracted"] = nhia_match.is_contracted
                result["hospital_code"] = nhia_match.hospital_code
                result["nhia_type"] = nhia_match.type
                result["nhia_department"] = nhia_match.department
                if nhia_match.phone and not place.phone:
                    result["phone"] = nhia_match.phone
            else:
                result["is_contracted"] = None

        except Exception:
            # 健保比對失敗不影響主要功能
            result["is_contracted"] = None

        enhanced_results.append(result)

    return enhanced_results


def get_nhia_statistics(registry: List[NHIARegistryEntry]) -> Dict[str, Any]:
    """
    取得健保名冊統計資訊

    Args:
        registry: 健保院所名冊

    Returns:
        Dict: 統計資訊
    """
    if not registry:
        return {
            "total_count": 0,
            "by_type": {},
            "by_department": {},
            "contracted_count": 0
        }

    # 按類型統計
    type_counts = {}
    for entry in registry:
        type_counts[entry.type] = type_counts.get(entry.type, 0) + 1

    # 按科別統計
    dept_counts = {}
    for entry in registry:
        dept_counts[entry.department] = dept_counts.get(entry.department, 0) + 1

    # 特約院所數量
    contracted_count = sum(1 for entry in registry if entry.is_contracted)

    return {
        "total_count": len(registry),
        "by_type": type_counts,
        "by_department": dept_counts,
        "contracted_count": contracted_count,
        "contract_ratio": contracted_count / len(registry) if registry else 0
    }