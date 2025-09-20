# 🆓 Render 免費部署指南

## 🌟 為什麼選擇 Render？

- ✅ **完全免費**：無需信用卡
- ✅ **支援外部 API**：可呼叫 Google API
- ✅ **自動部署**：GitHub 連接自動更新
- ⚠️ **休眠機制**：15分鐘無活動會休眠（30-60秒喚醒）

## 🚀 快速部署步驟

### 1. 準備 GitHub 專案
```bash
# 確保專案已推送到 GitHub
git add .
git commit -m "準備 Render 部署"
git push origin main
```

### 2. 建立 Render 服務

1. **註冊 Render 帳號**
   - 前往 [render.com](https://render.com)
   - 使用 GitHub 帳號登入

2. **建立 Web Service**
   - 點擊 "New +" → "Web Service"
   - 連接您的 GitHub 專案
   - 選擇 `NYCU-Med-AI-Agent` 專案

3. **配置服務設定**
   ```
   Name: taiwan-med-ai-backend
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

### 3. 設定環境變數

在 Render 控制台的 "Environment" 頁面添加：

```
ENVIRONMENT=production
DEBUG=false
DEFAULT_LANG=zh-TW
REGION=TW
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here
GOOGLE_GEOCODING_API_KEY=your_google_geocoding_api_key_here
```

### 4. 部署後端

點擊 "Create Web Service"，Render 會自動：
- 克隆您的程式碼
- 安裝依賴
- 部署應用程式

您的後端 URL 會是：`https://taiwan-med-ai-backend.onrender.com`

## 🎨 Vercel 前端部署

### 1. 連接 Vercel

1. **登入 Vercel**
   - 前往 [vercel.com](https://vercel.com)
   - 使用 GitHub 帳號登入

2. **導入專案**
   - 點擊 "Add New..." → "Project"
   - 選擇您的 GitHub 專案

3. **配置設定**
   ```
   Framework Preset: Create React App
   Root Directory: frontend
   Build Command: npm run build
   Output Directory: build
   Install Command: npm ci
   ```

### 2. 設定環境變數

在 Vercel 專案設定中添加：
```
REACT_APP_API_BASE_URL=https://taiwan-med-ai-backend.onrender.com
```

### 3. 部署

點擊 "Deploy"，您的前端會部署到：
`https://your-project-name.vercel.app`

## 🧪 測試部署

### 健康檢查
```bash
curl https://taiwan-med-ai-backend.onrender.com/v1/monitoring/health
```

### 症狀分析測試
```bash
curl -X POST "https://taiwan-med-ai-backend.onrender.com/v1/triage/quick" \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_text": "頭痛發燒",
    "include_nearby_hospitals": false
  }'
```

## ⚠️ 免費方案限制

### Render 限制
- **休眠**：15分鐘無活動自動休眠
- **喚醒時間**：30-60秒
- **流量**：無限制
- **儲存**：臨時檔案系統

### 解決休眠問題
1. **使用 uptimerobot.com**：免費監控服務每5分鐘ping一次
2. **前端處理**：顯示載入中狀態等待API喚醒

## 🔄 自動部署工作流程

設定完成後：
1. 推送程式碼到 GitHub
2. Render 和 Vercel 自動檢測變更
3. 自動重新部署
4. 更新上線

## 💡 成本比較

| 服務 | 免費額度 | 限制 | 升級成本 |
|------|----------|------|----------|
| **Render** | 永久免費 | 休眠機制 | $7/月 |
| **Vercel** | 永久免費 | 無限制 | $20/月 |
| **總計** | **$0/月** | 休眠 | $27/月 |

vs

| 服務 | 費用 | 限制 |
|------|------|------|
| PythonAnywhere | $5/月 | 無休眠 |
| Vercel | $0/月 | 無限制 |
| **總計** | **$5/月** | 無限制 |

## 🎯 建議

- **學習/展示**：使用 Render 免費方案
- **正式使用**：考慮 PythonAnywhere Hacker 方案
- **企業級**：升級到付費方案

現在您有兩個選擇：
1. **完全免費**：Render + Vercel（有休眠）
2. **低成本**：PythonAnywhere + Vercel（$5/月，無休眠）

需要我幫您設定哪一個方案？