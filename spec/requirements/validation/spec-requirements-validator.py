#!/usr/bin/env python3
"""
SPARC Specification Requirements Validator

Validates requirements for completeness, clarity, and quality.
Ensures Taiwan medical AI requirements meet safety and compliance standards.
"""

import yaml
import re
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class ValidationLevel(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationResult:
    level: ValidationLevel
    rule: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None


class RequirementValidator:
    """Validates requirements according to SPARC methodology and Taiwan medical standards."""

    def __init__(self):
        self.taiwan_emergency_numbers = ["119", "110", "112", "113", "165"]
        self.medical_safety_keywords = [
            "chest pain", "difficulty breathing", "unconscious", "severe pain",
            "胸痛", "呼吸困難", "意識不清", "劇烈疼痛", "過敏反應"
        ]
        self.pdpa_keywords = [
            "personal data", "個人資料", "phone", "address", "medical history",
            "電話", "地址", "病歷", "身分證"
        ]

    def validate_requirement_file(self, file_path: Path) -> List[ValidationResult]:
        """Validate a single requirement file."""
        results = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = yaml.safe_load(content)

            if not data:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "EMPTY_FILE",
                    "Requirement file is empty or invalid YAML",
                    str(file_path)
                ))
                return results

            # Validate structure
            results.extend(self._validate_structure(data, file_path))

            # Validate content quality
            results.extend(self._validate_content_quality(data, file_path))

            # Validate Taiwan localization
            results.extend(self._validate_taiwan_localization(data, file_path))

            # Validate medical safety
            results.extend(self._validate_medical_safety(data, file_path))

            # Validate PDPA compliance
            results.extend(self._validate_pdpa_compliance(data, file_path))

            # Validate testability
            results.extend(self._validate_testability(data, file_path))

        except Exception as e:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                "PARSE_ERROR",
                f"Failed to parse requirement file: {str(e)}",
                str(file_path)
            ))

        return results

    def _validate_structure(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate requirement structure."""
        results = []

        # Check required top-level sections
        required_sections = ['metadata', 'requirement']
        for section in required_sections:
            if section not in data:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "MISSING_SECTION",
                    f"Missing required section: {section}",
                    str(file_path)
                ))

        # Validate metadata
        if 'metadata' in data:
            metadata = data['metadata']
            required_metadata = ['id', 'title', 'description', 'priority', 'category']
            for field in required_metadata:
                if field not in metadata or not metadata[field]:
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "MISSING_METADATA",
                        f"Missing or empty metadata field: {field}",
                        str(file_path)
                    ))

            # Validate ID format
            if 'id' in metadata and metadata['id']:
                if not re.match(r'^[A-Z]{2,3}-[A-Z]+-\d{3}$', metadata['id']):
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        "INVALID_ID_FORMAT",
                        "ID should follow format: PREFIX-CATEGORY-NUMBER (e.g., FR-TRIAGE-001)",
                        str(file_path)
                    ))

        return results

    def _validate_content_quality(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate content quality and clarity."""
        results = []

        if 'requirement' not in data:
            return results

        requirement = data['requirement']

        # Check description quality
        if 'description' in requirement:
            desc = requirement['description']
            if len(desc.strip()) < 50:
                results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "SHORT_DESCRIPTION",
                    "Requirement description should be more detailed (minimum 50 characters)",
                    str(file_path)
                ))

            # Check for vague language
            vague_words = ['good', 'fast', 'user-friendly', 'efficient', 'robust']
            for word in vague_words:
                if word.lower() in desc.lower():
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        "VAGUE_LANGUAGE",
                        f"Avoid vague term '{word}' - use specific, measurable criteria",
                        str(file_path)
                    ))

        # Check for acceptance criteria
        if 'acceptance_criteria' not in requirement:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                "MISSING_ACCEPTANCE_CRITERIA",
                "Requirement must have acceptance criteria for TDD",
                str(file_path)
            ))
        elif 'scenarios' not in requirement['acceptance_criteria']:
            results.append(ValidationResult(
                ValidationLevel.ERROR,
                "MISSING_SCENARIOS",
                "Acceptance criteria must include test scenarios",
                str(file_path)
            ))

        return results

    def _validate_taiwan_localization(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate Taiwan-specific requirements."""
        results = []

        metadata = data.get('metadata', {})
        if metadata.get('taiwan_specific', False):

            # Check for Taiwan localization section
            if 'taiwan_localization' not in data:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "MISSING_TAIWAN_LOCALIZATION",
                    "Taiwan-specific requirement must include taiwan_localization section",
                    str(file_path)
                ))
            else:
                taiwan = data['taiwan_localization']

                # Check language setting
                if taiwan.get('language') != 'zh-TW':
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "WRONG_LANGUAGE",
                        "Taiwan localization must use language: zh-TW",
                        str(file_path)
                    ))

                # Check region setting
                if taiwan.get('region') != 'TW':
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "WRONG_REGION",
                        "Taiwan localization must use region: TW",
                        str(file_path)
                    ))

                # Check emergency numbers
                emergency_nums = taiwan.get('emergency_numbers', [])
                for num in self.taiwan_emergency_numbers:
                    if num not in emergency_nums:
                        results.append(ValidationResult(
                            ValidationLevel.WARNING,
                            "MISSING_EMERGENCY_NUMBER",
                            f"Consider including emergency number: {num}",
                            str(file_path)
                        ))

        return results

    def _validate_medical_safety(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate medical safety requirements."""
        results = []

        metadata = data.get('metadata', {})
        is_medical_safety = metadata.get('medical_safety', False)

        # Check if requirement should be flagged as medical safety
        requirement_text = str(data.get('requirement', {})).lower()
        has_safety_keywords = any(keyword.lower() in requirement_text
                                for keyword in self.medical_safety_keywords)

        if has_safety_keywords and not is_medical_safety:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                "POTENTIAL_MEDICAL_SAFETY",
                "Requirement contains medical safety keywords - consider flagging as medical_safety: true",
                str(file_path)
            ))

        if is_medical_safety:
            # Check for medical safety section
            if 'medical_safety' not in data:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "MISSING_MEDICAL_SAFETY_SECTION",
                    "Medical safety requirement must include medical_safety section",
                    str(file_path)
                ))
            else:
                safety = data['medical_safety']

                # Check risk level
                if 'risk_level' not in safety or not safety['risk_level']:
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "MISSING_RISK_LEVEL",
                        "Medical safety requirement must specify risk_level",
                        str(file_path)
                    ))

                # Check safety measures
                if 'safety_measures' not in safety or not safety['safety_measures']:
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        "MISSING_SAFETY_MEASURES",
                        "Consider specifying safety measures for medical requirement",
                        str(file_path)
                    ))

                # Check disclaimer requirement
                if not safety.get('disclaimer_required', False):
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "MISSING_DISCLAIMER",
                        "Medical safety requirement must require disclaimer",
                        str(file_path)
                    ))

        return results

    def _validate_pdpa_compliance(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate PDPA compliance requirements."""
        results = []

        metadata = data.get('metadata', {})
        is_pdpa_relevant = metadata.get('pdpa_relevant', False)

        # Check if requirement should be flagged as PDPA relevant
        requirement_text = str(data.get('requirement', {})).lower()
        has_pdpa_keywords = any(keyword.lower() in requirement_text
                              for keyword in self.pdpa_keywords)

        if has_pdpa_keywords and not is_pdpa_relevant:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                "POTENTIAL_PDPA_RELEVANT",
                "Requirement mentions personal data - consider flagging as pdpa_relevant: true",
                str(file_path)
            ))

        if is_pdpa_relevant:
            # Check for compliance section
            if 'compliance' not in data:
                results.append(ValidationResult(
                    ValidationLevel.ERROR,
                    "MISSING_COMPLIANCE_SECTION",
                    "PDPA-relevant requirement must include compliance section",
                    str(file_path)
                ))
            else:
                compliance = data['compliance']

                # Check data classification
                if 'pdpa_classification' not in compliance or not compliance['pdpa_classification']:
                    results.append(ValidationResult(
                        ValidationLevel.ERROR,
                        "MISSING_PDPA_CLASSIFICATION",
                        "PDPA-relevant requirement must specify data classification",
                        str(file_path)
                    ))

                # Check data minimization
                if not compliance.get('data_minimization', False):
                    results.append(ValidationResult(
                        ValidationLevel.WARNING,
                        "MISSING_DATA_MINIMIZATION",
                        "Consider enabling data minimization for PDPA compliance",
                        str(file_path)
                    ))

        return results

    def _validate_testability(self, data: Dict, file_path: Path) -> List[ValidationResult]:
        """Validate that requirements are testable (TDD-ready)."""
        results = []

        if 'testing' not in data:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                "MISSING_TESTING_SECTION",
                "Consider adding testing section for TDD approach",
                str(file_path)
            ))
            return results

        testing = data['testing']

        # Check for test types
        test_types = ['unit_tests', 'integration_tests', 'e2e_tests']
        has_tests = any(testing.get(test_type) for test_type in test_types)

        if not has_tests:
            results.append(ValidationResult(
                ValidationLevel.WARNING,
                "NO_TESTS_SPECIFIED",
                "No tests specified - TDD requires test-first approach",
                str(file_path)
            ))

        # Check acceptance criteria testability
        acceptance = data.get('requirement', {}).get('acceptance_criteria', {})
        scenarios = acceptance.get('scenarios', [])

        for i, scenario in enumerate(scenarios):
            if not all(key in scenario for key in ['given', 'when', 'then']):
                results.append(ValidationResult(
                    ValidationLevel.WARNING,
                    "INCOMPLETE_SCENARIO",
                    f"Scenario {i+1} missing Given/When/Then structure",
                    str(file_path)
                ))

        return results

    def validate_directory(self, directory: Path) -> Dict[str, List[ValidationResult]]:
        """Validate all requirement files in a directory."""
        results = {}

        for file_path in directory.rglob("*.yaml"):
            if file_path.name.endswith("-template.yaml"):
                continue  # Skip templates

            file_results = self.validate_requirement_file(file_path)
            if file_results:
                results[str(file_path)] = file_results

        return results

    def print_results(self, results: Dict[str, List[ValidationResult]]) -> int:
        """Print validation results and return error count."""
        error_count = 0
        warning_count = 0

        for file_path, file_results in results.items():
            print(f"\n📄 {file_path}")
            print("=" * 50)

            for result in file_results:
                if result.level == ValidationLevel.ERROR:
                    icon = "❌"
                    error_count += 1
                elif result.level == ValidationLevel.WARNING:
                    icon = "⚠️"
                    warning_count += 1
                else:
                    icon = "ℹ️"

                print(f"{icon} [{result.rule}] {result.message}")

        print(f"\n📊 Summary: {error_count} errors, {warning_count} warnings")
        return error_count


def main():
    """Main validation function."""
    if len(sys.argv) != 2:
        print("Usage: python spec-requirements-validator.py <requirements_directory>")
        sys.exit(1)

    directory = Path(sys.argv[1])
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)

    validator = RequirementValidator()
    results = validator.validate_directory(directory)

    if not results:
        print("✅ No requirement files found or all requirements are valid!")
        return 0

    error_count = validator.print_results(results)
    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())