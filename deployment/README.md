# 🚀 台灣醫療 AI 助理 - 部署指南

## 📋 部署架構概覽

本專案採用前後端分離部署架構，提供兩種部署方案：

## 🆓 方案一：完全免費（推薦學習用）
- **後端**：Render 免費方案（FastAPI + Python）
- **前端**：Vercel 免費方案（React + TypeScript）
- **成本**：$0/月
- **限制**：後端15分鐘無活動會休眠

## 💰 方案二：低成本穩定（推薦正式用）
- **後端**：PythonAnywhere Hacker 方案（FastAPI + Python）
- **前端**：Vercel 免費方案（React + TypeScript）
- **成本**：$5/月
- **優點**：無休眠，24/7 運行

## 🔧 快速部署

### 選擇部署方案

**🆓 免費方案 → [Render 部署指南](./render/README.md)**
**💰 穩定方案 → [PythonAnywhere 部署指南](./pythonanywhere/README.md)**

---

## 📋 方案一：Render + Vercel（免費）

詳細步驟請參考：[Render 部署指南](./render/README.md)

**簡要步驟：**
1. GitHub 推送程式碼
2. Render 連接 GitHub 建立服務
3. Vercel 連接 GitHub 部署前端
4. 設定環境變數連接前後端

---

## 📋 方案二：PythonAnywhere + Vercel（$5/月）

### 1. 後端部署（PythonAnywhere）

#### 📁 準備工作
```bash
# 克隆專案
git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent
```

#### 🐍 自動部署腳本
```bash
chmod +x deployment/pythonanywhere/setup.sh
./deployment/pythonanywhere/setup.sh
```

#### ⚙️ 手動配置步驟
1. **建立 Web 應用程式**
   - 選擇 Python 3.11
   - Manual configuration

2. **設定 WSGI 檔案路徑**
   ```
   /home/yourusername/NYCU-Med-AI-Agent/deployment/pythonanywhere/wsgi.py
   ```

3. **設定虛擬環境路徑**
   ```
   /home/yourusername/NYCU-Med-AI-Agent/venv
   ```

4. **建立環境變數檔案**
   ```ini
   # .env
   GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
   GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key_here
   ENVIRONMENT=production
   DEBUG=false
   DEFAULT_LANG=zh-TW
   REGION=TW
   ```

### 2. 前端部署（Vercel）

#### 🌐 Vercel CLI 部署
```bash
# 安裝 Vercel CLI
npm i -g vercel

# 部署
vercel --cwd frontend

# 設定環境變數
vercel env add REACT_APP_API_BASE_URL
# 輸入：https://yourusername.pythonanywhere.com
```

#### 🔗 GitHub 自動部署
1. 連接 GitHub 專案到 Vercel
2. 設定建置目錄：`frontend`
3. 設定環境變數：
   ```
   REACT_APP_API_BASE_URL=https://yourusername.pythonanywhere.com
   ```

## 🧪 測試部署

### 後端健康檢查
```bash
curl https://yourusername.pythonanywhere.com/v1/monitoring/health
```

### 前端功能測試
```bash
# 測試症狀分析 API
curl -X POST "https://yourusername.pythonanywhere.com/v1/triage/quick" \
  -H "Content-Type: application/json" \
  -d '{"symptom_text": "頭痛發燒", "include_nearby_hospitals": false}'
```

### API 文檔檢查
- 後端 API 文檔：`https://yourusername.pythonanywhere.com/docs`
- 前端應用：`https://your-app.vercel.app`

## 🔐 環境變數配置

### 後端環境變數 (.env)
```ini
# Google API（必填）
GOOGLE_PLACES_API_KEY=your_key_here
GOOGLE_GEOCODING_API_KEY=your_key_here

# 應用程式設定
ENVIRONMENT=production
DEBUG=false
APP_NAME=台灣醫療 AI 助理
APP_VERSION=0.1.0

# 地區設定
DEFAULT_LANG=zh-TW
REGION=TW
```

### 前端環境變數 (Vercel)
```ini
REACT_APP_API_BASE_URL=https://yourusername.pythonanywhere.com
```

## 📊 監控與維護

### 即時監控
- **健康檢查**：`/v1/monitoring/health`
- **系統指標**：`/v1/monitoring/metrics`
- **Vercel 分析**：Vercel Dashboard

### 日誌檢查
- **PythonAnywhere**：Web 控制台 > Error log
- **Vercel**：Functions 頁面的執行日誌

### 更新應用程式
```bash
# 後端更新
cd NYCU-Med-AI-Agent
git pull origin main
pip install -r requirements.txt
# 在 PythonAnywhere 控制台點擊 Reload

# 前端更新
git push origin main  # 自動觸發 Vercel 重新部署
```

## 🚨 故障排除

### 常見問題

#### 1. 外部 API 呼叫失敗
**症狀**：Google Places API 無法使用
**解決方案**：升級到 PythonAnywhere Hacker 方案（$5/月）

#### 2. CORS 錯誤
**症狀**：前端無法連接後端
**解決方案**：檢查 API URL 和 CORS 設定

#### 3. 環境變數未載入
**症狀**：API 金鑰錯誤
**解決方案**：
- 確認 `.env` 檔案在專案根目錄
- 檢查檔案權限和格式
- 重新載入 Web 應用程式

#### 4. 建置失敗
**症狀**：Vercel 部署失敗
**解決方案**：
- 檢查 Node.js 版本相容性
- 確認 `frontend/` 目錄結構
- 檢查 `package.json` 腳本

## 💰 成本估算

### PythonAnywhere
- **免費方案**：$0/月（限制外部 API）
- **Hacker 方案**：$5/月（推薦，支援完整功能）

### Vercel
- **Hobby 方案**：$0/月（個人專案）
- **Pro 方案**：$20/月（商業用途）

### Google API
- **Places API**：免費額度 + 使用量計費
- **Geocoding API**：免費額度 + 使用量計費

## 🔗 相關連結

- [PythonAnywhere 部署詳細指南](./pythonanywhere/README.md)
- [Vercel 部署文檔](https://vercel.com/docs)
- [專案 GitHub](https://github.com/thc1006/NYCU-Med-AI-Agent)
- [FastAPI 文檔](https://fastapi.tiangolo.com/)
- [React 部署指南](https://create-react-app.dev/docs/deployment/)

## 📞 技術支援

如有部署問題，請：
1. 檢查本指南的故障排除章節
2. 查看專案 GitHub Issues
3. 聯絡專案維護者

---

**注意**：本專案僅供教育和研究用途，不得用於實際醫療診斷。