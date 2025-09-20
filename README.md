# 🏥 台灣醫療 AI 助理系統 (Taiwan Medical AI Assistant)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Code Coverage](https://img.shields.io/badge/coverage-80%2B-brightgreen.svg)](https://pytest-cov.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PDPA Compliant](https://img.shields.io/badge/PDPA-Compliant-blue.svg)](https://law.moj.gov.tw/eng/LawClass/LawAll.aspx?PCode=I0050021)

> 🏥 **專為台灣醫療環境設計的智能 AI 助理系統**
> A Taiwan-localized medical AI assistant designed for the local healthcare environment

專為台灣醫療環境設計的 AI 助理系統，結合現代化 React 前端與 FastAPI 後端，提供症狀評估、醫院搜尋、緊急醫療指引等功能。具備玻璃效果設計的直觀介面與完整的監控、審計與 PDPA 合規功能。

## 🌟 主要特色 (Key Features)

### 🎨 現代化前端介面
- **React 18 + TypeScript**：完整的現代前端架構
- **玻璃效果設計**：優雅的視覺體驗與直觀操作
- **PWA 支援**：可安裝的 Web 應用程式
- **響應式設計**：完美支援手機與桌面裝置

### 🇹🇼 台灣在地化 (Taiwan Localization)
- **繁體中文優先**：完整支援正體中文介面與回應
- **台灣急救系統整合**：119/110/112/113/165 急救熱線整合
- **健保體系相容**：整合衛福部醫療院所資料
- **PDPA 合規**：符合《個人資料保護法》的隱私保護

### 🏥 核心醫療功能
- **智能症狀分析**：基於規則與 AI 的症狀分級系統
- **緊急狀況識別**：自動識別緊急醫療狀況並引導至急救系統
- **就近醫療搜尋**：整合 Google Places API 的醫療院所定位
- **健康資訊服務**：提供權威的健康教育與醫療指引

### 🛡️ 企業級監控
- **結構化日誌**：完整的操作審計與事件追蹤
- **即時健康監控**：API 健康狀態與效能監控
- **度量分析**：詳細的使用統計與效能分析
- **速率限制**：防止濫用的智能限流機制

## 📊 專案統計

- **程式碼行數**：33,266 行 Python 程式碼
- **測試覆蓋率**：80%+
- **API 端點**：11 個 RESTful 端點
- **測試案例**：625 個測試函數
- **支援症狀**：60 個症狀關鍵字
- **前端元件**：React + TypeScript 現代化架構

## 🚀 快速開始 (Quick Start)

### 環境要求 (Requirements)

- **Python**: 3.11 或更高版本
- **Google Places API Key**: 用於醫療院所搜尋功能
- **作業系統**: Windows/Linux/macOS

### 1. 安裝與設定 (Installation)

```bash
# 複製專案
git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent

# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境變數設定 (Environment Configuration)

```bash
# 複製環境變數範本
cp .env.example .env

# 編輯 .env 檔案
# 必填：GOOGLE_PLACES_API_KEY
```

**.env 檔案範例**：
```ini
# Google Places API 設定 (必填)
GOOGLE_PLACES_API_KEY=your_google_places_api_key_here

# 台灣在地化設定
DEFAULT_LANG=zh-TW
REGION=TW

# 應用程式設定
APP_NAME=台灣醫療 AI 助理
APP_VERSION=0.1.0
DEBUG=false

# API 服務設定
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. 啟動服務 (Start the Service)

```bash
# 開發模式啟動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生產模式啟動
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 驗證安裝 (Verify Installation)

```bash
# 健康檢查
curl http://localhost:8000/healthz

# 查看 API 文檔
# 瀏覽器開啟: http://localhost:8000/docs
```

## 📚 API 文檔 (API Documentation)

### 基礎資訊 (Basic Information)

| 項目 | 說明 |
|------|------|
| 基礎 URL | `http://localhost:8000` |
| API 版本 | v1 |
| 文檔位置 | `/docs` (Swagger), `/redoc` (ReDoc) |
| 健康檢查 | `/healthz` |

### 核心端點 (Core Endpoints)

#### 1. 症狀分析與分流 (Symptom Triage)

**POST** `/v1/triage`

