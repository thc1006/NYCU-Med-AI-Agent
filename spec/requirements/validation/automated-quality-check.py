#!/usr/bin/env python3
"""
Automated Requirements Quality Checking System

Proactive validation of requirements quality with continuous monitoring.
Integrates with SPARC steering system for comprehensive quality assurance.
"""

import os
import sys
import time
import yaml
import json
from pathlib import Path
from typing import Dict, List, Set
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from spec_requirements_validator import RequirementValidator, ValidationResult, ValidationLevel
from sparc_spec_steering import SPARCSpecificationSteering

class RequirementFileHandler(FileSystemEventHandler):
    """Handles file system events for requirement files."""

    def __init__(self, quality_checker):
        self.quality_checker = quality_checker
        self.pending_files = set()

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix == '.yaml' and not file_path.name.endswith('-template.yaml'):
            self.pending_files.add(file_path)
            # Debounce: wait for multiple changes to settle
            time.sleep(0.5)
            if file_path in self.pending_files:
                self.quality_checker.check_file(file_path)
                self.pending_files.discard(file_path)

    def on_created(self, event):
        self.on_modified(event)

class AutomatedQualityChecker:
    """Automated quality checking system for requirements."""

    def __init__(self, spec_directory: Path):
        self.spec_directory = spec_directory
        self.requirements_dir = spec_directory / "requirements"
        self.quality_report_dir = spec_directory / "quality-reports"
        self.validator = RequirementValidator()
        self.steering = SPARCSpecificationSteering(spec_directory)

        # Create quality reports directory
        self.quality_report_dir.mkdir(parents=True, exist_ok=True)

        # Quality thresholds
        self.quality_thresholds = {
            'max_errors': 0,          # Zero tolerance for errors
            'max_warnings': 5,        # Limited warnings allowed
            'min_testability': 70,    # Minimum testability score
            'min_coverage': 80,       # Minimum requirement coverage
            'min_medical_safety': 2,  # Minimum safety requirements
            'min_taiwan_specific': 2, # Minimum Taiwan requirements
            'min_pdpa': 1            # Minimum PDPA requirements
        }

    def run_comprehensive_check(self) -> Dict:
        """Run comprehensive quality check on all requirements."""
        print("🔍 Running comprehensive quality check...")

        # Validate all requirements
        validation_results = self.validator.validate_directory(self.requirements_dir)

        # Analyze specification completeness
        metrics, progress = self.steering.analyze_specification_completeness()

        # Generate quality assessment
        quality_assessment = self._assess_quality(validation_results, metrics, progress)

        # Save quality report
        report_file = self._save_quality_report(quality_assessment, validation_results, metrics, progress)

        # Print summary
        self._print_quality_summary(quality_assessment, metrics)

        return {
            'quality_assessment': quality_assessment,
            'validation_results': validation_results,
            'metrics': metrics,
            'progress': progress,
            'report_file': str(report_file)
        }

    def check_file(self, file_path: Path):
        """Check a single requirement file and provide immediate feedback."""
        print(f"🔍 Checking {file_path.name}...")

        results = self.validator.validate_requirement_file(file_path)

        if not results:
            print(f"✅ {file_path.name} - No issues found")
            return

        error_count = sum(1 for r in results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in results if r.level == ValidationLevel.WARNING)

        print(f"📊 {file_path.name} - {error_count} errors, {warning_count} warnings")

        for result in results:
            icon = "❌" if result.level == ValidationLevel.ERROR else "⚠️"
            print(f"  {icon} [{result.rule}] {result.message}")

        # Auto-fix suggestions
        if results:
            self._suggest_auto_fixes(file_path, results)

    def _assess_quality(self, validation_results: Dict, metrics, progress) -> Dict:
        """Assess overall quality against thresholds."""
        assessment = {
            'overall_score': 0,
            'grade': 'F',
            'passed_checks': [],
            'failed_checks': [],
            'critical_issues': [],
            'recommendations': []
        }

        total_errors = sum(
            len([r for r in results if r.level == ValidationLevel.ERROR])
            for results in validation_results.values()
        )
        total_warnings = sum(
            len([r for r in results if r.level == ValidationLevel.WARNING])
            for results in validation_results.values()
        )

        # Check against thresholds
        checks = [
            ('errors', total_errors <= self.quality_thresholds['max_errors'],
             f"Error count: {total_errors} (max: {self.quality_thresholds['max_errors']})"),

            ('warnings', total_warnings <= self.quality_thresholds['max_warnings'],
             f"Warning count: {total_warnings} (max: {self.quality_thresholds['max_warnings']})"),

            ('testability', metrics.testability_score >= self.quality_thresholds['min_testability'],
             f"Testability score: {metrics.testability_score:.1f} (min: {self.quality_thresholds['min_testability']})"),

            ('coverage', metrics.coverage_percentage >= self.quality_thresholds['min_coverage'],
             f"Coverage: {metrics.coverage_percentage:.1f}% (min: {self.quality_thresholds['min_coverage']}%)"),

            ('medical_safety', metrics.medical_safety_requirements >= self.quality_thresholds['min_medical_safety'],
             f"Medical safety reqs: {metrics.medical_safety_requirements} (min: {self.quality_thresholds['min_medical_safety']})"),

            ('taiwan_specific', metrics.taiwan_specific_requirements >= self.quality_thresholds['min_taiwan_specific'],
             f"Taiwan reqs: {metrics.taiwan_specific_requirements} (min: {self.quality_thresholds['min_taiwan_specific']})"),

            ('pdpa', metrics.pdpa_requirements >= self.quality_thresholds['min_pdpa'],
             f"PDPA reqs: {metrics.pdpa_requirements} (min: {self.quality_thresholds['min_pdpa']})")
        ]

        passed_count = 0
        for check_name, passed, description in checks:
            if passed:
                assessment['passed_checks'].append(description)
                passed_count += 1
            else:
                assessment['failed_checks'].append(description)
                if check_name in ['errors', 'medical_safety']:
                    assessment['critical_issues'].append(description)

        # Calculate overall score and grade
        assessment['overall_score'] = (passed_count / len(checks)) * 100

        if assessment['overall_score'] >= 90:
            assessment['grade'] = 'A'
        elif assessment['overall_score'] >= 80:
            assessment['grade'] = 'B'
        elif assessment['overall_score'] >= 70:
            assessment['grade'] = 'C'
        elif assessment['overall_score'] >= 60:
            assessment['grade'] = 'D'
        else:
            assessment['grade'] = 'F'

        # Generate recommendations
        if total_errors > 0:
            assessment['recommendations'].append("Fix all validation errors before proceeding")

        if metrics.testability_score < 70:
            assessment['recommendations'].append("Add acceptance criteria and test scenarios")

        if metrics.medical_safety_requirements < 2:
            assessment['recommendations'].append("Define comprehensive medical safety requirements")

        if metrics.taiwan_specific_requirements < 2:
            assessment['recommendations'].append("Complete Taiwan localization requirements")

        if not progress.ready_for_architecture:
            assessment['recommendations'].append("Complete specification phase requirements")

        return assessment

    def _save_quality_report(self, assessment, validation_results, metrics, progress) -> Path:
        """Save comprehensive quality report."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.quality_report_dir / f"quality_report_{timestamp}.json"

        report_data = {
            'timestamp': datetime.now().isoformat(),
            'quality_assessment': assessment,
            'metrics': {
                'total_requirements': metrics.total_requirements,
                'functional_requirements': metrics.functional_requirements,
                'non_functional_requirements': metrics.non_functional_requirements,
                'medical_safety_requirements': metrics.medical_safety_requirements,
                'taiwan_specific_requirements': metrics.taiwan_specific_requirements,
                'pdpa_requirements': metrics.pdpa_requirements,
                'approved_requirements': metrics.approved_requirements,
                'coverage_percentage': metrics.coverage_percentage,
                'testability_score': metrics.testability_score
            },
            'progress': {
                'current_phase': progress.current_phase.value,
                'requirements_complete': progress.requirements_complete,
                'validation_passed': progress.validation_passed,
                'medical_safety_reviewed': progress.medical_safety_reviewed,
                'taiwan_localization_complete': progress.taiwan_localization_complete,
                'pdpa_compliance_verified': progress.pdpa_compliance_verified,
                'ready_for_architecture': progress.ready_for_architecture,
                'next_actions': progress.next_actions,
                'blockers': progress.blockers
            },
            'validation_summary': {
                'total_files': len(validation_results),
                'total_errors': sum(len([r for r in results if r.level == ValidationLevel.ERROR])
                                  for results in validation_results.values()),
                'total_warnings': sum(len([r for r in results if r.level == ValidationLevel.WARNING])
                                    for results in validation_results.values())
            }
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        return report_file

    def _print_quality_summary(self, assessment, metrics):
        """Print quality assessment summary."""
        print("\n" + "="*60)
        print("📊 REQUIREMENTS QUALITY ASSESSMENT")
        print("="*60)

        print(f"🎯 Overall Score: {assessment['overall_score']:.1f}/100 (Grade: {assessment['grade']})")
        print(f"📈 Requirements: {metrics.total_requirements} total, {metrics.approved_requirements} approved")
        print(f"🧪 Testability: {metrics.testability_score:.1f}/100")
        print(f"📋 Coverage: {metrics.coverage_percentage:.1f}%")

        if assessment['critical_issues']:
            print(f"\n🚨 CRITICAL ISSUES:")
            for issue in assessment['critical_issues']:
                print(f"  ❌ {issue}")

        if assessment['failed_checks']:
            print(f"\n⚠️ FAILED CHECKS:")
            for check in assessment['failed_checks']:
                print(f"  ❌ {check}")

        if assessment['passed_checks']:
            print(f"\n✅ PASSED CHECKS:")
            for check in assessment['passed_checks']:
                print(f"  ✅ {check}")

        if assessment['recommendations']:
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in assessment['recommendations']:
                print(f"  • {rec}")

        print("="*60)

    def _suggest_auto_fixes(self, file_path: Path, results: List[ValidationResult]):
        """Suggest automatic fixes for common issues."""
        suggestions = []

        for result in results:
            if result.rule == "MISSING_ACCEPTANCE_CRITERIA":
                suggestions.append("Add acceptance_criteria section with scenarios")
            elif result.rule == "MISSING_TESTING_SECTION":
                suggestions.append("Add testing section with unit/integration/e2e tests")
            elif result.rule == "SHORT_DESCRIPTION":
                suggestions.append("Expand requirement description (minimum 50 characters)")
            elif result.rule == "MISSING_DISCLAIMER":
                suggestions.append("Set disclaimer_required: true in medical_safety section")

        if suggestions:
            print(f"💡 Auto-fix suggestions for {file_path.name}:")
            for suggestion in suggestions:
                print(f"  • {suggestion}")

    def watch_requirements(self):
        """Start watching requirements directory for changes."""
        print(f"👁️ Watching {self.requirements_dir} for changes...")
        print("Press Ctrl+C to stop watching")

        event_handler = RequirementFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(self.requirements_dir), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n👋 Stopped watching requirements")

        observer.join()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python automated-quality-check.py <command> [spec_directory]")
        print("Commands:")
        print("  check [spec_dir]  - Run comprehensive quality check")
        print("  watch [spec_dir]  - Watch requirements and check on changes")
        print("  file <file_path>  - Check specific requirement file")
        sys.exit(1)

    command = sys.argv[1]
    spec_directory = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("spec")

    if not spec_directory.exists():
        print(f"❌ Specification directory not found: {spec_directory}")
        sys.exit(1)

    checker = AutomatedQualityChecker(spec_directory)

    if command == "check":
        result = checker.run_comprehensive_check()
        sys.exit(0 if result['quality_assessment']['grade'] in ['A', 'B'] else 1)

    elif command == "watch":
        checker.watch_requirements()

    elif command == "file":
        if len(sys.argv) != 3:
            print("Usage: python automated-quality-check.py file <file_path>")
            sys.exit(1)

        file_path = Path(sys.argv[2])
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)

        checker.check_file(file_path)

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()