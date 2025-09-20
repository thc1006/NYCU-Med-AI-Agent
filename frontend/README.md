# 台灣醫療 AI 助手 - 前端應用

## 📱 專案簡介

台灣醫療 AI 助手前端是一個基於 React + TypeScript 的響應式網頁應用程式，提供症狀分級評估與就近醫療院所搜尋功能。

### 🎯 主要功能

- **症狀輸入與評估** - 支援文字輸入和常見症狀快選
- **智慧分級系統** - 紅旗症狀優先處理
- **醫院搜尋** - 基於地理位置的醫院搜尋和篩選
- **緊急撥號** - 一鍵撥打 119/110/112
- **症狀歷史** - 本地儲存查詢記錄
- **響應式設計** - 支援手機、平板、桌面裝置

## 🚀 技術棧

### 核心框架
- **React 18** - 前端框架
- **TypeScript** - 類型安全
- **React Router DOM** - 路由管理

### 狀態管理
- **Zustand** - 輕量級狀態管理
- **React Hot Toast** - 通知系統

### UI/UX
- **Tailwind CSS** - 原子化 CSS 框架
- **Lucide React** - 圖示庫
- **響應式設計** - Mobile-first 設計理念

### 工具與服務
- **Axios** - HTTP 客戶端
- **PWA 支援** - 漸進式網頁應用
- **Service Worker** - 離線支援

## 📁 專案結構

```
frontend/
├── public/                     # 靜態資源
│   ├── index.html             # HTML 模板
│   ├── manifest.json          # PWA 配置
│   └── favicon.ico            # 網站圖示
├── src/
│   ├── components/            # React 元件
│   │   ├── Layout/           # 佈局元件
│   │   │   └── Header.tsx    # 標題列
│   │   ├── SymptomForm/      # 症狀表單
│   │   │   ├── SymptomForm.tsx
│   │   │   ├── QuickSymptomSelect.tsx
│   │   │   └── AdditionalInfoForm.tsx
│   │   ├── TriageResult/     # 分級結果
│   │   │   ├── TriageResult.tsx
│   │   │   └── EmergencyActions.tsx
│   │   ├── HospitalList/     # 醫院列表
│   │   │   ├── HospitalList.tsx
│   │   │   ├── HospitalCard.tsx
│   │   │   └── HospitalFilters.tsx
│   │   └── SymptomHistory/   # 症狀歷史
│   │       ├── SymptomHistory.tsx
│   │       └── SymptomHistoryItem.tsx
│   ├── pages/                # 頁面元件
│   │   ├── HomePage.tsx      # 首頁
│   │   └── HistoryPage.tsx   # 歷史頁面
│   ├── services/             # API 服務
│   │   └── api.ts           # API 客戶端
│   ├── stores/               # 狀態管理
│   │   └── useAppStore.ts   # 主要 Store
│   ├── hooks/                # 自定義 Hooks
│   │   └── useGeolocation.ts # 地理位置 Hook
│   ├── types/                # 類型定義
│   │   └── index.ts         # 主要類型
│   ├── styles/               # 樣式檔案
│   │   └── index.css        # 主要樣式
│   ├── App.tsx              # 主應用元件
│   └── index.tsx            # 應用入口點
├── package.json             # 專案配置
├── tsconfig.json           # TypeScript 配置
├── tailwind.config.js      # Tailwind 配置
└── postcss.config.js       # PostCSS 配置
```

## 🛠️ 開發指南

### 環境需求

- Node.js 16+
- npm 或 yarn
- 現代瀏覽器（支援 ES2017+）

### 安裝與執行

```bash
# 安裝依賴
npm install

# 啟動開發伺服器
npm start

# 建構生產版本
npm run build

# 執行測試
npm test

# 類型檢查
npm run typecheck
```

### 開發伺服器

開發伺服器會在 `http://localhost:3000` 啟動，並自動代理 API 請求到 `http://localhost:8000`。

## 🎨 設計規範

### 色彩系統

```css
/* 主要色彩 */
--primary: #EF4444    /* 紅色 - 緊急、主要按鈕 */
--secondary: #6B7280  /* 灰色 - 次要元素 */
--success: #10B981    /* 綠色 - 成功狀態 */
--warning: #F59E0B    /* 橙色 - 警告狀態 */
--danger: #EF4444     /* 紅色 - 錯誤、緊急 */
```

### 響應式斷點

```css
/* Tailwind CSS 斷點 */
sm: 640px     /* 小型裝置 */
md: 768px     /* 中型裝置 */
lg: 1024px    /* 大型裝置 */
xl: 1280px    /* 超大型裝置 */
```

