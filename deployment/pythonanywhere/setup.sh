#!/bin/bash
# PythonAnywhere 部署設定腳本
# 在 PythonAnywhere 控制台中執行此腳本來設定專案

echo "🏥 開始部署台灣醫療 AI 助理到 PythonAnywhere..."

# 1. 克隆專案（如果還沒有的話）
if [ ! -d "NYCU-Med-AI-Agent" ]; then
    echo "📥 克隆專案..."
    git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
    cd NYCU-Med-AI-Agent
else
    echo "📥 更新專案..."
    cd NYCU-Med-AI-Agent
    git pull origin main
fi

# 2. 創建虛擬環境
echo "🐍 設定 Python 虛擬環境..."
python3.11 -m venv venv
source venv/bin/activate

# 3. 升級 pip
echo "📦 升級 pip..."
pip install --upgrade pip

# 4. 安裝依賴
echo "📦 安裝依賴套件..."
pip install -r requirements.txt

# 5. 檢查安裝
echo "🔍 檢查安裝狀態..."
python -c "import app.main; print('✅ FastAPI 應用程式可正常導入')"

# 6. 設定環境變數提醒
echo ""
echo "⚠️  接下來請手動設定："
echo "1. 在 PythonAnywhere Web 控制台中設定 WSGI 檔案路徑："
echo "   /home/thc1006/NYCU-Med-AI-Agent/deployment/pythonanywhere/wsgi.py"
echo ""
echo "2. 在專案根目錄建立 .env 檔案，包含您的 API 金鑰："
echo "   GOOGLE_PLACES_API_KEY=your_new_api_key_here"
echo "   GOOGLE_GEOCODING_API_KEY=your_new_api_key_here"
echo "   ENVIRONMENT=production"
echo ""
echo "3. 在 Web 控制台中設定虛擬環境路徑："
echo "   /home/thc1006/NYCU-Med-AI-Agent/venv"
echo ""
echo "🎉 設定完成！重新載入 Web 應用程式即可使用。"