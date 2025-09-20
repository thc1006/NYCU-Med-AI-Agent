# PythonAnywhere 部署指南

## 📋 部署步驟

### 1. 註冊 PythonAnywhere 帳號
- 前往 [PythonAnywhere](https://www.pythonanywhere.com/)
- 選擇免費帳號或付費方案
- **建議**：Hacker 方案（$5/月）支援外部 API 呼叫

### 2. 上傳專案代碼

#### 方法 A：使用 Git（推薦）
```bash
# 在 PythonAnywhere 控制台中執行
git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent
```

#### 方法 B：上傳 ZIP 檔案
1. 下載專案 ZIP 檔案
2. 在 Files 頁面上傳並解壓縮

### 3. 設定虛擬環境
```bash
# 在 PythonAnywhere 控制台中執行
chmod +x deployment/pythonanywhere/setup.sh
./deployment/pythonanywhere/setup.sh
```

### 4. 設定環境變數
在專案根目錄建立 `.env` 檔案：
```ini
# Google API 設定（必填）
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key_here

# 環境設定
ENVIRONMENT=production
DEBUG=false

# 台灣在地化設定
DEFAULT_LANG=zh-TW
REGION=TW

# 應用程式資訊
APP_NAME=台灣醫療 AI 助理
APP_VERSION=0.1.0
```

### 5. 設定 Web 應用程式

#### 在 PythonAnywhere Web 控制台中：

1. **建立新的 Web 應用程式**
   - 選擇 Python 3.11
   - 選擇 Manual configuration

2. **設定 WSGI 檔案路徑**
   ```
   /home/yourusername/NYCU-Med-AI-Agent/deployment/pythonanywhere/wsgi.py
   ```

3. **設定虛擬環境路徑**
   ```
   /home/yourusername/NYCU-Med-AI-Agent/venv
   ```

4. **設定靜態檔案**（可選）
   - URL: `/static/`
   - Directory: `/home/yourusername/NYCU-Med-AI-Agent/static/`

### 6. 重新載入應用程式
點擊 **Reload** 按鈕啟動應用程式

## 🔧 測試部署

### 檢查 API 端點
```bash
# 健康檢查
curl https://thc1006.pythonanywhere.com/v1/monitoring/health

# API 文檔
https://thc1006.pythonanywhere.com/docs
```

### 測試症狀分析
```bash
curl -X POST "https://thc1006.pythonanywhere.com/v1/triage" \
  -H "Content-Type: application/json" \
  -d '{"symptom_text": "頭痛發燒"}'
```

## 📊 監控與維護

### 查看錯誤日誌
在 PythonAnywhere Web 控制台的 **Error log** 頁面

### 更新應用程式
```bash
cd NYCU-Med-AI-Agent
git pull origin main
pip install -r requirements.txt
```
然後在 Web 控制台點擊 **Reload**

### 環境變數管理
在 Files 頁面編輯 `.env` 檔案

## 🚨 常見問題

### 1. 外部 API 無法呼叫
**問題**：Google Places API 呼叫失敗
**解決方案**：升級到 Hacker 方案（$5/月）以支援外部網路存取

### 2. 模組導入錯誤
**問題**：`ModuleNotFoundError`
**解決方案**：
- 確認虛擬環境路徑正確
- 重新安裝依賴：`pip install -r requirements.txt`

### 3. 環境變數讀取失敗
**問題**：API 金鑰未正確載入
**解決方案**：
- 確認 `.env` 檔案在專案根目錄
- 檢查檔案權限與內容格式

## 💰 費用說明

### 免費方案限制
- 無法呼叫外部 API（Google Places API 無法使用）
- 適合僅測試內部功能

### Hacker 方案（推薦）
- $5/月
- 完整外部 API 支援
- 適合正式部署

## 🔗 相關連結

- [PythonAnywhere 官方文檔](https://help.pythonanywhere.com/)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- [專案 GitHub](https://github.com/thc1006/NYCU-Med-AI-Agent)