```json
// 請求範例
{
  "symptom_text": "胸痛伴隨冷汗，呼吸困難"
}

// 回應範例
{
  "level": "emergency",
  "advice": "您的症狀顯示可能的心臟急症，請立即撥打 119 或前往最近的急診室。",
  "next_steps": [
    "立即撥打 119",
    "保持冷靜，避免劇烈活動",
    "準備身分證與健保卡"
  ],
  "emergency_contacts": {
    "119": "消防救護專線",
    "112": "行動電話緊急號碼"
  },
  "disclaimer": "本系統僅供參考，不替代專業醫療診斷。緊急狀況請立即求醫。"
}
```

#### 2. 就近醫療院所搜尋 (Nearby Hospitals)

**GET** `/v1/hospitals/nearby`

**查詢參數**：
- `lat` (float): 緯度
- `lng` (float): 經度
- `radius` (int): 搜尋半徑（公尺，預設 3000）
- `type` (string): 醫療類型（hospital, clinic）

```json
// 回應範例
{
  "results": [
    {
      "name": "臺大醫院",
      "address": "台北市中正區中山南路7號",
      "phone": "+886-2-23123456",
      "rating": 4.5,
      "distance_meters": 850,
      "opening_hours": "24小時",
      "has_emergency": true,
      "nhi_contracted": true
    }
  ],
  "search_params": {
    "location": {"lat": 25.0339, "lng": 121.5645},
    "radius": 3000,
    "total_found": 12
  },
  "emergency_guidance": {
    "119": "消防救護專線",
    "112": "行動電話緊急號碼"
  }
}
```

#### 3. 健康資訊服務 (Health Information)

**GET** `/v1/health-info/topics`

```json
// 回應範例
{
  "topics": [
    {
      "id": "emergency_procedures",
      "title": "緊急就醫程序",
      "summary": "緊急狀況的處理流程與注意事項",
      "category": "急救指引",
      "url": "https://www.mohw.gov.tw/emergency-guide"
    },
    {
      "id": "nhi_services",
      "title": "健保就醫指南",
      "summary": "健保給付範圍與就醫流程說明",
      "category": "健保資訊",
      "url": "https://www.nhi.gov.tw/guide"
    }
  ]
}
```

#### 4. 系統監控 (System Monitoring)

**GET** `/v1/monitoring/health`

```json
{
  "status": "healthy",
  "timestamp": "2024-09-19T10:30:00Z",
  "services": {
    "api": {"status": "up", "response_time_ms": 45},
    "google_places": {"status": "up", "last_check": "2024-09-19T10:29:30Z"},
    "database": {"status": "up", "connections": 3}
  },
  "metrics": {
    "uptime_seconds": 86400,
    "total_requests": 1250,
    "avg_response_time_ms": 120
  }
}
```

**GET** `/v1/monitoring/metrics`

系統效能指標與使用統計。

**GET** `/v1/monitoring/dashboard`

監控儀表板數據（包含圖表資料）。

### 錯誤回應格式 (Error Response Format)

```json
{
  "error": {
    "code": "INVALID_SYMPTOM",
    "message": "症狀描述不能為空",
    "details": "請提供具體的症狀描述以進行分析",
    "request_id": "req_123456789"
  },
  "emergency_guidance": {
    "119": "如有緊急狀況，請撥打 119",
    "112": "行動電話可撥打 112"
  }
}
```

## 🧪 測試 (Testing)

### 執行測試套件

```bash
# 安裝測試依賴
pip install -r requirements-test.txt

# 執行全部測試
pytest

# 執行特定類型測試
pytest -m unit          # 單元測試
pytest -m integration   # 整合測試
pytest -m e2e           # 端到端測試

# 生成覆蓋率報告
pytest --cov=app --cov-report=html
# 查看報告：open htmlcov/index.html
```

### 測試分類標記

| 標記 | 說明 |
|------|------|
| `unit` | 單元測試 |
| `integration` | 整合測試 |
| `e2e` | 端到端測試 |
| `medical_safety` | 醫療安全相關測試 |
| `taiwan_localization` | 台灣在地化測試 |

### 測試覆蓋率要求

- **最低覆蓋率**: 80%
- **核心模組覆蓋率**: 90% 以上
- **醫療安全功能**: 100% 覆蓋

