#!/usr/bin/env python3
"""
Requirement Traceability System

Maintains bidirectional traceability from requirements to tests to implementation.
Ensures all requirements are covered and tracks changes through development lifecycle.
"""

import yaml
import json
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict

@dataclass
class TraceabilityLink:
    requirement_id: str
    test_files: List[str]
    implementation_files: List[str]
    coverage_percentage: float
    last_updated: str

@dataclass
class RequirementCoverage:
    requirement_id: str
    title: str
    status: str
    has_tests: bool
    has_implementation: bool
    test_count: int
    implementation_files: List[str]
    coverage_gaps: List[str]

@dataclass
class TraceabilityReport:
    total_requirements: int
    covered_requirements: int
    coverage_percentage: float
    uncovered_requirements: List[str]
    orphaned_tests: List[str]
    orphaned_implementations: List[str]
    traceability_links: List[TraceabilityLink]
    coverage_details: List[RequirementCoverage]

class RequirementTraceabilitySystem:
    """System for tracking requirement traceability."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.spec_dir = project_root / "spec"
        self.requirements_dir = self.spec_dir / "requirements"
        self.tests_dir = project_root / "tests"
        self.app_dir = project_root / "app"
        self.traceability_file = self.spec_dir / "traceability.json"

    def analyze_traceability(self) -> TraceabilityReport:
        """Analyze complete requirement traceability."""
        print("🔍 Analyzing requirement traceability...")

        # Load all requirements
        requirements = self._load_requirements()

        # Find test files and their requirement references
        test_mappings = self._analyze_test_files()

        # Find implementation files and their requirement references
        impl_mappings = self._analyze_implementation_files()

        # Build traceability links
        traceability_links = self._build_traceability_links(requirements, test_mappings, impl_mappings)

        # Generate coverage analysis
        coverage_details = self._analyze_coverage(requirements, test_mappings, impl_mappings)

        # Find orphaned files
        orphaned_tests = self._find_orphaned_tests(test_mappings, requirements)
        orphaned_implementations = self._find_orphaned_implementations(impl_mappings, requirements)

        # Calculate overall metrics
        covered_count = sum(1 for detail in coverage_details if detail.has_tests and detail.has_implementation)
        coverage_percentage = (covered_count / len(requirements)) * 100 if requirements else 0

        uncovered_requirements = [
            req_id for req_id, detail in zip(requirements.keys(), coverage_details)
            if not (detail.has_tests and detail.has_implementation)
        ]

        report = TraceabilityReport(
            total_requirements=len(requirements),
            covered_requirements=covered_count,
            coverage_percentage=coverage_percentage,
            uncovered_requirements=uncovered_requirements,
            orphaned_tests=orphaned_tests,
            orphaned_implementations=orphaned_implementations,
            traceability_links=traceability_links,
            coverage_details=coverage_details
        )

        # Save traceability data
        self._save_traceability_data(report)

        return report

    def _load_requirements(self) -> Dict[str, Dict]:
        """Load all requirements from YAML files."""
        requirements = {}

        for req_file in self.requirements_dir.rglob("*.yaml"):
            if req_file.name.endswith("-template.yaml"):
                continue

            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    req_data = yaml.safe_load(f)

                if req_data and 'metadata' in req_data and 'id' in req_data['metadata']:
                    req_id = req_data['metadata']['id']
                    requirements[req_id] = {
                        'file': str(req_file),
                        'data': req_data
                    }

            except Exception as e:
                print(f"Warning: Could not load requirement file {req_file}: {e}")

        return requirements

    def _analyze_test_files(self) -> Dict[str, List[str]]:
        """Analyze test files and extract requirement references."""
        test_mappings = defaultdict(list)

        if not self.tests_dir.exists():
            return test_mappings

        for test_file in self.tests_dir.rglob("*.py"):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for requirement IDs in comments and strings
                req_ids = self._extract_requirement_ids(content)

                for req_id in req_ids:
                    test_mappings[req_id].append(str(test_file))

                # Also check for test function names that reference requirements
                function_names = self._extract_test_function_names(content)
                for func_name in function_names:
                    req_ids_in_name = self._extract_requirement_ids_from_name(func_name)
                    for req_id in req_ids_in_name:
                        if str(test_file) not in test_mappings[req_id]:
                            test_mappings[req_id].append(str(test_file))

            except Exception as e:
                print(f"Warning: Could not analyze test file {test_file}: {e}")

        return dict(test_mappings)

    def _analyze_implementation_files(self) -> Dict[str, List[str]]:
        """Analyze implementation files and extract requirement references."""
        impl_mappings = defaultdict(list)

        if not self.app_dir.exists():
            return impl_mappings

        for impl_file in self.app_dir.rglob("*.py"):
            try:
                with open(impl_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Look for requirement IDs in comments and docstrings
                req_ids = self._extract_requirement_ids(content)

                for req_id in req_ids:
                    impl_mappings[req_id].append(str(impl_file))

            except Exception as e:
                print(f"Warning: Could not analyze implementation file {impl_file}: {e}")

        return dict(impl_mappings)

    def _extract_requirement_ids(self, content: str) -> Set[str]:
        """Extract requirement IDs from file content."""
        # Pattern to match requirement IDs: PREFIX-CATEGORY-NUMBER
        pattern = r'\b([A-Z]{2,4}-[A-Z]+-\d{3})\b'
        matches = re.findall(pattern, content)
        return set(matches)

    def _extract_test_function_names(self, content: str) -> List[str]:
        """Extract test function names from Python test files."""
        try:
            tree = ast.parse(content)
            function_names = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                    function_names.append(node.name)

            return function_names

        except Exception:
            # Fallback to regex if AST parsing fails
            pattern = r'def\s+(test_\w+)\s*\('
            return re.findall(pattern, content)

    def _extract_requirement_ids_from_name(self, name: str) -> Set[str]:
        """Extract requirement IDs from function or variable names."""
        # Look for patterns like test_fr_auth_001 -> FR-AUTH-001
        pattern = r'([a-z]{2,4})_([a-z]+)_(\d{3})'
        matches = re.findall(pattern, name.lower())

        req_ids = set()
        for prefix, category, number in matches:
            req_id = f"{prefix.upper()}-{category.upper()}-{number}"
            req_ids.add(req_id)

        return req_ids

    def _build_traceability_links(self, requirements: Dict, test_mappings: Dict, impl_mappings: Dict) -> List[TraceabilityLink]:
        """Build traceability links between requirements, tests, and implementation."""
        links = []

        for req_id in requirements.keys():
            test_files = test_mappings.get(req_id, [])
            impl_files = impl_mappings.get(req_id, [])

            # Calculate coverage percentage
            has_tests = len(test_files) > 0
            has_impl = len(impl_files) > 0

            if has_tests and has_impl:
                coverage = 100.0
            elif has_tests or has_impl:
                coverage = 50.0
            else:
                coverage = 0.0

            link = TraceabilityLink(
                requirement_id=req_id,
                test_files=test_files,
                implementation_files=impl_files,
                coverage_percentage=coverage,
                last_updated=datetime.now().isoformat()
            )

            links.append(link)

        return links

    def _analyze_coverage(self, requirements: Dict, test_mappings: Dict, impl_mappings: Dict) -> List[RequirementCoverage]:
        """Analyze coverage for each requirement."""
        coverage_details = []

        for req_id, req_info in requirements.items():
            req_data = req_info['data']
            metadata = req_data.get('metadata', {})

            test_files = test_mappings.get(req_id, [])
            impl_files = impl_mappings.get(req_id, [])

            has_tests = len(test_files) > 0
            has_implementation = len(impl_files) > 0

            # Identify coverage gaps
            gaps = []
            if not has_tests:
                gaps.append("No test coverage")
            if not has_implementation:
                gaps.append("No implementation")

            # Check for acceptance criteria without tests
            acceptance_criteria = req_data.get('requirement', {}).get('acceptance_criteria', {})
            scenarios = acceptance_criteria.get('scenarios', [])
            if scenarios and not has_tests:
                gaps.append("Acceptance criteria defined but no tests found")

            coverage = RequirementCoverage(
                requirement_id=req_id,
                title=metadata.get('title', 'Unknown'),
                status=metadata.get('status', 'unknown'),
                has_tests=has_tests,
                has_implementation=has_implementation,
                test_count=len(test_files),
                implementation_files=impl_files,
                coverage_gaps=gaps
            )

            coverage_details.append(coverage)

        return coverage_details

    def _find_orphaned_tests(self, test_mappings: Dict, requirements: Dict) -> List[str]:
        """Find test files that don't reference any known requirements."""
        orphaned = []

        if not self.tests_dir.exists():
            return orphaned

        all_test_files = set(str(f) for f in self.tests_dir.rglob("*.py"))
        referenced_test_files = set()

        for test_files in test_mappings.values():
            referenced_test_files.update(test_files)

        orphaned = list(all_test_files - referenced_test_files)
        return orphaned

    def _find_orphaned_implementations(self, impl_mappings: Dict, requirements: Dict) -> List[str]:
        """Find implementation files that don't reference any known requirements."""
        orphaned = []

        if not self.app_dir.exists():
            return orphaned

        all_impl_files = set(str(f) for f in self.app_dir.rglob("*.py"))
        referenced_impl_files = set()

        for impl_files in impl_mappings.values():
            referenced_impl_files.update(impl_files)

        # Don't consider framework/infrastructure files as orphaned
        infrastructure_patterns = ['__init__.py', 'main.py', 'config.py', 'deps.py']
        filtered_impl_files = set()

        for file_path in all_impl_files:
            if not any(pattern in Path(file_path).name for pattern in infrastructure_patterns):
                filtered_impl_files.add(file_path)

        orphaned = list(filtered_impl_files - referenced_impl_files)
        return orphaned

    def _save_traceability_data(self, report: TraceabilityReport):
        """Save traceability data to file."""
        self.spec_dir.mkdir(parents=True, exist_ok=True)

        traceability_data = {
            'timestamp': datetime.now().isoformat(),
            'report': asdict(report)
        }

        with open(self.traceability_file, 'w', encoding='utf-8') as f:
            json.dump(traceability_data, f, indent=2, ensure_ascii=False)

    def generate_traceability_matrix(self) -> str:
        """Generate traceability matrix in markdown format."""
        report = self.analyze_traceability()

        matrix = []
        matrix.append("# Requirement Traceability Matrix")
        matrix.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        matrix.append("")

        # Summary
        matrix.append("## Summary")
        matrix.append(f"- **Total Requirements**: {report.total_requirements}")
        matrix.append(f"- **Covered Requirements**: {report.covered_requirements}")
        matrix.append(f"- **Coverage Percentage**: {report.coverage_percentage:.1f}%")
        matrix.append(f"- **Orphaned Tests**: {len(report.orphaned_tests)}")
        matrix.append(f"- **Orphaned Implementations**: {len(report.orphaned_implementations)}")
        matrix.append("")

        # Traceability Matrix
        matrix.append("## Traceability Matrix")
        matrix.append("| Requirement ID | Title | Status | Tests | Implementation | Coverage |")
        matrix.append("|---|---|---|---|---|---|")

        for detail in report.coverage_details:
            test_icon = "✅" if detail.has_tests else "❌"
            impl_icon = "✅" if detail.has_implementation else "❌"

            if detail.has_tests and detail.has_implementation:
                coverage_icon = "🟢 Full"
            elif detail.has_tests or detail.has_implementation:
                coverage_icon = "🟡 Partial"
            else:
                coverage_icon = "🔴 None"

            matrix.append(f"| {detail.requirement_id} | {detail.title} | {detail.status} | {test_icon} ({detail.test_count}) | {impl_icon} | {coverage_icon} |")

        matrix.append("")

        # Uncovered Requirements
        if report.uncovered_requirements:
            matrix.append("## ⚠️ Uncovered Requirements")
            for req_id in report.uncovered_requirements:
                detail = next((d for d in report.coverage_details if d.requirement_id == req_id), None)
                if detail:
                    matrix.append(f"- **{req_id}**: {detail.title}")
                    for gap in detail.coverage_gaps:
                        matrix.append(f"  - {gap}")
            matrix.append("")

        # Orphaned Files
        if report.orphaned_tests:
            matrix.append("## 🔍 Orphaned Test Files")
            for test_file in report.orphaned_tests:
                matrix.append(f"- `{test_file}`")
            matrix.append("")

        if report.orphaned_implementations:
            matrix.append("## 🔍 Orphaned Implementation Files")
            for impl_file in report.orphaned_implementations:
                matrix.append(f"- `{impl_file}`")
            matrix.append("")

        # Recommendations
        matrix.append("## 💡 Recommendations")

        if report.coverage_percentage < 80:
            matrix.append("- **Improve Coverage**: Add tests and implementation for uncovered requirements")

        if report.orphaned_tests:
            matrix.append("- **Link Orphaned Tests**: Add requirement ID references to orphaned test files")

        if report.orphaned_implementations:
            matrix.append("- **Document Implementation**: Add requirement ID references to implementation files")

        uncovered_critical = [
            detail for detail in report.coverage_details
            if not (detail.has_tests and detail.has_implementation)
            and any(keyword in detail.requirement_id.lower() for keyword in ['emergency', 'safety', 'medical'])
        ]

        if uncovered_critical:
            matrix.append("- **Critical Gap**: Prioritize coverage for medical safety and emergency requirements")

        return "\n".join(matrix)

    def check_requirement_coverage(self, requirement_id: str) -> Optional[RequirementCoverage]:
        """Check coverage for a specific requirement."""
        report = self.analyze_traceability()

        for detail in report.coverage_details:
            if detail.requirement_id == requirement_id:
                return detail

        return None

    def suggest_test_files_for_requirement(self, requirement_id: str) -> List[str]:
        """Suggest test file names for a requirement based on its category."""
        # Extract category from requirement ID (e.g., FR-TRIAGE-001 -> triage)
        parts = requirement_id.split('-')
        if len(parts) >= 3:
            category = parts[1].lower()
            number = parts[2]

            suggestions = [
                f"tests/unit/test_{category}_{number.lower()}.py",
                f"tests/integration/test_{category}_integration.py",
                f"tests/e2e/test_{category}_e2e.py"
            ]

            return suggestions

        return []

