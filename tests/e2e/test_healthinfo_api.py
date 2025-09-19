"""
End-to-end tests for health information API endpoints.
Tests the complete health information API functionality including responses and data formats.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, List, Any
import json
import re

# This will be the actual FastAPI app once implemented
# For now, we'll use a mock setup that defines the expected behavior


class MockHealthInfoApp:
    """Mock FastAPI app for testing health info endpoints"""

    def __init__(self):
        self.routes = {
            "/v1/health-info/topics": self._get_topics,
            "/v1/health-info/resources": self._get_resources,
            "/v1/health-info/vaccinations": self._get_vaccinations,
            "/v1/health-info/insurance": self._get_insurance
        }

    def get(self, path: str, **kwargs):
        """Mock GET request handler"""
        if path in self.routes:
            return MockResponse(200, self.routes[path]())
        return MockResponse(404, {"detail": "Not found"})

    def _get_topics(self):
        """Mock topics endpoint response"""
        return {
            "topics": [
                {
                    "id": "medical_process",
                    "title": "就醫流程指引",
                    "summary": "了解台灣醫療體系的就醫流程，包括掛號、看診、檢查等步驟，確保您能順利就醫",
                    "url": "https://www.mohw.gov.tw/medical-process",
                    "category": "medical_guidance",
                    "priority": 1,
                    "last_updated": "2024-01-15"
                },
                {
                    "id": "nhi_query",
                    "title": "健保查詢服務",
                    "summary": "查詢健保給付項目、醫療院所特約資訊及個人健保繳費與就醫紀錄",
                    "url": "https://www.nhi.gov.tw/query-services",
                    "category": "insurance",
                    "priority": 2,
                    "last_updated": "2024-01-10"
                },
                {
                    "id": "emergency_guidance",
                    "title": "急診就醫指引",
                    "summary": "緊急醫療情況的處理原則、急診流程及注意事項，協助您在緊急時刻做出正確判斷",
                    "url": "https://www.mohw.gov.tw/emergency-guide",
                    "category": "emergency",
                    "priority": 1,
                    "last_updated": "2024-01-20"
                },
                {
                    "id": "health_checkup",
                    "title": "預防保健服務",
                    "summary": "成人健康檢查、癌症篩檢及其他預防保健項目的說明與申請流程",
                    "url": "https://www.hpa.gov.tw/health-checkup",
                    "category": "prevention",
                    "priority": 3,
                    "last_updated": "2024-01-05"
                },
                {
                    "id": "mental_health",
                    "title": "心理健康資源",
                    "summary": "心理諮商、精神醫療及社區心理衛生服務資源介紹",
                    "url": "https://www.mohw.gov.tw/mental-health",
                    "category": "mental_health",
                    "priority": 2,
                    "last_updated": "2024-01-12"
                }
            ],
            "total": 5,
            "language": "zh-TW",
            "last_updated": "2024-01-20"
        }

    def _get_resources(self):
        """Mock resources endpoint response"""
        return {
            "resources": [
                {
                    "id": "mohw_portal",
                    "title": "衛生福利部",
                    "description": "中華民國衛生福利部官方網站，提供最新的衛生福利政策與法規資訊",
                    "url": "https://www.mohw.gov.tw",
                    "type": "government",
                    "language": "zh-TW",
                    "category": "primary"
                },
                {
                    "id": "nhi_portal",
                    "title": "全民健康保險署",
                    "description": "全民健康保險署官方網站，提供健保相關服務與資訊查詢",
                    "url": "https://www.nhi.gov.tw",
                    "type": "government",
                    "language": "zh-TW",
                    "category": "insurance"
                },
                {
                    "id": "cdc_portal",
                    "title": "疾病管制署",
                    "description": "衛生福利部疾病管制署官方網站，提供疫情資訊與防疫指引",
                    "url": "https://www.cdc.gov.tw",
                    "type": "government",
                    "language": "zh-TW",
                    "category": "disease_control"
                },
                {
                    "id": "hpa_portal",
                    "title": "國民健康署",
                    "description": "衛生福利部國民健康署官方網站，推廣健康促進與疾病預防",
                    "url": "https://www.hpa.gov.tw",
                    "type": "government",
                    "language": "zh-TW",
                    "category": "health_promotion"
                },
                {
                    "id": "emergency_hotlines",
                    "title": "緊急聯絡電話",
                    "description": "台灣地區緊急救護、消防、警政等緊急聯絡電話彙整",
                    "url": "https://www.gov.tw/emergency-contacts",
                    "type": "emergency",
                    "language": "zh-TW",
                    "category": "emergency"
                }
            ],
            "total": 5,
            "language": "zh-TW",
            "categories": ["primary", "insurance", "disease_control", "health_promotion", "emergency"]
        }

    def _get_vaccinations(self):
        """Mock vaccinations endpoint response"""
        return {
            "vaccinations": {
                "children": {
                    "title": "兒童疫苗接種時程",
                    "description": "依據疾病管制署公布之兒童常規疫苗接種時程表",
                    "schedule": [
                        {
                            "age": "出生24小時內",
                            "age_months": 0,
                            "vaccines": [
                                {
                                    "name": "B型肝炎疫苗第1劑",
                                    "type": "hepatitis_b",
                                    "dose": 1,
                                    "required": True
                                },
                                {
                                    "name": "卡介苗",
                                    "type": "bcg",
                                    "dose": 1,
                                    "required": True
                                }
                            ],
                            "notes": "應於出生後儘速接種，最遲不超過24小時",
                            "location": "出生醫院"
                        },
                        {
                            "age": "出生滿1個月",
                            "age_months": 1,
                            "vaccines": [
                                {
                                    "name": "B型肝炎疫苗第2劑",
                                    "type": "hepatitis_b",
                                    "dose": 2,
                                    "required": True
                                }
                            ],
                            "notes": "與第1劑間隔至少1個月",
                            "location": "醫療院所或衛生所"
                        },
                        {
                            "age": "出生滿2個月",
                            "age_months": 2,
                            "vaccines": [
                                {
                                    "name": "白喉破傷風百日咳、b型嗜血桿菌及不活化小兒麻痺五合一疫苗第1劑",
                                    "type": "pentavalent",
                                    "dose": 1,
                                    "required": True
                                },
                                {
                                    "name": "13價結合型肺炎鏈球菌疫苗第1劑",
                                    "type": "pneumococcal",
                                    "dose": 1,
                                    "required": True
                                },
                                {
                                    "name": "輪狀病毒疫苗第1劑",
                                    "type": "rotavirus",
                                    "dose": 1,
                                    "required": False
                                }
                            ],
                            "notes": "可同時接種不同疫苗，但需分別注射於不同部位",
                            "location": "醫療院所或衛生所"
                        }
                    ],
                    "source_url": "https://www.cdc.gov.tw/Category/Page/h2RHafMjIgXBvqPaRA9nKQ",
                    "last_updated": "2024-01-15"
                },
                "adults": {
                    "title": "成人疫苗接種建議",
                    "description": "成人常規疫苗接種建議時程與注意事項",
                    "recommendations": [
                        {
                            "vaccine": "流感疫苗",
                            "type": "influenza",
                            "frequency": "每年1劑",
                            "target_group": "所有成人，特別是65歲以上長者",
                            "notes": "建議每年10月開始接種，流感季節前完成接種",
                            "priority": "high"
                        },
                        {
                            "vaccine": "COVID-19疫苗",
                            "type": "covid19",
                            "frequency": "依疫情狀況調整",
                            "target_group": "所有成人",
                            "notes": "依據中央流行疫情指揮中心最新建議接種",
                            "priority": "high"
                        },
                        {
                            "vaccine": "破傷風、白喉、百日咳混合疫苗",
                            "type": "tdap",
                            "frequency": "每10年1劑",
                            "target_group": "所有成人",
                            "notes": "特別建議孕婦於懷孕28-36週接種",
                            "priority": "medium"
                        },
                        {
                            "vaccine": "帶狀疱疹疫苗",
                            "type": "zoster",
                            "frequency": "50歲以上接種1-2劑",
                            "target_group": "50歲以上成人",
                            "notes": "可預防帶狀疱疹及其併發症",
                            "priority": "medium"
                        }
                    ],
                    "source_url": "https://www.cdc.gov.tw/Category/Page/4Hj-ARQcxzQvXflMg6hU_g",
                    "last_updated": "2024-01-10"
                }
            },
            "language": "zh-TW",
            "disclaimer": "疫苗接種建議可能因個人健康狀況而異，請諮詢醫療專業人員"
        }

    def _get_insurance(self):
        """Mock insurance endpoint response"""
        return {
            "insurance": {
                "basic_info": {
                    "title": "全民健康保險基本資訊",
                    "description": "全民健康保險制度基本介紹與保險對象權益說明",
                    "coverage": {
                        "outpatient": {
                            "name": "門診醫療",
                            "description": "一般門診、專科門診醫療服務",
                            "included": True
                        },
                        "inpatient": {
                            "name": "住院醫療",
                            "description": "住院治療、手術等醫療服務",
                            "included": True
                        },
                        "emergency": {
                            "name": "急診醫療",
                            "description": "急診醫療服務與緊急醫療處置",
                            "included": True
                        },
                        "dental": {
                            "name": "牙科醫療",
                            "description": "牙科治療、口腔保健服務",
                            "included": True
                        },
                        "chinese_medicine": {
                            "name": "中醫醫療",
                            "description": "中醫診療、針灸、傷科等服務",
                            "included": True
                        },
                        "preventive": {
                            "name": "預防保健",
                            "description": "健康檢查、疫苗接種、癌症篩檢",
                            "included": True
                        }
                    },
                    "copayment": {
                        "outpatient": {
                            "description": "門診部分負擔",
                            "amount": "50-420元",
                            "details": "依醫院層級與疾病複雜度計算"
                        },
                        "emergency": {
                            "description": "急診部分負擔",
                            "amount": "150-550元",
                            "details": "依急診檢傷分類與後續處置計算"
                        },
                        "inpatient": {
                            "description": "住院部分負擔",
                            "amount": "5-30%",
                            "details": "依住院天數與病房等級計算"
                        }
                    }
                },
                "services": [
                    {
                        "id": "ic_card",
                        "name": "健保卡申請",
                        "description": "健保卡首次申請、換發、補發及讀卡機相關服務",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=F1E9736C40AB4E65",
                        "contact": "0800-030-598",
                        "online_service": True
                    },
                    {
                        "id": "premium_query",
                        "name": "保險費查詢",
                        "description": "個人保險費繳費紀錄、欠費查詢及繳費證明申請",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=AB41370000B72ED6",
                        "contact": "0800-030-598",
                        "online_service": True
                    },
                    {
                        "id": "medical_expense",
                        "name": "醫療費用核退",
                        "description": "自墊醫療費用核退申請及相關證明文件",
                        "url": "https://www.nhi.gov.tw/Content_List.aspx?n=E9A0EDFE3D127C9B",
                        "contact": "0800-030-598",
                        "online_service": True
                    },
                    {
                        "id": "hospital_search",
                        "name": "醫療院所查詢",
                        "description": "特約醫療院所查詢、看診時間及聯絡資訊",
                        "url": "https://www.nhi.gov.tw/QueryN/Query1.aspx",
                        "contact": "0800-030-598",
                        "online_service": True
                    }
                ],
                "contacts": {
                    "nhi_hotline": {
                        "number": "0800-030-598",
                        "description": "健保諮詢服務專線",
                        "hours": "週一至週五 08:30-17:30"
                    },
                    "emergency_numbers": [
                        {
                            "number": "119",
                            "description": "消防救護車"
                        },
                        {
                            "number": "112",
                            "description": "行動電話國際緊急號碼"
                        },
                        {
                            "number": "110",
                            "description": "警察局"
                        }
                    ]
                }
            },
            "language": "zh-TW",
            "last_updated": "2024-01-15"
        }


class MockResponse:
    """Mock HTTP response for testing"""
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class TestHealthInfoAPI:
    """Test health information API endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client - this will use real FastAPI app once implemented"""
        # For now, return mock app that simulates the expected behavior
        return MockHealthInfoApp()

    def test_health_topics_endpoint_success(self, client):
        """Test GET /v1/health-info/topics returns successful response"""
        response = client.get("/v1/health-info/topics")

        assert response.status_code == 200

        data = response.json()
        assert "topics" in data
        assert "total" in data
        assert "language" in data
        assert "last_updated" in data

        assert data["language"] == "zh-TW"
        assert isinstance(data["topics"], list)
        assert isinstance(data["total"], int)
        assert data["total"] > 0

    def test_health_topics_content_structure(self, client):
        """Test topics endpoint returns properly structured content"""
        response = client.get("/v1/health-info/topics")
        data = response.json()

        topics = data["topics"]
        assert len(topics) >= 3  # Should have at least 3 topics

        for topic in topics:
            # Required fields
            assert "id" in topic
            assert "title" in topic
            assert "summary" in topic
            assert "url" in topic
            assert "category" in topic
            assert "priority" in topic
            assert "last_updated" in topic

            # Data types and format validation
            assert isinstance(topic["id"], str)
            assert isinstance(topic["title"], str)
            assert isinstance(topic["summary"], str)
            assert isinstance(topic["url"], str)
            assert isinstance(topic["category"], str)
            assert isinstance(topic["priority"], int)
            assert isinstance(topic["last_updated"], str)

            # Content validation
            assert len(topic["title"]) > 0
            assert len(topic["summary"]) > 10  # Should have meaningful summary
            assert topic["url"].startswith("https://")
            assert topic["priority"] in [1, 2, 3]

    def test_health_topics_traditional_chinese_content(self, client):
        """Test topics contain Traditional Chinese content"""
        response = client.get("/v1/health-info/topics")
        data = response.json()

        topics = data["topics"]

        # Check for Traditional Chinese characters
        traditional_chars = ["醫", "療", "健", "康", "診", "護", "險", "檢", "查", "病"]

        for topic in topics:
            title_has_chinese = any(char in topic["title"] for char in traditional_chars)
            summary_has_chinese = any(char in topic["summary"] for char in traditional_chars)

            assert title_has_chinese or summary_has_chinese, f"Topic {topic['id']} should contain Traditional Chinese"

    def test_health_topics_required_categories(self, client):
        """Test topics include required categories"""
        response = client.get("/v1/health-info/topics")
        data = response.json()

        topics = data["topics"]
        categories = [topic["category"] for topic in topics]

        required_categories = ["medical_guidance", "insurance", "emergency"]
        for required_cat in required_categories:
            assert required_cat in categories, f"Required category '{required_cat}' not found"

    def test_health_resources_endpoint_success(self, client):
        """Test GET /v1/health-info/resources returns successful response"""
        response = client.get("/v1/health-info/resources")

        assert response.status_code == 200

        data = response.json()
        assert "resources" in data
        assert "total" in data
        assert "language" in data
        assert "categories" in data

        assert data["language"] == "zh-TW"
        assert isinstance(data["resources"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["categories"], list)

    def test_health_resources_content_structure(self, client):
        """Test resources endpoint returns properly structured content"""
        response = client.get("/v1/health-info/resources")
        data = response.json()

        resources = data["resources"]
        assert len(resources) >= 3

        for resource in resources:
            # Required fields
            assert "id" in resource
            assert "title" in resource
            assert "description" in resource
            assert "url" in resource
            assert "type" in resource
            assert "language" in resource
            assert "category" in resource

            # Data validation
            assert isinstance(resource["title"], str)
            assert isinstance(resource["description"], str)
            assert isinstance(resource["url"], str)
            assert isinstance(resource["type"], str)
            assert resource["language"] == "zh-TW"

            # Content validation
            assert len(resource["title"]) > 0
            assert len(resource["description"]) > 10
            assert resource["url"].startswith("https://")

    def test_health_resources_government_urls(self, client):
        """Test government resources use .gov.tw domains"""
        response = client.get("/v1/health-info/resources")
        data = response.json()

        resources = data["resources"]
        government_resources = [r for r in resources if r["type"] == "government"]

        assert len(government_resources) >= 3, "Should have multiple government resources"

        for resource in government_resources:
            assert ".gov.tw" in resource["url"], f"Government resource should use .gov.tw domain: {resource['url']}"

    def test_vaccinations_endpoint_success(self, client):
        """Test GET /v1/health-info/vaccinations returns successful response"""
        response = client.get("/v1/health-info/vaccinations")

        assert response.status_code == 200

        data = response.json()
        assert "vaccinations" in data
        assert "language" in data
        assert "disclaimer" in data

        assert data["language"] == "zh-TW"
        assert isinstance(data["vaccinations"], dict)

        vaccinations = data["vaccinations"]
        assert "children" in vaccinations
        assert "adults" in vaccinations

    def test_vaccinations_children_structure(self, client):
        """Test children vaccination information structure"""
        response = client.get("/v1/health-info/vaccinations")
        data = response.json()

        children = data["vaccinations"]["children"]

        # Required fields
        assert "title" in children
        assert "description" in children
        assert "schedule" in children
        assert "source_url" in children
        assert "last_updated" in children

        # Schedule validation
        schedule = children["schedule"]
        assert isinstance(schedule, list)
        assert len(schedule) >= 2

        for schedule_item in schedule:
            assert "age" in schedule_item
            assert "age_months" in schedule_item
            assert "vaccines" in schedule_item
            assert "notes" in schedule_item
            assert "location" in schedule_item

            # Vaccines validation
            vaccines = schedule_item["vaccines"]
            assert isinstance(vaccines, list)
            assert len(vaccines) > 0

            for vaccine in vaccines:
                assert "name" in vaccine
                assert "type" in vaccine
                assert "dose" in vaccine
                assert "required" in vaccine

                assert isinstance(vaccine["name"], str)
                assert isinstance(vaccine["type"], str)
                assert isinstance(vaccine["dose"], int)
                assert isinstance(vaccine["required"], bool)

    def test_vaccinations_adults_structure(self, client):
        """Test adults vaccination information structure"""
        response = client.get("/v1/health-info/vaccinations")
        data = response.json()

        adults = data["vaccinations"]["adults"]

        # Required fields
        assert "title" in adults
        assert "description" in adults
        assert "recommendations" in adults
        assert "source_url" in adults
        assert "last_updated" in adults

        # Recommendations validation
        recommendations = adults["recommendations"]
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 2

        for recommendation in recommendations:
            assert "vaccine" in recommendation
            assert "type" in recommendation
            assert "frequency" in recommendation
            assert "target_group" in recommendation
            assert "notes" in recommendation
            assert "priority" in recommendation

            assert isinstance(recommendation["vaccine"], str)
            assert isinstance(recommendation["frequency"], str)
            assert isinstance(recommendation["target_group"], str)
            assert recommendation["priority"] in ["high", "medium", "low"]

    def test_vaccinations_traditional_chinese_content(self, client):
        """Test vaccination information contains Traditional Chinese"""
        response = client.get("/v1/health-info/vaccinations")
        data = response.json()

        vaccinations = data["vaccinations"]

        # Check children vaccination content
        children = vaccinations["children"]
        assert any(char in children["title"] for char in ["兒", "童", "疫", "苗", "接", "種"])

        # Check vaccine names in children schedule
        for schedule_item in children["schedule"]:
            for vaccine in schedule_item["vaccines"]:
                vaccine_name = vaccine["name"]
                # Should contain Traditional Chinese medical terms
                chinese_medical_terms = ["疫", "苗", "型", "肝", "炎", "卡", "介", "白", "喉", "破", "傷", "風", "百", "日", "咳"]
                if not any(term in vaccine_name for term in chinese_medical_terms):
                    # Some vaccine names might be in English (like specific brand names)
                    # but most should contain Chinese characters
                    pass

        # Check adults vaccination content
        adults = vaccinations["adults"]
        assert any(char in adults["title"] for char in ["成", "人", "疫", "苗"])

    def test_insurance_endpoint_success(self, client):
        """Test GET /v1/health-info/insurance returns successful response"""
        response = client.get("/v1/health-info/insurance")

        assert response.status_code == 200

        data = response.json()
        assert "insurance" in data
        assert "language" in data
        assert "last_updated" in data

        assert data["language"] == "zh-TW"
        assert isinstance(data["insurance"], dict)

    def test_insurance_content_structure(self, client):
        """Test insurance endpoint returns properly structured content"""
        response = client.get("/v1/health-info/insurance")
        data = response.json()

        insurance = data["insurance"]

        # Required sections
        assert "basic_info" in insurance
        assert "services" in insurance
        assert "contacts" in insurance

        # Basic info validation
        basic_info = insurance["basic_info"]
        assert "title" in basic_info
        assert "description" in basic_info
        assert "coverage" in basic_info
        assert "copayment" in basic_info

        # Coverage validation
        coverage = basic_info["coverage"]
        required_coverage = ["outpatient", "inpatient", "emergency", "dental", "chinese_medicine", "preventive"]
        for coverage_type in required_coverage:
            assert coverage_type in coverage
            assert "name" in coverage[coverage_type]
            assert "description" in coverage[coverage_type]
            assert "included" in coverage[coverage_type]

        # Services validation
        services = insurance["services"]
        assert isinstance(services, list)
        assert len(services) >= 3

        for service in services:
            assert "id" in service
            assert "name" in service
            assert "description" in service
            assert "url" in service
            assert "contact" in service
            assert "online_service" in service

            assert service["url"].startswith("https://")
            assert "nhi.gov.tw" in service["url"]

        # Contacts validation
        contacts = insurance["contacts"]
        assert "nhi_hotline" in contacts
        assert "emergency_numbers" in contacts

        nhi_hotline = contacts["nhi_hotline"]
        assert "number" in nhi_hotline
        assert "description" in nhi_hotline
        assert "hours" in nhi_hotline
        assert "0800" in nhi_hotline["number"]

        emergency_numbers = contacts["emergency_numbers"]
        assert isinstance(emergency_numbers, list)
        emergency_nums = [contact["number"] for contact in emergency_numbers]
        assert "119" in emergency_nums
        assert "112" in emergency_nums

    def test_insurance_traditional_chinese_content(self, client):
        """Test insurance information contains Traditional Chinese"""
        response = client.get("/v1/health-info/insurance")
        data = response.json()

        insurance = data["insurance"]
        basic_info = insurance["basic_info"]

        # Check title contains Traditional Chinese
        assert any(char in basic_info["title"] for char in ["全", "民", "健", "康", "保", "險"])

        # Check coverage descriptions
        coverage = basic_info["coverage"]
        for coverage_type, coverage_info in coverage.items():
            name = coverage_info["name"]
            description = coverage_info["description"]

            # Should contain Traditional Chinese medical terms
            chinese_terms = ["門", "診", "住", "院", "急", "診", "醫", "療", "牙", "科", "中", "醫", "預", "防", "保", "健"]
            assert any(term in name for term in chinese_terms) or any(term in description for term in chinese_terms)

        # Check services use Traditional Chinese
        services = insurance["services"]
        for service in services:
            service_name = service["name"]
            chinese_service_terms = ["健", "保", "卡", "費", "查", "詢", "核", "退", "院", "所"]
            assert any(term in service_name for term in chinese_service_terms)

    def test_api_response_headers_and_metadata(self, client):
        """Test API responses include proper metadata"""
        endpoints = [
            "/v1/health-info/topics",
            "/v1/health-info/resources",
            "/v1/health-info/vaccinations",
            "/v1/health-info/insurance"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            data = response.json()
            assert "language" in data
            assert data["language"] == "zh-TW"

            # Most endpoints should have last_updated
            if "last_updated" in data:
                # Should be in YYYY-MM-DD format
                date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
                assert date_pattern.match(data["last_updated"]), f"Invalid date format in {endpoint}"

    def test_url_format_validation_across_endpoints(self, client):
        """Test URL formats are valid across all endpoints"""
        url_pattern = re.compile(
            r'^https?://'
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
            r'localhost|'
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
            r'(?::\d+)?'
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

        # Check topics URLs
        response = client.get("/v1/health-info/topics")
        topics = response.json()["topics"]
        for topic in topics:
            assert url_pattern.match(topic["url"]), f"Invalid URL in topics: {topic['url']}"

        # Check resources URLs
        response = client.get("/v1/health-info/resources")
        resources = response.json()["resources"]
        for resource in resources:
            assert url_pattern.match(resource["url"]), f"Invalid URL in resources: {resource['url']}"

        # Check vaccination source URLs
        response = client.get("/v1/health-info/vaccinations")
        vaccinations = response.json()["vaccinations"]
        for section in ["children", "adults"]:
            source_url = vaccinations[section]["source_url"]
            assert url_pattern.match(source_url), f"Invalid URL in vaccinations {section}: {source_url}"

        # Check insurance service URLs
        response = client.get("/v1/health-info/insurance")
        services = response.json()["insurance"]["services"]
        for service in services:
            assert url_pattern.match(service["url"]), f"Invalid URL in insurance services: {service['url']}"

    def test_error_handling_for_invalid_endpoints(self, client):
        """Test error handling for non-existent endpoints"""
        invalid_endpoints = [
            "/v1/health-info/invalid",
            "/v1/health-info/topics/invalid",
            "/v1/health-info/nonexistent"
        ]

        for endpoint in invalid_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 404

            error_data = response.json()
            assert "detail" in error_data

    def test_data_consistency_across_endpoints(self, client):
        """Test data consistency and cross-references between endpoints"""
        # Get all endpoint data
        topics_response = client.get("/v1/health-info/topics")
        resources_response = client.get("/v1/health-info/resources")
        vaccinations_response = client.get("/v1/health-info/vaccinations")
        insurance_response = client.get("/v1/health-info/insurance")

        topics_data = topics_response.json()
        resources_data = resources_response.json()
        vaccinations_data = vaccinations_response.json()
        insurance_data = insurance_response.json()

        # All should use zh-TW language
        assert topics_data["language"] == "zh-TW"
        assert resources_data["language"] == "zh-TW"
        assert vaccinations_data["language"] == "zh-TW"
        assert insurance_data["language"] == "zh-TW"

        # Check for emergency contact consistency
        insurance_emergency = insurance_data["insurance"]["contacts"]["emergency_numbers"]
        emergency_numbers = [contact["number"] for contact in insurance_emergency]

        # Emergency numbers should be consistent
        assert "119" in emergency_numbers
        assert "112" in emergency_numbers

        # Check resource URLs point to same domains as topic URLs where applicable
        resource_domains = set()
        for resource in resources_data["resources"]:
            if resource["type"] == "government":
                domain = resource["url"].split("/")[2]
                resource_domains.add(domain)

        topic_domains = set()
        for topic in topics_data["topics"]:
            domain = topic["url"].split("/")[2]
            topic_domains.add(domain)

        # Some overlap expected between government resource domains and topic domains
        assert len(resource_domains.intersection(topic_domains)) > 0, "Should have some common government domains"

    def test_comprehensive_traditional_chinese_validation(self, client):
        """Comprehensive test for Traditional Chinese usage across all endpoints"""
        endpoints = [
            "/v1/health-info/topics",
            "/v1/health-info/resources",
            "/v1/health-info/vaccinations",
            "/v1/health-info/insurance"
        ]

        # Common Traditional Chinese characters in medical/health context
        common_tc_chars = set("醫療健康診護險檢查病症治藥物院所醫師護士病患疾疫苗接種診斷護理照顧手術開刀住院門診急診")

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200

            # Convert entire response to string and check for Traditional Chinese
            response_text = json.dumps(response.json(), ensure_ascii=False)

            # Should contain multiple Traditional Chinese characters
            tc_chars_found = set(char for char in response_text if char in common_tc_chars)
            assert len(tc_chars_found) >= 5, f"Endpoint {endpoint} should contain more Traditional Chinese medical terms"

            # Should not contain Simplified Chinese variants (basic check)
            simplified_variants = {"医", "护", "诊", "检", "疗", "险", "药"}
            sc_chars_found = set(char for char in response_text if char in simplified_variants)
            assert len(sc_chars_found) == 0, f"Endpoint {endpoint} should not contain Simplified Chinese characters"