## 🏗️ 系統架構 (System Architecture)

### 整體架構圖

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │    │   Web Browser   │    │   Mobile Apps   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      Load Balancer       │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │      FastAPI Gateway     │
                    │    (Rate Limit + Auth)   │
                    └─────────────┬─────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
   ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
   │ Triage Service  │  │Hospital Service │  │ Health Service  │
   │ (症狀分析)      │  │ (院所搜尋)      │  │ (健康資訊)      │
   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     External APIs        │
                    │ • Google Places API      │
                    │ • Google Geocoding API   │
                    │ • MOHW Open Data        │
                    └──────────────────────────┘
```

### 核心模組結構

```
app/
├── main.py                 # FastAPI 應用程式入口
├── config.py              # 設定管理
├── domain/                # 領域模型
│   ├── models.py          # Pydantic 資料模型
│   ├── rules_tw.py        # 台灣醫療規則
│   └── triage.py          # 症狀分級邏輯
├── services/              # 業務邏輯服務
│   ├── geocoding.py       # 地理編碼服務
│   ├── places.py          # 醫療院所搜尋
│   ├── triage.py          # 症狀分析服務
│   └── health_info.py     # 健康資訊服務
├── routers/               # API 路由
│   ├── triage.py          # 症狀分析路由
│   ├── hospitals.py       # 醫院搜尋路由
│   ├── healthinfo.py      # 健康資訊路由
│   ├── meta.py            # 系統元資訊
│   └── monitoring.py      # 監控與度量
├── middlewares/           # 中介軟體
│   ├── privacy.py         # 隱私保護 (PDPA)
│   ├── rate_limit.py      # 速率限制
│   └── structured_logging.py # 結構化日誌
└── monitoring/            # 監控系統
    ├── health.py          # 健康檢查
    ├── metrics.py         # 度量收集
    └── structured_logging.py # 日誌管理
```

## 🔧 開發指南 (Development Guide)

### 開發環境設定

```bash
# 安裝開發依賴
pip install -r requirements-dev.txt

# 啟用 pre-commit hooks
pre-commit install

# 設定 IDE
# VS Code: 安裝 Python、FastAPI 擴充功能
# PyCharm: 設定 Python 解譯器為虛擬環境
```

### 程式碼品質工具

| 工具 | 用途 | 執行指令 |
|------|------|----------|
| **Black** | 程式碼格式化 | `black app/ tests/` |
| **isort** | import 排序 | `isort app/ tests/` |
| **flake8** | 語法檢查 | `flake8 app/ tests/` |
| **mypy** | 型別檢查 | `mypy app/` |
| **pytest** | 測試執行 | `pytest` |

### 程式碼風格指南

#### 1. 檔案結構
- 每個檔案不超過 500 行
- 使用有意義的檔案和目錄名稱
- 遵循 FastAPI 專案結構慣例

#### 2. 命名規範
```python
# 變數與函數：snake_case
def get_user_profile():
    user_id = "12345"

# 類別：PascalCase
class SymptomAnalyzer:
    pass

# 常數：UPPER_SNAKE_CASE
EMERGENCY_KEYWORDS = ["胸痛", "呼吸困難"]

# 私有屬性：前綴底線
class Service:
    def __init__(self):
        self._internal_state = {}
```

#### 3. 文檔字串格式
```python
def analyze_symptoms(symptom_text: str) -> TriageResult:
    """
    分析症狀並進行醫療分流

    Args:
        symptom_text: 使用者描述的症狀文字

    Returns:
        TriageResult: 包含風險等級與建議的分析結果

    Raises:
        ValueError: 當症狀描述為空或無效時

    Example:
        >>> result = analyze_symptoms("頭痛發燒")
        >>> print(result.level)
        'outpatient'
    """
