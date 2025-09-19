"""
Health Data Service
Service for loading and managing health information from YAML data files
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from functools import lru_cache

from app.domain.models_extended import (
    HealthTopic, HealthResource, VaccinationInfo, InsuranceInfo,
    HealthTopicsResponse, HealthResourcesResponse, VaccinationsResponse, InsuranceResponse,
    VaccineInfo, VaccinationSchedule, VaccinationRecommendation,
    InsuranceBasicInfo, InsuranceCoverage, InsuranceCopayment,
    InsuranceService, InsuranceContacts, InsuranceContact, EmergencyContact
)

logger = logging.getLogger(__name__)


class HealthDataService:
    """健康資訊資料服務"""

    def __init__(self, data_path: Optional[str] = None):
        """初始化健康資料服務

        Args:
            data_path: 資料檔案路徑，預設為 app/data/
        """
        if data_path is None:
            # Get the app/data directory relative to this file
            current_file = Path(__file__)
            app_dir = current_file.parent.parent  # Go up to app/
            self.data_path = app_dir / "data"
        else:
            self.data_path = Path(data_path)

        self._cache_timeout = 300  # 5分鐘快取
        self._last_load_time = {}

    def _load_yaml_file(self, filename: str) -> Dict[str, Any]:
        """載入YAML檔案"""
        file_path = self.data_path / filename

        if not file_path.exists():
            logger.warning(f"Health data file not found: {file_path}")
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                logger.info(f"Loaded health data from {filename}")
                return data
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {filename}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading health data file {filename}: {e}")
            return {}

    @lru_cache(maxsize=32)
    def _load_health_topics(self) -> Dict[str, Any]:
        """載入健康主題資料"""
        return self._load_yaml_file("health_topics.yaml")

    @lru_cache(maxsize=32)
    def _load_health_resources(self) -> Dict[str, Any]:
        """載入健康資源資料"""
        return self._load_yaml_file("health_resources.yaml")

    @lru_cache(maxsize=32)
    def _load_vaccination_schedule(self) -> Dict[str, Any]:
        """載入疫苗接種資料"""
        return self._load_yaml_file("vaccination_schedule.yaml")

    @lru_cache(maxsize=32)
    def _load_nhi_info(self) -> Dict[str, Any]:
        """載入健保資訊"""
        return self._load_yaml_file("nhi_info.yaml")

    def get_health_topics(self) -> HealthTopicsResponse:
        """取得健康主題清單"""
        try:
            data = self._load_health_topics()
            topics_data = data.get("health_topics", [])

            topics = []
            for topic_data in topics_data:
                topic = HealthTopic(
                    id=topic_data.get("id", ""),
                    title=topic_data.get("title", ""),
                    summary=topic_data.get("summary", ""),
                    url=topic_data.get("url", ""),
                    category=topic_data.get("category", ""),
                    priority=topic_data.get("priority", 3),
                    keywords=topic_data.get("keywords", []),
                    content_points=topic_data.get("content_points", [])
                )
                topics.append(topic)

            return HealthTopicsResponse(
                topics=topics,
                total=len(topics),
                language="zh-TW",
                last_updated=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Error getting health topics: {e}")
            return HealthTopicsResponse(
                topics=[],
                total=0,
                language="zh-TW",
                last_updated=datetime.now().isoformat()
            )

    def get_health_resources(self) -> HealthResourcesResponse:
        """取得健康資源清單"""
        try:
            data = self._load_health_resources()

            resources = []
            categories = set()

            # Process government agencies
            gov_agencies = data.get("health_resources", {}).get("government_agencies", [])
            for agency_data in gov_agencies:
                resource = HealthResource(
                    id=agency_data.get("id", ""),
                    title=agency_data.get("title", ""),
                    description=agency_data.get("summary", ""),
                    url=agency_data.get("url", ""),
                    type="government",
                    language="zh-TW",
                    category=agency_data.get("category", "primary"),
                    contact=agency_data.get("contact", {}),
                    services=agency_data.get("services", [])
                )
                resources.append(resource)
                categories.add(resource.category)

            # Process medical institutions if present
            medical_institutions = data.get("health_resources", {}).get("medical_institutions", [])
            for inst_data in medical_institutions:
                resource = HealthResource(
                    id=inst_data.get("id", ""),
                    title=inst_data.get("title", ""),
                    description=inst_data.get("summary", ""),
                    url=inst_data.get("url", ""),
                    type="medical",
                    language="zh-TW",
                    category=inst_data.get("category", "hospital"),
                    contact=inst_data.get("contact", {}),
                    services=inst_data.get("services", [])
                )
                resources.append(resource)
                categories.add(resource.category)

            return HealthResourcesResponse(
                resources=resources,
                total=len(resources),
                language="zh-TW",
                categories=list(categories)
            )

        except Exception as e:
            logger.error(f"Error getting health resources: {e}")
            return HealthResourcesResponse(
                resources=[],
                total=0,
                language="zh-TW",
                categories=[]
            )

    def get_vaccinations(self) -> VaccinationsResponse:
        """取得疫苗接種資訊"""
        try:
            data = self._load_vaccination_schedule()
            vaccination_schedules = data.get("vaccination_schedules", {})

            vaccinations = {}

            # Process children vaccination schedule
            children_data = vaccination_schedules.get("children", {})
            if children_data:
                schedules = []
                for schedule_data in children_data.get("schedules", []):
                    vaccines = []
                    for vaccine_data in schedule_data.get("vaccines", []):
                        vaccine = VaccineInfo(
                            name=vaccine_data.get("name", ""),
                            type=vaccine_data.get("code", ""),
                            dose=1,  # Default dose
                            required=True,  # Default required
                            route=vaccine_data.get("route", ""),
                            site=vaccine_data.get("site", ""),
                            notes=vaccine_data.get("notes", "")
                        )
                        vaccines.append(vaccine)

                    schedule = VaccinationSchedule(
                        age=schedule_data.get("age", ""),
                        age_months=schedule_data.get("age_months"),
                        vaccines=vaccines,
                        notes=schedule_data.get("notes", ""),
                        location=schedule_data.get("location")
                    )
                    schedules.append(schedule)

                children_info = VaccinationInfo(
                    title=children_data.get("title", ""),
                    description=children_data.get("description", ""),
                    schedule=schedules,
                    source_url=children_data.get("reference_url", ""),
                    last_updated=datetime.now().isoformat()
                )
                vaccinations["children"] = children_info

            # Process adults vaccination recommendations
            adults_data = vaccination_schedules.get("adults", {})
            if adults_data:
                recommendations = []
                for rec_data in adults_data.get("recommendations", []):
                    recommendation = VaccinationRecommendation(
                        vaccine=rec_data.get("vaccine", ""),
                        type=rec_data.get("vaccine", "").lower().replace(" ", "_"),
                        frequency=rec_data.get("frequency", ""),
                        target_group=rec_data.get("target_group", ""),
                        notes=rec_data.get("notes", ""),
                        priority="medium"  # Default priority
                    )
                    recommendations.append(recommendation)

                adults_info = VaccinationInfo(
                    title=adults_data.get("title", ""),
                    description=adults_data.get("description", ""),
                    recommendations=recommendations,
                    source_url=adults_data.get("source_url", ""),
                    last_updated=datetime.now().isoformat()
                )
                vaccinations["adults"] = adults_info

            disclaimer = "疫苗接種建議可能因個人健康狀況而異，請諮詢醫療專業人員"

            return VaccinationsResponse(
                vaccinations=vaccinations,
                language="zh-TW",
                disclaimer=disclaimer
            )

        except Exception as e:
            logger.error(f"Error getting vaccination information: {e}")
            return VaccinationsResponse(
                vaccinations={},
                language="zh-TW",
                disclaimer="疫苗接種建議可能因個人健康狀況而異，請諮詢醫療專業人員"
            )

    def get_insurance_info(self) -> InsuranceResponse:
        """取得健保資訊"""
        try:
            data = self._load_nhi_info()
            nhi_data = data.get("nhi_general_info", {})

            # Basic info
            system_overview = nhi_data.get("system_overview", {})
            benefits = nhi_data.get("benefits", {})
            costs = nhi_data.get("costs", {})

            # Coverage
            coverage = {}
            medical_services = benefits.get("medical_services", [])
            for service in medical_services:
                key = service.lower().replace(" ", "_")
                coverage[key] = InsuranceCoverage(
                    name=service,
                    description=f"{service}服務",
                    included=True
                )

            # Copayment
            copayment = {}
            if costs:
                copayment_data = costs.get("copayment", {})
                for service_type, details in copayment_data.items():
                    copayment[service_type] = InsuranceCopayment(
                        description=details.get("description", ""),
                        amount=details.get("amount", ""),
                        details=details.get("details", "")
                    )

            basic_info = InsuranceBasicInfo(
                title=system_overview.get("title", "全民健康保險制度"),
                description=system_overview.get("description", ""),
                coverage=coverage,
                copayment=copayment
            )

            # Services
            services = []
            services_data = nhi_data.get("services", [])
            for service_data in services_data:
                service = InsuranceService(
                    id=service_data.get("id", ""),
                    name=service_data.get("name", ""),
                    description=service_data.get("description", ""),
                    url=service_data.get("url", ""),
                    contact=service_data.get("contact", ""),
                    online_service=service_data.get("online_service", True)
                )
                services.append(service)

            # Contacts
            emergency_contacts = []
            emergency_numbers = nhi_data.get("emergency_numbers", ["119", "112"])
            for number in emergency_numbers:
                contact = EmergencyContact(
                    number=number,
                    description="緊急電話" if number == "119" else "國際緊急電話"
                )
                emergency_contacts.append(contact)

            nhi_hotline = InsuranceContact(
                number=nhi_data.get("nhi_hotline", "0800-030-598"),
                description="健保諮詢服務專線",
                hours="週一至週五 08:30-17:30"
            )

            contacts = InsuranceContacts(
                nhi_hotline=nhi_hotline,
                emergency_numbers=emergency_contacts
            )

            insurance_info = InsuranceInfo(
                basic_info=basic_info,
                services=services,
                contacts=contacts
            )

            return InsuranceResponse(
                insurance=insurance_info,
                language="zh-TW",
                last_updated=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Error getting insurance information: {e}")
            # Return minimal default insurance info
            basic_info = InsuranceBasicInfo(
                title="全民健康保險制度",
                description="台灣全民健康保險制度基本資訊",
                coverage={},
                copayment={}
            )

            contacts = InsuranceContacts(
                nhi_hotline=InsuranceContact(
                    number="0800-030-598",
                    description="健保諮詢服務專線",
                    hours="週一至週五 08:30-17:30"
                ),
                emergency_numbers=[
                    EmergencyContact(number="119", description="消防救護車"),
                    EmergencyContact(number="112", description="行動電話國際緊急號碼")
                ]
            )

            insurance_info = InsuranceInfo(
                basic_info=basic_info,
                services=[],
                contacts=contacts
            )

            return InsuranceResponse(
                insurance=insurance_info,
                language="zh-TW",
                last_updated=datetime.now().isoformat()
            )


# Dependency injection function
def get_health_data_service() -> HealthDataService:
    """獲取健康資料服務實例（用於依賴注入）"""
    return HealthDataService()