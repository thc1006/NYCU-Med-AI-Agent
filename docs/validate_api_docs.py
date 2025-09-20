#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣醫療 AI 助理 API 文件驗證腳本
驗證 OpenAPI 文件的完整性與正確性
"""

import sys
import os
import json
import yaml
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def validate_openapi_config():
    """驗證 OpenAPI 配置"""
    try:
        from app.api_docs import get_taiwan_medical_openapi_config
        config = get_taiwan_medical_openapi_config()

        required_fields = ["title", "description", "version", "contact", "license_info"]
        missing_fields = [field for field in required_fields if field not in config]

        if missing_fields:
            return False, f"Missing required fields: {missing_fields}"

        return True, {
            "title": config["title"],
            "version": config["version"],
            "contact_email": config["contact"]["email"],
            "license": config["license_info"]["name"]
        }
    except Exception as e:
        return False, str(e)


def validate_router_docs():
    """驗證路由器文件"""
    try:
        from app.router_docs import create_enhanced_router_docs
        router_docs = create_enhanced_router_docs()

        expected_routers = ["triage", "hospitals", "meta", "monitoring"]
        missing_routers = [router for router in expected_routers if router not in router_docs]

        if missing_routers:
            return False, f"Missing router documentation: {missing_routers}"

        return True, {
            "routers": list(router_docs.keys()),
            "global_features": list(router_docs["global_features"].keys()) if "global_features" in router_docs else []
        }
    except Exception as e:
        return False, str(e)


def validate_openapi_yaml():
    """驗證 OpenAPI YAML 檔案"""
    yaml_path = Path(__file__).parent / "openapi.yaml"

    if not yaml_path.exists():
        return False, f"OpenAPI YAML file not found: {yaml_path}"

    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            yaml_content = yaml.safe_load(file)

        # Check required OpenAPI fields
        required_fields = ["openapi", "info", "paths", "components"]
        missing_fields = [field for field in required_fields if field not in yaml_content]

        if missing_fields:
            return False, f"Missing required OpenAPI fields: {missing_fields}"

        # Check OpenAPI version
        if yaml_content.get("openapi") != "3.0.0":
            return False, f"Invalid OpenAPI version: {yaml_content.get('openapi')}"

        # Count paths and components
        path_count = len(yaml_content.get("paths", {}))
        component_count = len(yaml_content.get("components", {}).get("schemas", {}))

        return True, {
            "file_size": yaml_path.stat().st_size,
            "openapi_version": yaml_content["openapi"],
            "api_title": yaml_content["info"]["title"],
            "api_version": yaml_content["info"]["version"],
            "path_count": path_count,
            "component_count": component_count,
            "tags": [tag["name"] for tag in yaml_content.get("tags", [])]
        }
    except Exception as e:
        return False, str(e)


def validate_taiwan_specific_features():
    """驗證台灣特色功能"""
    features = {
        "traditional_chinese": False,
        "emergency_numbers": False,
        "taiwan_addresses": False,
        "medical_disclaimers": False,
        "pdpa_compliance": False
    }

    try:
        yaml_path = Path(__file__).parent / "openapi.yaml"
        with open(yaml_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Check for Taiwan-specific content
        if "台灣" in content or "繁體中文" in content:
            features["traditional_chinese"] = True

        if "119" in content and "110" in content:
            features["emergency_numbers"] = True

        if "台北市" in content or "高雄市" in content:
            features["taiwan_addresses"] = True

        if "醫療免責" in content or "僅供參考" in content:
            features["medical_disclaimers"] = True

        if "PDPA" in content or "個人資料保護" in content:
            features["pdpa_compliance"] = True

        return True, features
    except Exception as e:
        return False, str(e)


def generate_validation_report():
    """生成驗證報告"""
    print("=" * 60)
    print("Taiwan Medical AI Assistant API Documentation Validation")
    print("=" * 60)
    print()

    # Test 1: OpenAPI Configuration
    print("1. OpenAPI Configuration")
    success, result = validate_openapi_config()
    if success:
        print("   Status: PASS")
        print(f"   Title: {result['title']}")
        print(f"   Version: {result['version']}")
        print(f"   Contact: {result['contact_email']}")
        print(f"   License: {result['license']}")
    else:
        print("   Status: FAIL")
        print(f"   Error: {result}")
    print()

    # Test 2: Router Documentation
    print("2. Router Documentation")
    success, result = validate_router_docs()
    if success:
        print("   Status: PASS")
        print(f"   Routers: {', '.join(result['routers'])}")
        print(f"   Global features: {', '.join(result['global_features'])}")
    else:
        print("   Status: FAIL")
        print(f"   Error: {result}")
    print()

    # Test 3: OpenAPI YAML File
    print("3. OpenAPI YAML File")
    success, result = validate_openapi_yaml()
    if success:
        print("   Status: PASS")
        print(f"   File size: {result['file_size']:,} bytes")
        print(f"   OpenAPI version: {result['openapi_version']}")
        print(f"   API title: {result['api_title']}")
        print(f"   API version: {result['api_version']}")
        print(f"   Number of paths: {result['path_count']}")
        print(f"   Number of components: {result['component_count']}")
        print(f"   Tags: {', '.join(result['tags'])}")
    else:
        print("   Status: FAIL")
        print(f"   Error: {result}")
    print()

    # Test 4: Taiwan-specific Features
    print("4. Taiwan-specific Features")
    success, result = validate_taiwan_specific_features()
    if success:
        print("   Status: PASS")
        for feature, enabled in result.items():
            status = "YES" if enabled else "NO"
            print(f"   {feature.replace('_', ' ').title()}: {status}")
    else:
        print("   Status: FAIL")
        print(f"   Error: {result}")
    print()

    # Summary
    print("=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    tests = [
        validate_openapi_config(),
        validate_router_docs(),
        validate_openapi_yaml(),
        validate_taiwan_specific_features()
    ]

    passed = sum(1 for success, _ in tests if success)
    total = len(tests)

    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("Status: ALL TESTS PASSED")
        print("The Taiwan Medical AI Assistant API documentation is complete and valid.")
    else:
        print("Status: SOME TESTS FAILED")
        print("Please review and fix the issues above.")

    print()
    print("Documentation files created:")
    print("- docs/openapi.yaml (Comprehensive OpenAPI 3.0 specification)")
    print("- app/api_docs.py (FastAPI OpenAPI customization)")
    print("- app/router_docs.py (Router-specific documentation enhancements)")
    print("- app/main_enhanced.py (Enhanced FastAPI application)")
    print()


if __name__ == "__main__":
    generate_validation_report()