```

### TDD 開發流程

1. **撰寫失敗測試** (Red)
   ```bash
   # 建立測試檔案
   tests/unit/test_new_feature.py
   ```

2. **實作最小功能** (Green)
   ```bash
   # 讓測試通過的最小實作
   app/services/new_feature.py
   ```

3. **重構改善** (Refactor)
   ```bash
   # 改善程式碼品質
   black app/ tests/
   pytest
   ```

## 🐳 Docker 部署 (Docker Deployment)

### 建立 Docker 映像

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY app/ ./app/

# 建立非 root 使用者
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# 暴露埠號
EXPOSE 8000

# 啟動指令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose 配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  taiwan-med-ai:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_PLACES_API_KEY=${GOOGLE_PLACES_API_KEY}
      - DEFAULT_LANG=zh-TW
      - REGION=TW
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - taiwan-med-ai
    restart: unless-stopped
```

### 部署指令

```bash
# 建立映像
docker build -t taiwan-med-ai:latest .

# 本地測試
docker run -p 8000:8000 --env-file .env taiwan-med-ai:latest

# 使用 Docker Compose
docker-compose up -d

# 查看日誌
docker-compose logs -f taiwan-med-ai

# 擴展服務
docker-compose up -d --scale taiwan-med-ai=3
```

## 🚀 生產環境部署 (Production Deployment)

### 系統需求

| 元件 | 最低需求 | 建議規格 |
|------|----------|----------|
| **CPU** | 2 核心 | 4 核心以上 |
| **記憶體** | 4GB | 8GB 以上 |
| **儲存** | 20GB SSD | 50GB SSD |
| **網路** | 100Mbps | 1Gbps |
| **作業系統** | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### 部署步驟

#### 1. 伺服器準備
```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝必要套件
sudo apt install -y python3.11 python3.11-venv nginx certbot

# 建立應用程式使用者
sudo useradd -m -s /bin/bash taiwan-med-ai
sudo usermod -aG sudo taiwan-med-ai
```

#### 2. 應用程式部署
```bash
# 切換至應用程式使用者
sudo su - taiwan-med-ai

# 複製程式碼
git clone https://github.com/thc1006/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent

# 建立虛擬環境
python3.11 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 設定實際的 API 金鑰
```

#### 3. Systemd 服務設定
```ini
# /etc/systemd/system/taiwan-med-ai.service
[Unit]
Description=Taiwan Medical AI Assistant
After=network.target

[Service]
Type=exec
User=taiwan-med-ai
Group=taiwan-med-ai
WorkingDirectory=/home/taiwan-med-ai/NYCU-Med-AI-Agent
Environment=PATH=/home/taiwan-med-ai/NYCU-Med-AI-Agent/venv/bin
EnvironmentFile=/home/taiwan-med-ai/NYCU-Med-AI-Agent/.env
ExecStart=/home/taiwan-med-ai/NYCU-Med-AI-Agent/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# 啟用服務
sudo systemctl enable taiwan-med-ai
sudo systemctl start taiwan-med-ai
sudo systemctl status taiwan-med-ai
```

#### 4. Nginx 反向代理設定
```nginx
# /etc/nginx/sites-available/taiwan-med-ai
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL 設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # 安全標頭
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # 代理設定
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 逾時設定
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康檢查
    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
        access_log off;
    }

    # 靜態檔案快取
    location /static {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# 啟用網站
sudo ln -s /etc/nginx/sites-available/taiwan-med-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 設定 SSL 憑證
sudo certbot --nginx -d your-domain.com
```

### 監控與日誌

#### 1. 日誌管理
```bash
# 設定 logrotate
sudo tee /etc/logrotate.d/taiwan-med-ai <<EOF
/home/taiwan-med-ai/NYCU-Med-AI-Agent/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 taiwan-med-ai taiwan-med-ai
    postrotate
        systemctl reload taiwan-med-ai
    endscript
}
EOF
```

#### 2. 系統監控
```bash
# 安裝監控工具
sudo apt install -y htop iotop nethogs

# 設定自動監控腳本
cat > /home/taiwan-med-ai/monitor.sh <<EOF
#!/bin/bash
# 監控系統資源
DATE=$(date '+%Y-%m-%d %H:%M:%S')
CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')
MEM=$(free | grep Mem | awk '{printf "%.2f%%", $3/$2 * 100.0}')
DISK=$(df -h / | awk 'NR==2{printf "%s", $5}')

echo "[$DATE] CPU: $CPU%, Memory: $MEM, Disk: $DISK" >> /home/taiwan-med-ai/system.log
EOF

chmod +x /home/taiwan-med-ai/monitor.sh

# 設定 crontab
echo "*/5 * * * * /home/taiwan-med-ai/monitor.sh" | crontab -
```

