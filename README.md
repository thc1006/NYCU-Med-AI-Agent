# 🏥 台灣醫療 AI 助理系統 (Taiwan Medical AI Assistant)

專為台灣醫療環境設計的 AI 助理系統，提供症狀評估、醫院搜尋、緊急醫療指引等功能。

## 🌟 核心功能

- **症狀分級評估**：45種紅旗症狀自動檢測，提供就醫建議
- **醫院搜尋引擎**：整合 Google Places API，精確定位附近醫療院所
- **緊急醫療資訊**：台灣緊急聯絡資訊（119, 110, 112, 113, 165）
- **PDPA 合規審計**：完整隱私保護與醫療免責聲明
- **繁體中文介面**：100% 台灣在地化

## 📊 專案統計

- **程式碼行數**：33,266 行 Python 程式碼
- **測試覆蓋率**：80%+
- **API 端點**：11 個 RESTful 端點
- **測試案例**：625 個測試函數
- **支援症狀**：60 個症狀關鍵字

## 🚀 快速開始

### 環境需求

- Python 3.11+
- Google Cloud API 密鑰（Places API & Geocoding API）

### 安裝步驟

1. **複製專案**
```bash
git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent
```

2. **安裝依賴套件**
```bash
pip install -r requirements.txt
```

3. **設定環境變數**
```bash
# 建立 .env 檔案
GOOGLE_PLACES_API_KEY="your-api-key"
GOOGLE_GEOCODING_API_KEY="your-api-key"
```

4. **啟動服務**
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5. **開啟 API 文件**
```
http://localhost:8000/docs
```

## 📖 API 使用範例

### 症狀評估

**快速評估**
```bash
curl -X POST "http://localhost:8000/v1/triage/quick?symptom_text=頭痛"
```

**詳細分析**
```bash
curl -X POST "http://localhost:8000/v1/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_text": "胸痛、呼吸困難",
    "age": 45,
    "gender": "M",
    "duration_hours": 2
  }'
```

### 醫院搜尋

**座標搜尋**
```bash
curl "http://localhost:8000/v1/hospitals/nearby?latitude=25.033&longitude=121.565&radius=3000"
```

**地址搜尋**
```bash
curl "http://localhost:8000/v1/hospitals/nearby?address=台北車站&radius=2000"
```

**包含症狀檢測**
```bash
curl "http://localhost:8000/v1/hospitals/nearby?latitude=25.033&longitude=121.565&symptoms=胸痛"
```

### 緊急資訊

```bash
curl "http://localhost:8000/v1/hospitals/emergency-info"
```

## 📝 API 端點列表

### 症狀分級 (`/v1/triage`)
- `POST /v1/triage` - 完整症狀評估
- `POST /v1/triage/quick` - 快速症狀評估
- `GET /v1/triage/symptoms/emergency` - 緊急症狀列表
- `GET /v1/triage/symptoms/mild` - 輕微症狀列表
- `GET /v1/triage/departments` - 科別對照表

### 醫院搜尋 (`/v1/hospitals`)
- `GET /v1/hospitals/nearby` - 搜尋附近醫院
- `GET /v1/hospitals/nearby/simple` - 簡化版搜尋
- `GET /v1/hospitals/emergency-info` - 緊急醫療資訊

### 健康資訊 (`/v1/healthinfo`)
- `GET /v1/healthinfo/topics` - 健康主題
- `GET /v1/healthinfo/resources` - 醫療資源
- `GET /v1/healthinfo/vaccinations` - 疫苗資訊

### 監控系統 (`/v1/monitoring`)
- `GET /v1/monitoring/health` - 系統健康狀態
- `GET /v1/monitoring/metrics` - 效能指標
- `GET /v1/monitoring/dashboard` - 監控儀表板

## 🔧 開發與測試

### 執行測試
```bash
# 執行所有測試
pytest tests/

# 執行特定測試
pytest tests/unit/

# 檢查測試覆蓋率
pytest --cov=app --cov-report=html
```

### 程式碼品質檢查
```bash
# PEP8 檢查
flake8 app/

# 類型檢查
mypy app/

# 格式化
black app/
```

## 🏗️ 專案結構

```
NYCU-Med-AI-Agent/
├── app/
│   ├── main.py              # FastAPI 主程式
│   ├── config.py            # 設定管理
│   ├── domain/              # 領域模型
│   │   ├── models.py        # 資料模型
│   │   ├── triage.py        # 症狀分級邏輯
│   │   └── rules_tw.py      # 台灣醫療規則
│   ├── routers/             # API 路由
│   │   ├── hospitals.py     # 醫院搜尋
│   │   ├── triage.py        # 症狀分級
│   │   └── monitoring.py    # 監控端點
│   ├── services/            # 外部服務
│   │   ├── places.py        # Google Places
│   │   ├── geocoding.py     # 地理編碼
│   │   └── nhia_registry.py # 健保特約
│   ├── middlewares/         # 中介層
│   │   ├── privacy.py       # PDPA 合規
│   │   └── rate_limit.py    # 速率限制
│   └── monitoring/          # 監控系統
│       ├── health.py        # 健康檢查
│       └── metrics.py       # 度量收集
├── tests/                   # 測試套件
├── docs/                    # 文件
├── requirements.txt         # 依賴套件
└── .env                     # 環境變數
```

## 🔐 安全與合規

- **PDPA 合規**：所有個資處理符合台灣個資法
- **醫療免責聲明**：每個 API 回應都包含免責聲明
- **隱私保護**：不儲存使用者個人資料
- **加密傳輸**：支援 HTTPS
- **速率限制**：防止 API 濫用

## 🚨 緊急聯絡資訊

- **119**：消防救護專線
- **110**：警察報案專線
- **112**：手機緊急撥號
- **113**：婦幼保護專線
- **165**：反詐騙諮詢專線

## 📄 授權

MIT License

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

## ⚠️ 醫療免責聲明

本系統僅供醫療資訊參考，不能取代專業醫療診斷。如有緊急狀況，請立即撥打 119 或前往最近的急診室。

---

**開發團隊**：NYCU Medical AI Team
**版本**：v0.1.0
**最後更新**：2025-09-20