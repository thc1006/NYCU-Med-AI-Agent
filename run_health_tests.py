#!/usr/bin/env python3
"""
Test runner script for health information tests.
Validates test structure and provides feedback on test coverage.
"""

import sys
import subprocess
from pathlib import Path


def run_tests():
    """Run health information tests with detailed output"""
    test_dir = Path(__file__).parent / "tests"

    print("Taiwan Medical AI Assistant - Health Information Tests")
    print("=" * 60)

    # Check test files exist
    unit_test = test_dir / "unit" / "test_healthinfo_static.py"
    e2e_test = test_dir / "e2e" / "test_healthinfo_api.py"
    conftest = test_dir / "conftest.py"

    print("\nTest Structure Validation:")
    print(f"+ Unit tests: {unit_test.exists()}")
    print(f"+ E2E tests: {e2e_test.exists()}")
    print(f"+ Test config: {conftest.exists()}")

    if not all([unit_test.exists(), e2e_test.exists(), conftest.exists()]):
        print("ERROR: Missing test files!")
        return False

    # Dry run to check syntax
    print("\nSyntax Validation:")
    try:
        subprocess.run([
            sys.executable, "-m", "pytest",
            "--collect-only",
            "--quiet",
            str(test_dir)
        ], check=True, capture_output=True, text=True)
        print("+ All test files have valid syntax")
    except subprocess.CalledProcessError as e:
        print("ERROR: Syntax errors found!")
        print(e.stdout)
        print(e.stderr)
        return False

    # Count test functions
    print("\nTest Coverage Analysis:")

    # Count unit tests
    unit_test_content = unit_test.read_text(encoding='utf-8')
    unit_test_count = unit_test_content.count("def test_")
    print(f"Unit tests: {unit_test_count}")

    # Count E2E tests
    e2e_test_content = e2e_test.read_text(encoding='utf-8')
    e2e_test_count = e2e_test_content.count("def test_")
    print(f"E2E tests: {e2e_test_count}")

    print(f"Total tests: {unit_test_count + e2e_test_count}")

    # Validate test categories
    print("\nTest Categories:")

    categories = {
        "Structure validation": ["structure", "content_structure"],
        "Traditional Chinese": ["traditional_chinese", "zh_TW"],
        "URL validation": ["url", "format_validation"],
        "API endpoints": ["endpoint", "api"],
        "Data consistency": ["consistency", "completeness"],
        "Error handling": ["error", "invalid"]
    }

    all_test_content = unit_test_content + e2e_test_content

    for category, keywords in categories.items():
        found = any(keyword in all_test_content.lower() for keyword in keywords)
        status = "OK" if found else "WARN"
        print(f"{status}: {category}")

    # Check for TDD compliance
    print("\nTDD Compliance Check:")

    tdd_requirements = {
        "No pytest.mark.skip": "pytest.mark.skip" not in all_test_content,
        "Traditional Chinese validation": "traditional_chinese" in all_test_content.lower(),
        "Mock external dependencies": "mock" in all_test_content.lower() or "Mock" in all_test_content,
        "Government URL validation": ".gov.tw" in all_test_content,
        "Error handling tests": "error" in all_test_content.lower(),
        "Data structure tests": "structure" in all_test_content.lower()
    }

    for requirement, passed in tdd_requirements.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {requirement}")

    all_passed = all(tdd_requirements.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All TDD requirements met! Tests are ready for implementation.")
        print("\nNext steps:")
        print("   1. Implement app/routers/healthinfo.py")
        print("   2. Create app/services/healthinfo.py")
        print("   3. Add health data YAML/JSON files")
        print("   4. Run: pytest tests/unit/test_healthinfo_static.py")
        print("   5. Run: pytest tests/e2e/test_healthinfo_api.py")
    else:
        print("WARNING: Some TDD requirements not fully met. Review test implementation.")

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)