## 🔍 故障排除 (Troubleshooting)

### 常見問題與解決方案

#### 1. Google Places API 錯誤

**問題**: `401 Unauthorized` 或 `403 Forbidden`
```bash
# 檢查 API 金鑰
curl -X GET "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=25.0339,121.5645&radius=3000&key=YOUR_API_KEY"
```

**解決方案**:
- 確認 API 金鑰正確設定在 `.env` 檔案
- 檢查 Google Cloud Console 中的 API 啟用狀態
- 確認計費帳戶已設定

#### 2. 服務無法啟動

**問題**: `uvicorn` 無法啟動或頻繁重啟

**檢查步驟**:
```bash
# 檢查服務狀態
sudo systemctl status taiwan-med-ai

# 查看詳細日誌
sudo journalctl -u taiwan-med-ai -f

# 檢查埠號占用
sudo netstat -tlnp | grep :8000

# 手動測試
cd /home/taiwan-med-ai/NYCU-Med-AI-Agent
source venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level debug
```

**常見解決方案**:
- 檢查 `.env` 檔案中的必要環境變數
- 確認虛擬環境路徑正確
- 檢查檔案權限 (`chown -R taiwan-med-ai:taiwan-med-ai /home/taiwan-med-ai/`)

#### 3. 記憶體不足

**問題**: 系統記憶體使用率過高

```bash
# 檢查記憶體使用
free -h
top -p $(pgrep -f uvicorn)

# 檢查日誌大小
du -sh /home/taiwan-med-ai/NYCU-Med-AI-Agent/logs/
```

**優化措施**:
- 減少 worker 數量 (`--workers 2`)
- 設定 log rotation
- 增加 swap 空間

#### 4. API 回應緩慢

**診斷工具**:
```bash
# 檢查 API 回應時間
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/healthz

# curl-format.txt 內容:
#     time_namelookup:  %{time_namelookup}\n
#        time_connect:  %{time_connect}\n
#     time_appconnect:  %{time_appconnect}\n
#    time_pretransfer:  %{time_pretransfer}\n
#       time_redirect:  %{time_redirect}\n
#  time_starttransfer:  %{time_starttransfer}\n
#                     ----------\n
#          time_total:  %{time_total}\n
```

**效能調優**:
- 啟用 HTTP/2 (`nginx` 設定)
- 使用 Redis 快取 (`pip install redis`)
- 優化資料庫查詢
- 啟用 gzip 壓縮

### 日誌分析

#### 1. 應用程式日誌
```bash
# 即時監控日誌
tail -f /home/taiwan-med-ai/NYCU-Med-AI-Agent/logs/app.log

# 錯誤日誌過濾
grep -i error /home/taiwan-med-ai/NYCU-Med-AI-Agent/logs/app.log

# 統計 API 使用
awk '/POST \/v1\/triage/ {count++} END {print "Triage API calls:", count}' /var/log/nginx/access.log
```

