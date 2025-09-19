"""
Unit tests for static health information service.
Tests the health information data structures and static content validation.
"""

import pytest
import yaml
import json
from typing import Dict, List, Any
from pathlib import Path

# Mock health info service that will be implemented
class MockHealthInfoService:
    """Mock health info service for testing data structures"""

    def __init__(self, data_source: Dict[str, Any]):
        self.data = data_source

    def get_topics(self) -> List[Dict[str, str]]:
        return self.data.get("topics", [])

    def get_resources(self) -> List[Dict[str, str]]:
        return self.data.get("resources", [])

    def get_vaccinations(self) -> Dict[str, Any]:
        return self.data.get("vaccinations", {})

    def get_insurance_info(self) -> Dict[str, Any]:
        return self.data.get("insurance", {})


class TestHealthInfoStatic:
    """Test static health information data structures and content"""

    @pytest.fixture
    def sample_health_data(self) -> Dict[str, Any]:
        """Sample health data that mimics the expected YAML/JSON structure"""
        return {
            "topics": [
                {
                    "id": "medical_process",
                    "title": "就醫流程指引",
                    "summary": "了解台灣醫療體系的就醫流程，包括掛號、看診、檢查等步驟",
                    "url": "https://www.mohw.gov.tw/medical-process",
                    "category": "medical_guidance",
                    "priority": 1
                },
                {
                    "id": "nhi_query",
                    "title": "健保查詢服務",
                    "summary": "查詢健保給付項目、醫療院所特約資訊及個人健保資料",
                    "url": "https://www.nhi.gov.tw/query-services",
                    "category": "insurance",
                    "priority": 2
                },
                {
                    "id": "emergency_guidance",
                    "title": "急診就醫指引",
                    "summary": "緊急醫療情況的處理原則、急診流程及注意事項",
                    "url": "https://www.mohw.gov.tw/emergency-guide",
                    "category": "emergency",
                    "priority": 1
                },
                {
                    "id": "health_checkup",
                    "title": "預防保健服務",
                    "summary": "成人健康檢查、癌症篩檢及其他預防保健項目說明",
                    "url": "https://www.hpa.gov.tw/health-checkup",
                    "category": "prevention",
                    "priority": 3
                }
            ],
            "resources": [
                {
                    "id": "mohw_portal",
                    "title": "衛生福利部",
                    "description": "中華民國衛生福利部官方網站",
                    "url": "https://www.mohw.gov.tw",
                    "type": "government",
                    "language": "zh-TW"
                },
                {
                    "id": "nhi_portal",
                    "title": "全民健康保險署",
                    "description": "全民健康保險署官方網站",
                    "url": "https://www.nhi.gov.tw",
                    "type": "government",
                    "language": "zh-TW"
                },
                {
                    "id": "cdc_portal",
                    "title": "疾病管制署",
                    "description": "衛生福利部疾病管制署官方網站",
                    "url": "https://www.cdc.gov.tw",
                    "type": "government",
                    "language": "zh-TW"
                },
                {
                    "id": "hpa_portal",
                    "title": "國民健康署",
                    "description": "衛生福利部國民健康署官方網站",
                    "url": "https://www.hpa.gov.tw",
                    "type": "government",
                    "language": "zh-TW"
                }
            ],
            "vaccinations": {
                "children": {
                    "title": "兒童疫苗接種時程",
                    "description": "依據疾病管制署公布之兒童常規疫苗接種時程",
                    "schedule": [
                        {
                            "age": "出生24小時內",
                            "vaccines": ["B型肝炎疫苗第1劑", "卡介苗"],
                            "notes": "應於出生後儘速接種"
                        },
                        {
                            "age": "出生滿1個月",
                            "vaccines": ["B型肝炎疫苗第2劑"],
                            "notes": "與第1劑間隔至少1個月"
                        },
                        {
                            "age": "出生滿2個月",
                            "vaccines": ["白喉破傷風百日咳、b型嗜血桿菌及不活化小兒麻痺五合一疫苗第1劑", "13價結合型肺炎鏈球菌疫苗第1劑", "輪狀病毒疫苗第1劑"],
                            "notes": "可同時接種不同疫苗"
                        }
                    ],
                    "source_url": "https://www.cdc.gov.tw/Category/Page/h2RHafMjIgXBvqPaRA9nKQ"
                },
                "adults": {
                    "title": "成人疫苗接種建議",
                    "description": "成人常規疫苗接種建議時程",
                    "recommendations": [
                        {
                            "vaccine": "流感疫苗",
                            "frequency": "每年1劑",
                            "target_group": "所有成人",
                            "notes": "建議每年10月開始接種"
                        },
                        {
                            "vaccine": "COVID-19疫苗",
                            "frequency": "依疫情狀況調整",
                            "target_group": "所有成人",
                            "notes": "依據中央流行疫情指揮中心建議"
                        }
                    ],
                    "source_url": "https://www.cdc.gov.tw/Category/Page/4Hj-ARQcxzQvXflMg6hU_g"
                }
            },
            "insurance": {
                "basic_info": {
                    "title": "全民健康保險基本資訊",
                    "description": "全民健康保險制度基本介紹與保險對象權益",
                    "coverage": {
                        "outpatient": "門診醫療",
                        "inpatient": "住院醫療",
                        "emergency": "急診醫療",
                        "dental": "牙醫醫療",
                        "chinese_medicine": "中醫醫療",
                        "preventive": "預防保健",
                        "rehabilitation": "復健治療",
                        "home_care": "居家照護"
                    },
                    "copayment": {
                        "outpatient": "門診部分負擔：50-420元",
                        "emergency": "急診部分負擔：150-550元",
                        "inpatient": "住院部分負擔：5-30%"
                    }
                },
                "services": [
                    {
                        "name": "健保卡申請",
                        "description": "健保卡首次申請、換發、補發服務",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=F1E9736C40AB4E65",
                        "contact": "0800-030-598"
                    },
                    {
                        "name": "保險費查詢",
                        "description": "個人保險費繳費紀錄查詢服務",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=AB41370000B72ED6",
                        "contact": "0800-030-598"
                    },
                    {
                        "name": "醫療費用核退",
                        "description": "自墊醫療費用核退申請",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=E9A0EDFE3D127C9B",
                        "contact": "0800-030-598"
                    }
                ],
                "emergency_numbers": ["119", "112"],
                "nhi_hotline": "0800-030-598"
            }
        }

    @pytest.fixture
    def health_service(self, sample_health_data) -> MockHealthInfoService:
        """Create mock health info service with sample data"""
        return MockHealthInfoService(sample_health_data)

    def test_topics_structure(self, health_service):
        """Test that health topics have correct structure"""
        topics = health_service.get_topics()

        assert isinstance(topics, list)
        assert len(topics) > 0

        for topic in topics:
            # Required fields
            assert "id" in topic
            assert "title" in topic
            assert "summary" in topic
            assert "url" in topic
            assert "category" in topic
            assert "priority" in topic

            # Data types
            assert isinstance(topic["id"], str)
            assert isinstance(topic["title"], str)
            assert isinstance(topic["summary"], str)
            assert isinstance(topic["url"], str)
            assert isinstance(topic["category"], str)
            assert isinstance(topic["priority"], int)

            # Content validation
            assert len(topic["title"]) > 0
            assert len(topic["summary"]) > 0
            assert topic["url"].startswith("http")
            assert topic["priority"] in [1, 2, 3]  # Priority levels

    def test_topics_traditional_chinese(self, health_service):
        """Test that all topic content is in Traditional Chinese"""
        topics = health_service.get_topics()

        # Check for Traditional Chinese characters in titles and summaries
        traditional_chinese_indicators = ["醫", "診", "檢", "療", "護", "康", "險", "劑"]

        for topic in topics:
            title_has_chinese = any(char in topic["title"] for char in traditional_chinese_indicators)
            summary_has_chinese = any(char in topic["summary"] for char in traditional_chinese_indicators)

            # At least one of title or summary should contain Traditional Chinese
            assert title_has_chinese or summary_has_chinese, f"Topic {topic['id']} should contain Traditional Chinese characters"

    def test_topics_required_categories(self, health_service):
        """Test that required health topic categories are present"""
        topics = health_service.get_topics()
        categories = [topic["category"] for topic in topics]

        required_categories = ["medical_guidance", "insurance", "emergency", "prevention"]

        for required_cat in required_categories:
            assert required_cat in categories, f"Required category '{required_cat}' not found in topics"

    def test_resources_structure(self, health_service):
        """Test that health resources have correct structure"""
        resources = health_service.get_resources()

        assert isinstance(resources, list)
        assert len(resources) > 0

        for resource in resources:
            # Required fields
            assert "id" in resource
            assert "title" in resource
            assert "description" in resource
            assert "url" in resource
            assert "type" in resource
            assert "language" in resource

            # Data types
            assert isinstance(resource["title"], str)
            assert isinstance(resource["description"], str)
            assert isinstance(resource["url"], str)
            assert isinstance(resource["type"], str)
            assert isinstance(resource["language"], str)

            # Content validation
            assert len(resource["title"]) > 0
            assert len(resource["description"]) > 0
            assert resource["url"].startswith("http")
            assert resource["language"] == "zh-TW"

    def test_resources_government_urls(self, health_service):
        """Test that government resources use .gov.tw domains"""
        resources = health_service.get_resources()

        government_resources = [r for r in resources if r["type"] == "government"]
        assert len(government_resources) > 0, "Should have government resources"

        for resource in government_resources:
            assert ".gov.tw" in resource["url"], f"Government resource {resource['id']} should use .gov.tw domain"

    def test_vaccinations_structure(self, health_service):
        """Test vaccination information structure"""
        vaccinations = health_service.get_vaccinations()

        assert isinstance(vaccinations, dict)
        assert "children" in vaccinations
        assert "adults" in vaccinations

        # Children vaccination structure
        children = vaccinations["children"]
        assert "title" in children
        assert "description" in children
        assert "schedule" in children
        assert "source_url" in children

        assert isinstance(children["schedule"], list)
        assert len(children["schedule"]) > 0

        for schedule_item in children["schedule"]:
            assert "age" in schedule_item
            assert "vaccines" in schedule_item
            assert "notes" in schedule_item
            assert isinstance(schedule_item["vaccines"], list)

        # Adults vaccination structure
        adults = vaccinations["adults"]
        assert "title" in adults
        assert "description" in adults
        assert "recommendations" in adults
        assert "source_url" in adults

        assert isinstance(adults["recommendations"], list)
        for recommendation in adults["recommendations"]:
            assert "vaccine" in recommendation
            assert "frequency" in recommendation
            assert "target_group" in recommendation

    def test_vaccinations_traditional_chinese(self, health_service):
        """Test vaccination information uses Traditional Chinese"""
        vaccinations = health_service.get_vaccinations()

        # Check children vaccination titles and descriptions
        children = vaccinations["children"]
        assert any(char in children["title"] for char in ["兒", "童", "疫", "苗", "接", "種"])
        assert any(char in children["description"] for char in ["疾", "病", "管", "制", "署"])

        # Check adults vaccination titles and descriptions
        adults = vaccinations["adults"]
        assert any(char in adults["title"] for char in ["成", "人", "疫", "苗", "接", "種"])

        # Check vaccine names are in Traditional Chinese
        for recommendation in adults["recommendations"]:
            vaccine_name = recommendation["vaccine"]
            if "流感" in vaccine_name or "疫苗" in vaccine_name:
                assert True  # Contains Traditional Chinese
            elif "COVID-19" in vaccine_name:
                assert True  # English name is acceptable for COVID-19
            else:
                # Should contain Traditional Chinese characters
                assert any(char in vaccine_name for char in ["疫", "苗", "炎", "菌"])

    def test_insurance_structure(self, health_service):
        """Test insurance information structure"""
        insurance = health_service.get_insurance_info()

        assert isinstance(insurance, dict)
        assert "basic_info" in insurance
        assert "services" in insurance
        assert "emergency_numbers" in insurance
        assert "nhi_hotline" in insurance

        # Basic info structure
        basic_info = insurance["basic_info"]
        assert "title" in basic_info
        assert "description" in basic_info
        assert "coverage" in basic_info
        assert "copayment" in basic_info

        # Services structure
        services = insurance["services"]
        assert isinstance(services, list)
        assert len(services) > 0

        for service in services:
            assert "name" in service
            assert "description" in service
            assert "url" in service
            assert "contact" in service
            assert service["url"].startswith("http")

        # Emergency numbers
        emergency_numbers = insurance["emergency_numbers"]
        assert isinstance(emergency_numbers, list)
        assert "119" in emergency_numbers
        assert "112" in emergency_numbers

        # NHI hotline
        assert isinstance(insurance["nhi_hotline"], str)
        assert "0800" in insurance["nhi_hotline"]

    def test_insurance_traditional_chinese(self, health_service):
        """Test insurance information uses Traditional Chinese"""
        insurance = health_service.get_insurance_info()

        basic_info = insurance["basic_info"]

        # Title should contain Traditional Chinese
        assert any(char in basic_info["title"] for char in ["全", "民", "健", "康", "保", "險"])

        # Coverage should use Traditional Chinese - check the actual service data structure
        coverage = basic_info["coverage"]
        for coverage_type, coverage_data in coverage.items():
            # Check if it's a string (mock) or InsuranceCoverage object (real service)
            if isinstance(coverage_data, str):
                description = coverage_data
            else:
                # Assume it has a 'name' or 'description' attribute for real service
                description = getattr(coverage_data, 'name', '') + getattr(coverage_data, 'description', '')
            # Use broader set of Traditional Chinese characters found in coverage data
            assert any(char in description for char in ["門", "診", "住", "院", "醫", "療", "服", "務", "預", "防", "保", "健", "居", "家", "照", "護", "復", "治", "牙", "中"])

        # Copayment should use Traditional Chinese
        copayment = basic_info["copayment"]
        for payment_type, payment_data in copayment.items():
            if isinstance(payment_data, str):
                description = payment_data
            else:
                # Handle InsuranceCopayment object
                description = getattr(payment_data, 'description', '') + getattr(payment_data, 'amount', '') + getattr(payment_data, 'details', '')
            assert any(char in description for char in ["部", "分", "負", "擔", "元", "醫", "療"])

        # Services should use Traditional Chinese
        services = insurance["services"]
        for service in services:
            service_name = service["name"] if isinstance(service, dict) else getattr(service, 'name', '')
            assert any(char in service_name for char in ["健", "保", "卡", "費", "查", "詢", "核", "退", "申", "請"])

    def test_insurance_nhi_urls(self, health_service):
        """Test that NHI services use correct government URLs"""
        insurance = health_service.get_insurance_info()
        services = insurance["services"]

        for service in services:
            url = service["url"]
            assert "nhi.gov.tw" in url, f"NHI service {service['name']} should use nhi.gov.tw domain"

    def test_data_completeness(self, health_service):
        """Test that all major data sections are complete"""
        # Test all methods return non-empty data
        topics = health_service.get_topics()
        resources = health_service.get_resources()
        vaccinations = health_service.get_vaccinations()
        insurance = health_service.get_insurance_info()

        assert len(topics) >= 3, "Should have at least 3 health topics"
        assert len(resources) >= 3, "Should have at least 3 health resources"
        assert len(vaccinations) >= 2, "Should have children and adults vaccination info"
        assert len(insurance) >= 4, "Should have complete insurance information"

        # Test priority topics are present
        topic_ids = [topic["id"] for topic in topics]
        required_topics = ["medical_process", "nhi_query", "emergency_guidance"]

        for required_topic in required_topics:
            assert required_topic in topic_ids, f"Required topic '{required_topic}' not found"

    def test_url_format_validation(self, health_service):
        """Test that all URLs follow proper format"""
        import re

        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # Check topic URLs
        topics = health_service.get_topics()
        for topic in topics:
            assert url_pattern.match(topic["url"]), f"Invalid URL format in topic {topic['id']}: {topic['url']}"

        # Check resource URLs
        resources = health_service.get_resources()
        for resource in resources:
            assert url_pattern.match(resource["url"]), f"Invalid URL format in resource {resource['id']}: {resource['url']}"

        # Check vaccination source URLs
        vaccinations = health_service.get_vaccinations()
        children_url = vaccinations["children"]["source_url"]
        adults_url = vaccinations["adults"]["source_url"]

        assert url_pattern.match(children_url), f"Invalid URL format in children vaccination: {children_url}"
        assert url_pattern.match(adults_url), f"Invalid URL format in adults vaccination: {adults_url}"

        # Check insurance service URLs
        insurance = health_service.get_insurance_info()
        for service in insurance["services"]:
            assert url_pattern.match(service["url"]), f"Invalid URL format in insurance service {service['name']}: {service['url']}"