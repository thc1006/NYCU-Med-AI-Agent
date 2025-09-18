#!/usr/bin/env python3
"""
SPARC Specification Steering System

Guides the specification phase and coordinates with other SPARC phases.
Ensures requirements are complete before moving to Architecture phase.
"""

import json
import yaml
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from datetime import datetime

class SpecPhase(Enum):
    PLANNING = "planning"
    REQUIREMENTS_GATHERING = "requirements_gathering"
    ANALYSIS = "analysis"
    VALIDATION = "validation"
    APPROVAL = "approval"
    COMPLETE = "complete"

class RequirementStatus(Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    IMPLEMENTED = "implemented"

@dataclass
class SpecificationMetrics:
    total_requirements: int = 0
    functional_requirements: int = 0
    non_functional_requirements: int = 0
    medical_safety_requirements: int = 0
    taiwan_specific_requirements: int = 0
    pdpa_requirements: int = 0
    approved_requirements: int = 0
    validation_errors: int = 0
    validation_warnings: int = 0
    coverage_percentage: float = 0.0
    testability_score: float = 0.0

@dataclass
class SpecificationProgress:
    current_phase: SpecPhase
    requirements_complete: bool
    validation_passed: bool
    medical_safety_reviewed: bool
    taiwan_localization_complete: bool
    pdpa_compliance_verified: bool
    ready_for_architecture: bool
    next_actions: List[str]
    blockers: List[str]

class SPARCSpecificationSteering:
    """Steering system for SPARC Specification phase."""

    def __init__(self, spec_directory: Path):
        self.spec_directory = spec_directory
        self.requirements_dir = spec_directory / "requirements"
        self.progress_file = spec_directory / "spec-progress.json"
        self.metrics_file = spec_directory / "spec-metrics.json"

    def analyze_specification_completeness(self) -> Tuple[SpecificationMetrics, SpecificationProgress]:
        """Analyze current specification completeness and progress."""
        metrics = self._calculate_metrics()
        progress = self._assess_progress(metrics)

        self._save_metrics(metrics)
        self._save_progress(progress)

        return metrics, progress

    def _calculate_metrics(self) -> SpecificationMetrics:
        """Calculate specification metrics."""
        metrics = SpecificationMetrics()

        # Count requirements by category
        for req_file in self.requirements_dir.rglob("*.yaml"):
            if req_file.name.endswith("-template.yaml"):
                continue

            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    req_data = yaml.safe_load(f)

                if not req_data or 'metadata' not in req_data:
                    continue

                metadata = req_data['metadata']
                metrics.total_requirements += 1

                # Categorize by type
                req_id = metadata.get('id', '')
                if req_id.startswith('FR-'):
                    metrics.functional_requirements += 1
                elif req_id.startswith('NFR-'):
                    metrics.non_functional_requirements += 1
                elif req_id.startswith('MS-'):
                    metrics.medical_safety_requirements += 1
                elif req_id.startswith('TW-'):
                    metrics.taiwan_specific_requirements += 1
                elif req_id.startswith('PDPA-'):
                    metrics.pdpa_requirements += 1

                # Count approved requirements
                if metadata.get('status') == 'approved':
                    metrics.approved_requirements += 1

            except Exception as e:
                print(f"Warning: Could not parse {req_file}: {e}")
                continue

        # Calculate coverage and testability
        if metrics.total_requirements > 0:
            metrics.coverage_percentage = (metrics.approved_requirements / metrics.total_requirements) * 100
            metrics.testability_score = self._calculate_testability_score()

        return metrics

    def _calculate_testability_score(self) -> float:
        """Calculate how testable the requirements are (0-100)."""
        total_score = 0
        requirement_count = 0

        for req_file in self.requirements_dir.rglob("*.yaml"):
            if req_file.name.endswith("-template.yaml"):
                continue

            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    req_data = yaml.safe_load(f)

                if not req_data or 'requirement' not in req_data:
                    continue

                requirement_count += 1
                score = 0

                # Check for acceptance criteria (40 points)
                if 'acceptance_criteria' in req_data['requirement']:
                    criteria = req_data['requirement']['acceptance_criteria']
                    if 'scenarios' in criteria and criteria['scenarios']:
                        score += 40

                        # Check for proper Given/When/Then structure (20 points)
                        for scenario in criteria['scenarios']:
                            if all(key in scenario for key in ['given', 'when', 'then']):
                                score += 5  # Up to 20 points for good scenarios
                                break

                # Check for testing section (25 points)
                if 'testing' in req_data:
                    testing = req_data['testing']
                    if any(testing.get(test_type) for test_type in ['unit_tests', 'integration_tests', 'e2e_tests']):
                        score += 25

                # Check for performance criteria (15 points)
                if 'acceptance_criteria' in req_data['requirement']:
                    criteria = req_data['requirement']['acceptance_criteria']
                    if 'performance_criteria' in criteria:
                        perf = criteria['performance_criteria']
                        if any(perf.get(criterion) for criterion in ['response_time', 'throughput', 'availability']):
                            score += 15

                total_score += min(score, 100)  # Cap at 100 per requirement

            except Exception:
                continue

        return total_score / requirement_count if requirement_count > 0 else 0

    def _assess_progress(self, metrics: SpecificationMetrics) -> SpecificationProgress:
        """Assess current progress and determine next actions."""
        progress = SpecificationProgress(
            current_phase=SpecPhase.PLANNING,
            requirements_complete=False,
            validation_passed=False,
            medical_safety_reviewed=False,
            taiwan_localization_complete=False,
            pdpa_compliance_verified=False,
            ready_for_architecture=False,
            next_actions=[],
            blockers=[]
        )

        # Determine current phase
        if metrics.total_requirements == 0:
            progress.current_phase = SpecPhase.PLANNING
            progress.next_actions.append("Create initial requirements using templates")
        elif metrics.coverage_percentage < 80:
            progress.current_phase = SpecPhase.REQUIREMENTS_GATHERING
            progress.next_actions.append(f"Complete requirements (currently {metrics.coverage_percentage:.1f}% approved)")
        elif metrics.validation_errors > 0:
            progress.current_phase = SpecPhase.VALIDATION
            progress.next_actions.append("Fix validation errors before proceeding")
        elif not progress.medical_safety_reviewed:
            progress.current_phase = SpecPhase.VALIDATION
            progress.next_actions.append("Complete medical safety review")
        else:
            progress.current_phase = SpecPhase.APPROVAL

        # Check completeness criteria
        progress.requirements_complete = (
            metrics.total_requirements >= 10 and  # Minimum viable set
            metrics.functional_requirements >= 3 and
            metrics.medical_safety_requirements >= 2 and
            metrics.taiwan_specific_requirements >= 2 and
            metrics.pdpa_requirements >= 1
        )

        # Check validation status
        progress.validation_passed = metrics.validation_errors == 0

        # Check medical safety review
        progress.medical_safety_reviewed = metrics.medical_safety_requirements > 0

        # Check Taiwan localization
        progress.taiwan_localization_complete = metrics.taiwan_specific_requirements >= 2

        # Check PDPA compliance
        progress.pdpa_compliance_verified = metrics.pdpa_requirements >= 1

        # Check if ready for architecture phase
        progress.ready_for_architecture = (
            progress.requirements_complete and
            progress.validation_passed and
            progress.medical_safety_reviewed and
            progress.taiwan_localization_complete and
            progress.pdpa_compliance_verified and
            metrics.testability_score >= 70
        )

        # Generate specific next actions
        if not progress.requirements_complete:
            if metrics.functional_requirements < 3:
                progress.next_actions.append("Add more functional requirements (symptoms analysis, hospital search, authentication)")
            if metrics.medical_safety_requirements < 2:
                progress.next_actions.append("Define medical safety requirements (emergency protocols, risk assessment)")
            if metrics.taiwan_specific_requirements < 2:
                progress.next_actions.append("Add Taiwan localization requirements (zh-TW, emergency numbers)")
            if metrics.pdpa_requirements < 1:
                progress.next_actions.append("Define PDPA compliance requirements")

        if not progress.validation_passed:
            progress.next_actions.append("Run validation and fix all errors")
            progress.blockers.append(f"{metrics.validation_errors} validation errors blocking progress")

        if metrics.testability_score < 70:
            progress.next_actions.append(f"Improve testability (current score: {metrics.testability_score:.1f}/100)")
            progress.next_actions.append("Add acceptance criteria and test scenarios to requirements")

        # Ready for next phase
        if progress.ready_for_architecture:
            progress.current_phase = SpecPhase.COMPLETE
            progress.next_actions = ["Specification phase complete - ready for Architecture phase"]

        return progress

    def _save_metrics(self, metrics: SpecificationMetrics):
        """Save metrics to file."""
        self.spec_directory.mkdir(parents=True, exist_ok=True)

        metrics_data = asdict(metrics)
        metrics_data['timestamp'] = datetime.now().isoformat()

        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)

    def _save_progress(self, progress: SpecificationProgress):
        """Save progress to file."""
        progress_data = asdict(progress)
        progress_data['current_phase'] = progress.current_phase.value
        progress_data['timestamp'] = datetime.now().isoformat()

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)

    def generate_specification_report(self) -> str:
        """Generate comprehensive specification report."""
        metrics, progress = self.analyze_specification_completeness()

        report = []
        report.append("# SPARC Specification Phase Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Overview
        report.append("## Overview")
        report.append(f"- **Current Phase**: {progress.current_phase.value.title()}")
        report.append(f"- **Total Requirements**: {metrics.total_requirements}")
        report.append(f"- **Approval Rate**: {metrics.coverage_percentage:.1f}%")
        report.append(f"- **Testability Score**: {metrics.testability_score:.1f}/100")
        report.append(f"- **Ready for Architecture**: {'✅ Yes' if progress.ready_for_architecture else '❌ No'}")
        report.append("")

        # Requirements Breakdown
        report.append("## Requirements Breakdown")
        report.append(f"- **Functional**: {metrics.functional_requirements}")
        report.append(f"- **Non-Functional**: {metrics.non_functional_requirements}")
        report.append(f"- **Medical Safety**: {metrics.medical_safety_requirements}")
        report.append(f"- **Taiwan Specific**: {metrics.taiwan_specific_requirements}")
        report.append(f"- **PDPA Compliance**: {metrics.pdpa_requirements}")
        report.append("")

        # Completeness Status
        report.append("## Completeness Status")
        report.append(f"- **Requirements Complete**: {'✅' if progress.requirements_complete else '❌'}")
        report.append(f"- **Validation Passed**: {'✅' if progress.validation_passed else '❌'}")
        report.append(f"- **Medical Safety Reviewed**: {'✅' if progress.medical_safety_reviewed else '❌'}")
        report.append(f"- **Taiwan Localization**: {'✅' if progress.taiwan_localization_complete else '❌'}")
        report.append(f"- **PDPA Compliance**: {'✅' if progress.pdpa_compliance_verified else '❌'}")
        report.append("")

        # Next Actions
        if progress.next_actions:
            report.append("## Next Actions")
            for action in progress.next_actions:
                report.append(f"- {action}")
            report.append("")

        # Blockers
        if progress.blockers:
            report.append("## ⚠️ Blockers")
            for blocker in progress.blockers:
                report.append(f"- {blocker}")
            report.append("")

        # Recommendations
        report.append("## Recommendations")

        if metrics.testability_score < 70:
            report.append("- **Improve Testability**: Add acceptance criteria with Given/When/Then scenarios")
            report.append("- **Add Test Plans**: Specify unit, integration, and E2E tests for each requirement")

        if metrics.medical_safety_requirements < 3:
            report.append("- **Enhance Medical Safety**: Add more safety-critical requirements")
            report.append("- **Risk Assessment**: Conduct thorough medical risk analysis")

        if metrics.taiwan_specific_requirements < 3:
            report.append("- **Complete Localization**: Add more Taiwan-specific requirements")
            report.append("- **Cultural Context**: Consider Taiwan healthcare system specifics")

        if metrics.coverage_percentage < 90:
            report.append("- **Requirement Approval**: Review and approve pending requirements")

        return "\n".join(report)

    def create_requirement_template(self, req_type: str, req_id: str) -> str:
        """Create a new requirement from template."""
        template_map = {
            'functional': 'functional-requirement-template.yaml',
            'medical-safety': 'medical-safety-requirement-template.yaml',
            'taiwan': 'taiwan-localization-template.yaml',
            'pdpa': 'pdpa-compliance-template.yaml'
        }

        if req_type not in template_map:
            raise ValueError(f"Unknown requirement type: {req_type}")

        template_path = self.requirements_dir / "templates" / template_map[req_type]

        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()

        # Replace placeholders
        template_content = template_content.replace("{req-id}", req_id)
        template_content = template_content.replace("{category}", req_type)
        template_content = template_content.replace("{number}", req_id.split('-')[-1])

        return template_content

def main():
    """Main steering function."""
    if len(sys.argv) < 2:
        print("Usage: python sparc-spec-steering.py <command> [args]")
        print("Commands:")
        print("  analyze <spec_directory> - Analyze specification completeness")
        print("  report <spec_directory>  - Generate specification report")
        print("  create <spec_directory> <type> <id> - Create requirement from template")
        sys.exit(1)

    command = sys.argv[1]
    spec_directory = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("spec")

    steering = SPARCSpecificationSteering(spec_directory)

    if command == "analyze":
        metrics, progress = steering.analyze_specification_completeness()
        print(f"📊 Analysis complete - {progress.current_phase.value} phase")
        print(f"Requirements: {metrics.total_requirements} total, {metrics.approved_requirements} approved")
        print(f"Ready for Architecture: {'Yes' if progress.ready_for_architecture else 'No'}")

    elif command == "report":
        report = steering.generate_specification_report()
        print(report)

    elif command == "create":
        if len(sys.argv) != 5:
            print("Usage: python sparc-spec-steering.py create <spec_directory> <type> <id>")
            print("Types: functional, medical-safety, taiwan, pdpa")
            sys.exit(1)

        req_type = sys.argv[3]
        req_id = sys.argv[4]

        try:
            content = steering.create_requirement_template(req_type, req_id)
            output_file = spec_directory / "requirements" / req_type / f"{req_id}.yaml"
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            print(f"✅ Created requirement: {output_file}")

        except Exception as e:
            print(f"❌ Error creating requirement: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()