#### 2. 系統日誌
```bash
# 系統服務日誌
sudo journalctl -u taiwan-med-ai --since "1 hour ago"

# Nginx 日誌
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🛡️ 安全性 (Security)

### PDPA 合規性

本系統嚴格遵循《個人資料保護法》：

#### 資料保護措施
- **最小化原則**: 僅收集必要的醫療諮詢資訊
- **去識別化**: 自動移除或遮罩個人識別資訊
- **加密傳輸**: 所有 API 通訊採用 HTTPS/TLS 1.3
- **存取記錄**: 完整的資料存取審計軌跡

#### 隱私保護功能
```python
# 自動資料遮罩範例
# 輸入: "我叫王小明，電話0912345678，身分證A123456789"
# 輸出: "我叫***，電話09****5678，身分證A12****789"
```

### 系統安全

#### 1. 認證與授權
- API 金鑰驗證
- 請求簽名驗證（可選）
- IP 白名單限制（生產環境）

#### 2. 速率限制
```python
# 預設限制
- 每分鐘 60 次請求（一般 API）
- 每分鐘 10 次請求（AI 分析 API）
- 每小時 1000 次請求（總計）
```

#### 3. 輸入驗證
- 嚴格的資料格式驗證
- SQL 注入防護
- XSS 攻擊防護
- CSRF 保護

### 安全配置檢查清單

- [ ] HTTPS 強制重定向已啟用
- [ ] SSL 憑證有效且自動更新
- [ ] 防火牆規則已正確設定
- [ ] 系統定期安全更新
- [ ] 日誌監控與異常告警
- [ ] 備份與災難恢復計畫
- [ ] 定期安全掃描與滲透測試

## 📊 效能基準 (Performance Benchmarks)

### 系統效能指標

| 測試項目 | 目標值 | 測試條件 |
|----------|--------|----------|
| **API 回應時間** | < 200ms | 單一請求，本地網路 |
| **併發處理** | 100 req/s | 4 worker, 8GB RAM |
| **症狀分析** | < 500ms | 複雜症狀，包含 AI 分析 |
| **醫院搜尋** | < 300ms | 半徑 3km，回傳 10 筆結果 |
| **系統可用性** | > 99.9% | 24x7 運行 |

### 負載測試結果

```bash
# 使用 wrk 進行負載測試
wrk -t8 -c100 -d30s --latency http://localhost:8000/healthz

# 預期結果:
# Requests/sec:    3245.67
# Latency (avg):   30.82ms
# Latency (99%):   89.23ms
```

### 記憶體使用

| 元件 | 基礎記憶體 | 高負載記憶體 |
|------|------------|--------------|
| **Python 程序** | 45MB | 120MB |
| **Nginx** | 8MB | 25MB |
| **系統緩存** | 50MB | 200MB |
| **總計** | 103MB | 345MB |

## 🤝 貢獻指南 (Contributing)

我們歡迎各種形式的貢獻，包括但不限於：

- 🐛 錯誤回報與修復
- ✨ 新功能提案與實作
- 📚 文檔改善與翻譯
- 🧪 測試案例補充
- 🎨 使用者介面改善

### 貢獻流程

#### 1. 環境準備
```bash
# Fork 專案到你的 GitHub 帳號
# Clone 到本地
git clone https://github.com/YOUR_USERNAME/NYCU-Med-AI-Agent.git
cd NYCU-Med-AI-Agent

# 新增原始專案為 upstream
git remote add upstream https://github.com/thc1006/NYCU-Med-AI-Agent.git

# 建立開發環境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate     # Windows

pip install -r requirements-dev.txt
pre-commit install
```

#### 2. 開發工作流程
```bash
# 建立功能分支
git checkout -b feature/your-feature-name

# 開發新功能（遵循 TDD）
# 1. 撰寫測試
# 2. 實作功能
# 3. 確認測試通過

# 檢查程式碼品質
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
pytest

# 提交變更
git add .
git commit -m "feat: add your feature description"

# 推送至你的 fork
git push origin feature/your-feature-name
```

#### 3. 提交 Pull Request
1. 在 GitHub 上建立 Pull Request
2. 填寫 PR 模板中的所有欄位
3. 確保所有 CI 檢查通過
4. 等待程式碼審查與回饋

### 程式碼貢獻標準

#### 提交訊息格式
使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**類型說明**:
- `feat`: 新功能
- `fix`: 錯誤修復
- `docs`: 文檔更新
- `style`: 程式碼格式（不影響功能）
- `refactor`: 重構
- `test`: 測試相關
- `chore`: 建置工具、輔助工具更新

**範例**:
```
feat(triage): add emergency keyword detection

Add automated detection of emergency symptoms like "胸痛" and "呼吸困難"
to improve emergency case identification accuracy.

Fixes #123
```

#### Pull Request 模板

```markdown
## 變更摘要 (Summary)
簡述此 PR 的主要變更內容

## 變更類型 (Type of Change)
- [ ] 錯誤修復 (Bug fix)
- [ ] 新功能 (New feature)
- [ ] 重大變更 (Breaking change)
- [ ] 文檔更新 (Documentation update)

## 測試 (Testing)
- [ ] 新增了測試案例
- [ ] 所有測試都通過
- [ ] 程式碼覆蓋率符合要求

