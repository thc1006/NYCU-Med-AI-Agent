"""
Pytest configuration file for Taiwan Medical AI Assistant tests.
Provides shared fixtures and test configuration.
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session")
def sample_health_data_yaml(test_data_dir):
    """Create sample health data YAML file for testing"""
    health_data = {
        "topics": [
            {
                "id": "medical_process",
                "title": "就醫流程指引",
                "summary": "了解台灣醫療體系的就醫流程，包括掛號、看診、檢查等步驟",
                "url": "https://www.mohw.gov.tw/medical-process",
                "category": "medical_guidance",
                "priority": 1,
                "last_updated": "2024-01-15"
            },
            {
                "id": "nhi_query",
                "title": "健保查詢服務",
                "summary": "查詢健保給付項目、醫療院所特約資訊及個人健保資料",
                "url": "https://www.nhi.gov.tw/query-services",
                "category": "insurance",
                "priority": 2,
                "last_updated": "2024-01-10"
            },
            {
                "id": "emergency_guidance",
                "title": "急診就醫指引",
                "summary": "緊急醫療情況的處理原則、急診流程及注意事項",
                "url": "https://www.mohw.gov.tw/emergency-guide",
                "category": "emergency",
                "priority": 1,
                "last_updated": "2024-01-20"
            }
        ],
        "resources": [
            {
                "id": "mohw_portal",
                "title": "衛生福利部",
                "description": "中華民國衛生福利部官方網站",
                "url": "https://www.mohw.gov.tw",
                "type": "government",
                "language": "zh-TW",
                "category": "primary"
            },
            {
                "id": "nhi_portal",
                "title": "全民健康保險署",
                "description": "全民健康保險署官方網站",
                "url": "https://www.nhi.gov.tw",
                "type": "government",
                "language": "zh-TW",
                "category": "insurance"
            }
        ]
    }

    yaml_file = test_data_dir / "health_data.yaml"
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(health_data, f, default_flow_style=False, allow_unicode=True)

    return yaml_file


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing"""
    test_env = {
        "DEFAULT_LANG": "zh-TW",
        "REGION": "TW",
        "GOOGLE_PLACES_API_KEY": "test-api-key-for-testing",
        "HEALTH_DATA_PATH": "data/health_info.yaml",
        "LOG_LEVEL": "DEBUG"
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


@pytest.fixture
def traditional_chinese_test_strings():
    """Provide test strings for Traditional Chinese validation"""
    return {
        "medical_terms": [
            "醫療", "診療", "護理", "檢查", "治療", "手術", "病患", "醫師", "護士",
            "醫院", "診所", "急診", "門診", "住院", "病房", "藥物", "處方", "疫苗"
        ],
        "insurance_terms": [
            "健保", "保險", "給付", "部分負擔", "醫療費用", "健保卡", "保險費",
            "醫療院所", "特約", "核退", "申請", "查詢", "服務"
        ],
        "emergency_terms": [
            "急診", "緊急", "救護", "消防", "救護車", "急救", "危急", "重症",
            "搶救", "急診室", "急診科", "緊急醫療", "生命徵象"
        ],
        "prevention_terms": [
            "預防", "保健", "疫苗", "接種", "健康檢查", "篩檢", "追蹤", "預防接種",
            "免疫", "抗體", "疫情", "防疫", "衛生", "健康促進"
        ]
    }


@pytest.fixture
def url_validation_patterns():
    """Provide regex patterns for URL validation"""
    import re

    return {
        "general_url": re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE
        ),
        "gov_tw_url": re.compile(r'^https://[a-zA-Z0-9.-]*\.gov\.tw', re.IGNORECASE),
        "nhi_url": re.compile(r'^https://[a-zA-Z0-9.-]*nhi\.gov\.tw', re.IGNORECASE),
        "mohw_url": re.compile(r'^https://[a-zA-Z0-9.-]*mohw\.gov\.tw', re.IGNORECASE),
        "cdc_url": re.compile(r'^https://[a-zA-Z0-9.-]*cdc\.gov\.tw', re.IGNORECASE)
    }


@pytest.fixture
def expected_emergency_numbers():
    """Provide expected emergency numbers for Taiwan"""
    return {
        "119": "消防救護車",
        "112": "行動電話國際緊急號碼",
        "110": "警察局",
        "113": "婦幼保護專線",
        "165": "反詐騙諮詢專線"
    }


@pytest.fixture
def health_info_api_endpoints():
    """Provide list of health info API endpoints for testing"""
    return [
        "/v1/health-info/topics",
        "/v1/health-info/resources",
        "/v1/health-info/vaccinations",
        "/v1/health-info/insurance"
    ]


@pytest.fixture
def required_topic_categories():
    """Provide required health topic categories"""
    return [
        "medical_guidance",
        "insurance",
        "emergency",
        "prevention"
    ]


@pytest.fixture
def required_coverage_types():
    """Provide required insurance coverage types"""
    return [
        "outpatient",
        "inpatient",
        "emergency",
        "dental",
        "chinese_medicine",
        "preventive"
    ]


# pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "traditional_chinese: mark test as Traditional Chinese validation"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location"""
    for item in items:
        # Mark tests by directory
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Mark Traditional Chinese tests
        if "traditional_chinese" in item.name or "zh_TW" in item.name:
            item.add_marker(pytest.mark.traditional_chinese)