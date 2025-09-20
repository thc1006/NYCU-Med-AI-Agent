"""
PythonAnywhere WSGI 配置檔案
用於在 PythonAnywhere 上部署台灣醫療 AI 助理後端
"""

import sys
import os
from pathlib import Path

# 將專案目錄加入 Python 路徑
project_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_path))

# 設定環境變數
os.environ.setdefault("ENVIRONMENT", "production")

# 導入 FastAPI 應用
from app.main import app

# WSGI 應用程式入口
application = app