## 檢查清單 (Checklist)
- [ ] 程式碼遵循專案風格指南
- [ ] 進行了自我程式碼審查
- [ ] 測試涵蓋了變更內容
- [ ] 更新了相關文檔
- [ ] 變更不會影響現有功能

## 相關議題 (Related Issues)
Fixes #(issue_number)
```

### 程式碼審查指南

#### 審查重點
1. **功能正確性**: 程式碼是否正確實現需求
2. **安全性**: 是否存在安全漏洞或隱私問題
3. **效能**: 是否有效能問題或改善空間
4. **可維護性**: 程式碼是否清晰易懂
5. **測試覆蓋**: 是否有足夠的測試案例

#### 醫療安全特別注意事項
- 緊急狀況判斷邏輯必須經過醫療專家驗證
- 所有醫療建議必須包含免責聲明
- 個人資料處理必須符合 PDPA 規範
- API 回應不得包含確診性醫療意見

## 📝 變更記錄 (Changelog)

### [0.1.0] - 2024-09-19

#### 新增 (Added)
- 🏥 完整的台灣醫療 AI 助理系統
- 🧠 基於規則的症狀分析與風險分級
- 🗺️ 整合 Google Places API 的醫療院所搜尋
- 🇹🇼 台灣急救系統整合 (119/110/112/113/165)
- 🛡️ PDPA 合規的隱私保護機制
- 📊 完整的監控、度量與審計系統
- 🧪 TDD 驅動的高測試覆蓋率 (80%+)
- 📚 繁體中文優先的使用者介面

#### 技術特性 (Technical Features)
- FastAPI 架構的高效能 API 服務
- 結構化日誌與事件追蹤
- 智能速率限制與防濫用機制
- 自動化健康檢查與故障恢復
- Docker 容器化部署支援
- Nginx 反向代理設定

## 📚 相關資源 (Resources)

### 官方文檔
- [FastAPI 官方文檔](https://fastapi.tiangolo.com/)
- [Google Places API 文檔](https://developers.google.com/maps/documentation/places/web-service)
- [個人資料保護法 (PDPA)](https://law.moj.gov.tw/eng/LawClass/LawAll.aspx?PCode=I0050021)

### 醫療資源
- [衛生福利部](https://www.mohw.gov.tw/)
- [中央健康保險署](https://www.nhi.gov.tw/)
- [台灣急救熱線說明](https://english.gov.taipei/News_Content.aspx?n=2991F84A4FAF842F&s=58A14F503DDDA3D7)

### 技術社群
- [Taiwan Python Community](https://tw.pycon.org/)
- [FastAPI Taiwan](https://www.facebook.com/groups/fastapi.taiwan/)
- [GitHub Discussions](https://github.com/thc1006/NYCU-Med-AI-Agent/discussions)

## 📞 聯絡資訊 (Contact)

### 開發團隊
- **專案維護者**: NYCU Medical AI Team
- **Email**: [聯絡信箱]
- **GitHub**: [thc1006](https://github.com/thc1006)

### 問題回報
- **Bug 回報**: [GitHub Issues](https://github.com/thc1006/NYCU-Med-AI-Agent/issues)
- **功能建議**: [GitHub Discussions](https://github.com/thc1006/NYCU-Med-AI-Agent/discussions)
- **安全問題**: 請直接聯絡維護團隊（不要公開回報）

### 商業合作
如需商業授權或客製化開發，請透過 Email 聯絡我們。

---

## 📄 授權條款 (License)

本專案採用 [MIT License](LICENSE) 授權。

```
MIT License

Copyright (c) 2024 NYCU Medical AI Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### 免責聲明 (Disclaimer)

**重要醫療免責聲明**:

本系統僅供一般健康資訊參考，不構成醫療診斷、治療建議或專業醫療意見。使用者在任何醫療決定前，應諮詢合格的醫療專業人士。

**緊急狀況處理**:
如遇緊急醫療狀況，請立即撥打：
- **119**: 消防救護專線
- **112**: 行動電話緊急號碼
- **110**: 警察報案專線

本系統不對使用者基於系統建議採取的任何行動負責。

---

<div align="center">

**🏥 為台灣醫療環境而生，以技術促進健康照護 🇹🇼**

Made with ❤️ by NYCU Medical AI Team

</div>
