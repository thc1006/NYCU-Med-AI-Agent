#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣醫療 AI 助理 API 使用示範
展示如何使用增強版 OpenAPI 文件功能
"""

import asyncio
import json
from pathlib import Path
import sys

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def demo_api_documentation():
    """示範 API 文件功能"""
    print("=" * 60)
    print("台灣醫療 AI 助理 API 文件示範")
    print("=" * 60)
    print()

    # 1. 展示 OpenAPI 配置
    print("1. OpenAPI 基本配置")
    print("-" * 30)
    try:
        from app.api_docs import get_taiwan_medical_openapi_config
        config = get_taiwan_medical_openapi_config()

        print(f"API 標題: {config['title']}")
        print(f"版本: {config['version']}")
        print(f"聯絡信箱: {config['contact']['email']}")
        print(f"授權: {config['license_info']['name']}")
        print(f"文件網址: {config['docs_url']}")
        print(f"ReDoc 網址: {config['redoc_url']}")
    except Exception as e:
        print(f"錯誤: {e}")
    print()

    # 2. 展示路由器增強文件
    print("2. 路由器增強文件")
    print("-" * 30)
    try:
        from app.router_docs import create_enhanced_router_docs, TAIWAN_MEDICAL_SPECIALTIES

        router_docs = create_enhanced_router_docs()
        print(f"已文件化的路由器: {list(router_docs.keys())}")
        print()

        print("台灣醫療專科範例:")
        for specialty, info in list(TAIWAN_MEDICAL_SPECIALTIES.items())[:3]:
            print(f"  {specialty} ({info['english']})")
            print(f"    常見症狀: {', '.join(info['symptoms'][:3])}")
            print(f"    緊急關鍵字: {', '.join(info['emergency_keywords'])}")
            print()

    except Exception as e:
        print(f"錯誤: {e}")

    # 3. 展示台灣特色範例
    print("3. 台灣特色 API 範例")
    print("-" * 30)
    try:
        from app.router_docs import TaiwanMedicalExampleGenerator

        generator = TaiwanMedicalExampleGenerator()

        # 症狀範例
        symptom_examples = generator.generate_symptom_examples()
        print("緊急症狀範例:")
        for example in symptom_examples['emergency_examples'][:2]:
            print(f"  情境: {example['scenario']}")
            print(f"  症狀: {example['symptoms']}")
            print(f"  預期分級: {example['expected_level']}")
            print(f"  建議行動: {', '.join(example['expected_actions'][:2])}")
            print()

        # 醫院範例
        hospital_examples = generator.generate_hospital_examples()
        print("主要城市醫院範例:")
        for city, info in list(hospital_examples['major_cities'].items())[:3]:
            print(f"  {city}: 緯度 {info['lat']}, 經度 {info['lng']}")
            print(f"    知名醫院: {', '.join(info['famous_hospitals'])}")
            print()

    except Exception as e:
        print(f"錯誤: {e}")

    # 4. 展示 OpenAPI YAML 資訊
    print("4. OpenAPI YAML 檔案資訊")
    print("-" * 30)
    yaml_path = Path(__file__).parent / "openapi.yaml"
    if yaml_path.exists():
        file_size = yaml_path.stat().st_size
        print(f"檔案路徑: {yaml_path}")
        print(f"檔案大小: {file_size:,} bytes ({file_size/1024:.1f} KB)")

        # 讀取並分析內容
        with open(yaml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"總行數: {len(content.splitlines()):,} 行")
        print(f"包含緊急電話: {'119' in content and '110' in content}")
        print(f"包含台灣地址: {'台北市' in content}")
        print(f"包含醫療免責: {'醫療免責' in content or '僅供參考' in content}")
        print(f"包含 PDPA: {'PDPA' in content}")
    else:
        print("OpenAPI YAML 檔案不存在")
    print()

    # 5. 展示如何啟動增強版應用程式
    print("5. 啟動增強版應用程式")
    print("-" * 30)
    print("步驟 1: 備份原始主應用程式")
    print("  mv app/main.py app/main_original.py")
    print()
    print("步驟 2: 使用增強版主應用程式")
    print("  mv app/main_enhanced.py app/main.py")
    print()
    print("步驟 3: 啟動服務")
    print("  uvicorn app.main:app --reload")
    print()
    print("步驟 4: 訪問文件")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  ReDoc: http://localhost:8000/redoc")
    print("  OpenAPI JSON: http://localhost:8000/openapi.json")
    print("  OpenAPI YAML: http://localhost:8000/openapi.yaml")
    print()

    # 6. 驗證指令
    print("6. 文件驗證與測試")
    print("-" * 30)
    print("驗證 API 文件:")
    print("  python docs/validate_api_docs.py")
    print()
    print("測試 API 端點:")
    print("  curl http://localhost:8000/healthz")
    print("  curl http://localhost:8000/v1/meta/emergency")
    print()

    print("=" * 60)
    print("示範完成！")
    print()
    print("📚 創建的文件檔案:")
    files = [
        "docs/openapi.yaml",
        "app/api_docs.py",
        "app/router_docs.py",
        "app/main_enhanced.py",
        "docs/validate_api_docs.py",
        "docs/API_DOCUMENTATION_SUMMARY.md"
    ]

    for file_path in files:
        full_path = Path(__file__).parent.parent / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"  ✅ {file_path} ({size:,} bytes)")
        else:
            print(f"  ❌ {file_path} (不存在)")

    print()
    print("🚀 下一步:")
    print("  1. 啟動增強版 FastAPI 應用程式")
    print("  2. 訪問 /docs 查看完整 API 文件")
    print("  3. 使用 OpenAPI 規格生成客戶端 SDK")
    print("  4. 執行驗證腳本確保文件正確性")
    print()
    print("⚠️  醫療安全提醒:")
    print("   本 API 僅供參考，緊急狀況請撥打 119")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_api_documentation())