def main():
    """Main traceability function."""
    if len(sys.argv) < 2:
        print("Usage: python requirement-traceability.py <command> [args]")
        print("Commands:")
        print("  analyze [project_root]           - Analyze complete traceability")
        print("  matrix [project_root]            - Generate traceability matrix")
        print("  check <req_id> [project_root]    - Check specific requirement coverage")
        print("  suggest <req_id> [project_root]  - Suggest test files for requirement")
        sys.exit(1)

    command = sys.argv[1]
    project_root = Path(sys.argv[-1]) if len(sys.argv) > 2 else Path(".")

    tracer = RequirementTraceabilitySystem(project_root)

    if command == "analyze":
        report = tracer.analyze_traceability()
        print(f"📊 Traceability Analysis Complete")
        print(f"Coverage: {report.coverage_percentage:.1f}% ({report.covered_requirements}/{report.total_requirements})")

    elif command == "matrix":
        matrix = tracer.generate_traceability_matrix()
        print(matrix)

    elif command == "check":
        if len(sys.argv) < 3:
            print("Usage: python requirement-traceability.py check <req_id>")
            sys.exit(1)

        req_id = sys.argv[2]
        coverage = tracer.check_requirement_coverage(req_id)

        if coverage:
            print(f"📋 Coverage for {req_id}:")
            print(f"- Tests: {'✅' if coverage.has_tests else '❌'} ({coverage.test_count} files)")
            print(f"- Implementation: {'✅' if coverage.has_implementation else '❌'}")
            if coverage.coverage_gaps:
                print("- Gaps:")
                for gap in coverage.coverage_gaps:
                    print(f"  • {gap}")
        else:
            print(f"❌ Requirement {req_id} not found")

    elif command == "suggest":
        if len(sys.argv) < 3:
            print("Usage: python requirement-traceability.py suggest <req_id>")
            sys.exit(1)

        req_id = sys.argv[2]
        suggestions = tracer.suggest_test_files_for_requirement(req_id)

        print(f"💡 Suggested test files for {req_id}:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()