### 字體系統

- 主要字體：Noto Sans TC（繁體中文優化）
- 英文字體：-apple-system, BlinkMacSystemFont, Segoe UI
- 字重：300 (輕), 400 (正常), 500 (中), 700 (粗)

## 🔗 API 整合

### 後端 API 端點

```typescript
// 症狀評估
POST /v1/triage/quick
{
  "symptom_text": "症狀描述",
  "age": 25,
  "gender": "M",
  "duration_hours": 2,
  "has_chronic_disease": false,
  "medications": [],
  "include_nearby_hospitals": true,
  "location": {
    "latitude": 25.0339,
    "longitude": 121.5645
  }
}

// 醫院搜尋
GET /v1/hospitals/nearby?lat=25.0339&lng=121.5645&radius=5000

// 緊急資訊
GET /v1/hospitals/emergency-info
```

### 錯誤處理

- 網路錯誤：自動重試機制
- API 錯誤：使用者友善的錯誤訊息
- 表單驗證：即時驗證與提示

## 🌟 功能特色

### 1. 智慧症狀評估

- **快速選擇**：預設常見症狀分類（緊急、一般）
- **詳細資訊**：可選填年齡、性別、病史等
- **即時驗證**：輸入驗證與格式化

### 2. 地理位置服務

- **自動定位**：支援 GPS 定位
- **隱私保護**：位置資訊不會被儲存
- **距離計算**：自動計算醫院距離

### 3. 緊急處理機制

- **紅旗症狀**：自動識別緊急症狀
- **快速撥號**：一鍵撥打緊急電話
- **視覺提醒**：緊急狀況的顯著提示

### 4. 醫院搜尋與篩選

- **智慧篩選**：依科別、距離、急診服務篩選
- **詳細資訊**：醫院地址、電話、科別
- **導航整合**：與 Google Maps 整合

### 5. 症狀歷史管理

- **本地儲存**：使用 localStorage 保存歷史
- **隱私保護**：不儲存敏感個人資訊
- **快速重用**：點擊歷史記錄可重新填入

## 📱 PWA 功能

### 安裝與離線支援

- **可安裝**：支援新增到主畫面
- **離線瀏覽**：基本功能離線可用
- **自動更新**：新版本自動更新

### 原生功能整合

- **撥號功能**：直接開啟撥號程式
- **定位服務**：整合裝置 GPS
- **通知系統**：系統層級通知

## 🔒 安全性考量

### 資料保護

- **PDPA 合規**：不儲存個人敏感資訊
- **最小化原則**：只收集必要資料
- **本地儲存**：敏感資料不傳送到伺服器

### 醫療安全

- **免責聲明**：每次輸出都包含免責條款
- **緊急優先**：紅旗症狀優先處理
- **專業建議**：不取代專業醫療診斷

## 🧪 測試策略

### 單元測試

```bash
# 執行測試
npm test

# 測試覆蓋率
npm run test:coverage
```

### E2E 測試

- 症狀輸入流程測試
- 醫院搜尋功能測試
- 緊急撥號功能測試

## 🚀 部署指南

### 建構生產版本

```bash
npm run build
```

### 環境變數

```bash
# .env.production
REACT_APP_API_BASE_URL=https://api.example.com
REACT_APP_GOOGLE_MAPS_API_KEY=your_api_key
```

### 效能優化

- **代碼分割**：路由層級的懶加載
- **圖片優化**：WebP 格式與壓縮
- **快取策略**：靜態資源長期快取

## 🤝 貢獻指南

### 開發規範

1. **TypeScript**：所有新程式碼必須使用 TypeScript
2. **ESLint**：遵循專案 ESLint 規則
3. **Prettier**：使用 Prettier 格式化程式碼
4. **測試**：新功能必須包含測試

### 提交規範

```bash
feat: 新增症狀評估功能
fix: 修復醫院搜尋問題
docs: 更新 README 文檔
style: 調整 UI 樣式
test: 新增單元測試
```

## 📞 支援與聯絡

- **問題回報**：GitHub Issues
- **功能建議**：GitHub Discussions
- **緊急聯絡**：119 (醫療緊急)、110 (警察)、112 (手機緊急)

## 📄 授權條款

本專案採用 MIT 授權條款。詳細資訊請參閱 LICENSE 檔案。

---

**免責聲明**：本系統僅供症狀分級參考，不可取代專業醫療診斷。如有緊急醫療狀況，請立即撥打 119 尋求協助。