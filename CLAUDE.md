# Claude Code Configuration - SPARC Development Environment

# CLAUDE.md（以「台灣在地化醫療助理」為目標的全端開發藍圖＋Claude Code 專用提示）

> 目標：以 **MediMind-AI-Agent** 的系統概念為參考，從零打造一個**台灣在地化**的醫療助理（症狀詢答＋就近醫療院所搜尋），**以 TDD 為核心流程**，並**以 Claude Code CLI** 驅動開發與自動化。原專案採 Google ADK 作多代理協作、整合 Google Places 與自動定位（以印度情境與 108 為急救號碼）([GitHub][1])。本藍圖將**全面台灣化**（語言、資料源、急救與合規）、**模組化**（LLM 介面可插拔）、**可測試**（單元／整合／E2E 都以測試先行）。

---

## 0) 架構與技術決策（最佳實務）

* **開發語言與框架**：Python 3.11 + **FastAPI**（輕量、異步、型別友善）＋ **httpx**（呼叫外部 API）＋ **pytest**（測試先行）([fastapi.tiangolo.com][2])
* **地點與院所查詢**：Google **Places API（New）Nearby Search** 與 **Geocoding API**，強制 `languageCode=zh-TW` 與 `regionCode=TW`（Places v1），Geocoding 使用 `language=zh-TW`（Web Service）以確保在地語系與地名正確性([Google for Developers][3])。
* **自動定位（可選）**：以 IP Geolocation（如 ipinfo、ipapi）推測使用者座標，再餵給 Places API。**注意 IP 推測具有誤差**，需在介面上標註可手動修正位置([IPinfo][4])。
* **台灣在地化**：

  * 急救與諮詢：**119**（消防／救護）、**110**（警政）、**112**（行動電話 GSM 國際緊急轉接，無卡亦可撥）、**113**（婦幼保護）、**165**（反詐騙諮詢）([Taipei City Government][5])。
  * 資料源：**MOHW／健保署**的醫事機構與統計開放資料（作為 Places 的權威比對與備援），例：**健保特約醫療院所名冊**與地圖查詢服務、醫療院所統計等([衛生福利部國民健康署][6])。
  * 隱私與法規：**個人資料保護法（PDPA）**，蒐集／處理／利用個資須符合法令與最小必要原則([法規資料庫][7])。
* **Claude Code CLI**：用於互動式改碼、執行測試、連接 MCP 工具；支援 `claude -p`（非互動印出）、`claude mcp`（管理 MCP 伺服器）等指令([Claude 文檔][8])。
* **測試方法**：pytest 單元與整合測試、**RESpx** 模擬 httpx 外呼（避免打爆第三方 API 與控成本），必要時以 pytest-httpx／VCR 方式封存回應([GitHub][9])。

---

## 1) 專案目錄建議

```
taiwan-med-agent/
├─ app/
│  ├─ main.py                 # FastAPI 入口
│  ├─ deps.py                 # DI / 設定注入
│  ├─ config.py               # 環境變數、常數（語系、急救號碼、風險等級）
│  ├─ domain/
│  │  ├─ models.py            # Pydantic 模型（SymptomQuery, Place, etc.）
│  │  ├─ rules_tw.py          # 台灣化醫療安全規則（緊急判斷、就醫建議級別）
│  │  ├─ triage.py            # 症狀粗分／風險分級（可插拔至 LLM）
│  ├─ services/
│  │  ├─ geocoding.py         # 位置處理（IP/地址→座標）
│  │  ├─ places.py            # Google Places Nearby Search（zh-TW/TW）
│  │  ├─ nhia_registry.py     # 健保院所名冊查核/比對（可選）
│  │  └─ llm.py               # LLM 抽象介面（plug-in: Anthropic/其他）
│  ├─ routers/
│  │  ├─ triage.py            # /v1/triage
│  │  ├─ hospitals.py         # /v1/hospitals/nearby
│  │  └─ healthinfo.py        # /v1/health-info（可選）
│  └─ middlewares/
│     └─ privacy.py           # 請求遮罩、PII 最小化、審計 log
├─ tests/
│  ├─ unit/...
│  ├─ integration/...
│  └─ e2e/...
├─ .env.example
├─ pyproject.toml / requirements.txt
└─ README.md / CLAUDE.md
```

---

## 2) 開發階段與子階段（**全面 TDD**；每一子階段都附上 **Claude Code 專用提示詞**）

> **原則**：**先寫測試，再實作**。所有測試 **不得 skip**；若測試失敗，**不得通過**該子階段。
> 參考：FastAPI 官方測試章節、pytest 文件（fixtures、參數化、標註），與 async 測試要點([fastapi.tiangolo.com][2])。

---

### 階段 A｜專案骨架與測試基礎

**A1. 專案初始化（空路由＋健康檢查）**

* 測試重點：`GET /healthz` 回 200 與 JSON `{status:"ok"}`；提供 `X-Request-Id`。
* Claude 提示：

  ```
  你現在是我的 TDD pair programmer。請在空白專案中建立 FastAPI 服務與 pytest 設定。
  先寫測試 tests/unit/test_healthz.py：
  - 對 GET /healthz 期望 200 與 {"status":"ok"}。
  - 驗證回應 header 含有 "X-Request-Id"。
  - 嚴禁使用 pytest.skip；不得存取外網。
  接著最小實作 app/main.py 通過測試，再補上 pyproject.toml 與 requirements.txt。
  使用 httpx TestClient/fastapi.testclient 完成測試。完成後執行 pytest 並貼出報告。
  ```

  > 參考：FastAPI 測試用 **TestClient**、pytest 入門([fastapi.tiangolo.com][2])。

**A2. 設定管理與環境變數**

* 測試重點：`.env` 讀入與預設值（例如 `GOOGLE_PLACES_API_KEY` 必填；`DEFAULT_LANG=zh-TW`）。
* Claude 提示：

  ```
  撰寫 tests/unit/test_config.py 驗證：
  - 缺少 GOOGLE_PLACES_API_KEY 時拋出明確例外。
  - 預設 DEFAULT_LANG=zh-TW, REGION=TW。
  - 測試可用 monkeypatch 設定環境變數。
  再實作 app/config.py 與 dotenv 載入。通過測試。
  ```

**A3. 中介層：隱私遮罩與審計 log（PDPA 最小化）**

* 測試重點：禁止把 symptom 字串原樣寫入 log；以 hash 或摘要；清除電話／身分證可能樣式。
* Claude 提示：

  ```
  先寫 tests/unit/test_privacy_mw.py：
  - 模擬含電話/身分字樣的 payload，確認中介層會遮罩敏感欄位。
  - 確認 access log 僅記載必要欄位（方法、路徑、status、耗時、request-id）。
  然後實作 middlewares/privacy.py 並掛載於 app/main.py；確保所有測試通過。
  ```

  > 法規參考：**PDPA**（蒐集、處理、利用個資須合法且相當必要）([法規資料庫][7])。

---

### 階段 B｜位置處理與在地化

**B1. IP → 座標（可關閉）**

* 測試重點：有網路時應以 **RESpx** 模擬 ipinfo/ipapi 回傳；誤差／缺值時回傳 None；可由客戶端覆寫座標。
* Claude 提示：

  ```
  以 RESpx 模擬 httpx 請求，撰寫 tests/unit/test_geocoding_ip.py：
  - 成功案例：返回台北市中心近似座標與城市名稱。
  - 失敗/逾時：回傳 None，不得 raise。
  - 加入 "使用者手動座標優先於IP" 的測試。
  再實作 services/geocoding.py 的 ip_geolocate()；不得直連真實 API。
  ```

  > 注意：IP 定位**不精確**，官方亦提示結果可能僅為大致區域([ipapi][10])。

**B2. 地址／地名 → 座標（Geocoding API）**

* 測試重點：`language=zh-TW`，模擬「臺北市信義區」等案例；不允許回傳空地址卻有座標。
* Claude 提示：

  ```
  用 RESpx 模擬 Google Geocoding，tests/unit/test_geocoding_addr.py：
  - 中文地址 zh-TW 取得正確座標與標準化地址。
  - 無效地址返回 404-like 錯誤模型（自定義）。
  然後實作 services/geocoding.py 的 geocode_address()；參數 language=zh-TW。
  ```

  > 參考：Geocoding API 語言參數說明([Google for Developers][11])。

**B3. 台灣急救與熱線常數**

* 測試重點：`config.EMERGENCY_NUMBERS` 必含 119/110/112/113/165 與描述；文件化於 `/v1/meta/emergency`。
* Claude 提示：

  ```
  撰寫 tests/unit/test_emergency_meta.py：
  - GET /v1/meta/emergency 回傳含 119/110/112/113/165 與中文描述。
  - 驗證 112 說明為「行動電話國際緊急號碼」。
  實作 routers/meta.py 與 config 常數。保持資料來源註解。
  ```

  > 資訊來源：台北市政府英文網頁、NCC 公告（112 可無卡撥打）等([Taipei City Government][5])。

---

### 階段 C｜就近醫療院所搜尋（Places v1）

**C1. Nearby Search（醫院/急診）**

* 測試重點：呼叫 **Places Nearby Search（New）**，`includedTypes` 至少含 **hospital**，`locationRestriction` 為使用者座標與半徑；強制 `languageCode=zh-TW`、`regionCode=TW`；回傳欄位（名稱、地址、電話、是否急診、rating、營業時間）格式化；以 RESpx 模擬。
* Claude 提示：

  ```
  撰寫 tests/integration/test_places_nearby.py（RESpx 模擬）：
  - 查詢半徑 3km，type=hospital，languageCode=zh-TW, regionCode=TW。
  - 回傳已排序（距離/評分），每筆含 name, address, tel(可缺), rating(可缺), openingHours(可缺)。
  - 錯誤路徑：API-KEY 無效 / 配額用盡 → 對應 401/429 錯誤模型。
  然後實作 services/places.py 的 nearby_hospitals()；不得使用舊版 rankby 參數。
  ```

  > 參考：**Nearby Search（New）** 的 `locationRestriction`、`languageCode`/`regionCode`；Place Types 說明（hospital 屬健康與醫療類型 / legacy 亦有 hospital 類型）([Google for Developers][3])。

**C2. 健保名冊比對（可選強化信任）**

* 測試重點：若院所名稱或地址能在 **健保特約醫療院所名冊**查得，回傳 `is_contracted=True` 與機構代碼；比對失敗不致命。
* Claude 提示：

  ```
  撰寫 tests/integration/test_nhia_registry.py（以本地fixture CSV/JSON 模擬名冊）：
  - 名稱/地址正規化比對（移除全形/半形差異、里/路等常見變體）。
  - 命中者加註 is_contracted 與機構代碼。
  實作 services/nhia_registry.py 的 match_from_registry()，並在 places.py 聚合。
  ```

  > 資料脈絡：健保署開放資料平臺（特約院所名冊）與地圖查詢服務([衛生福利部國民健康署][6])。

**C3. API 路由：`/v1/hospitals/nearby`**

* 測試重點：整合 geocoding（IP/地址）→ places →（可選）健保名冊；錯誤時傳回清晰錯誤碼與建議。
* Claude 提示：

  ```
  撰寫 tests/e2e/test_hospitals_api.py（使用 TestClient）：
  - 帶入 {lat,lng} 直查。
  - 帶入 address 需先 geocode。
  - 帶入 none 時，若啟用 IP 定位則採用；否則 400。
  - 回傳結構包含 emergencyNumbers 與語系 zh-TW。
  實作 routers/hospitals.py；完成後跑 pytest 全綠。
  ```

---

### 階段 D｜症狀詢答與風險分級（可插拔 LLM）

**D1. 規則化初版（無 LLM）**

* 測試重點：對 **胸痛、呼吸困難、麻痺、劇烈頭痛**等關鍵詞，**必須**立即建議「撥打 119／就近急診」；一般輕症給自我照護建議＋何時就醫。
* Claude 提示：

  ```
  先寫 tests/unit/test_triage_rules.py：
  - 關鍵症狀命中 → level="emergency" 並回傳 119 指引與就近急診提示。
  - 輕症（喉嚨痛、流鼻水） → level="self-care"，提供觀察期與若加劇之指引。
  - 注入台灣急救/就醫資訊，輸出繁中。
  然後實作 domain/rules_tw.py 與 domain/triage.py 的 rule_triage()。
  ```

**D2. LLM 介面抽象與實作（可接 Anthropic）**

* 測試重點：以假物件（stub/mock）模擬 LLM 回覆；除非標示 `level="emergency"`，否則不得返回絕對診斷語句；所有輸出**必須**附上免責聲明與 119 提醒。
* Claude 提示：

  ```
  撰寫 tests/unit/test_llm_adapter.py：
  - ILLMProvider 抽象介面；MockLLM 回傳可控 JSON。
  - triage.combine(rule_triage + llm_enrichment) 時，若兩者衝突，以 emergency 優先。
  - 產生繁中回覆，落款附醫療免責與119指引。
  實作 services/llm.py：定義 ILLMProvider 與 AnthropicProvider（僅接口，不連網）。
  ```

**D3. API 路由：`/v1/triage`**

* 測試重點：輸入症狀字串→回傳 `level`、`advice`、`next_steps`、`disclaimer`、`emergencyNumbers`。
* Claude 提示：

  ```
  寫 tests/e2e/test_triage_api.py：
  - 危急關鍵詞 → level emergency + 119/急診連結提示。
  - 一般症狀 → level self-care/outpatient + 就醫建議。
  - 所有輸出為繁中、不得包含醫療確診語句。
  然後實作 routers/triage.py，整合 rule 與（可選）LLM 介面。
  ```

---

### 階段 E｜在地健康資訊（可選）

**E1. 健康教育與官方連結整理**

* 測試重點：提供固定的 MOHW／健保署官方資訊連結（例如就醫統計報告、健保制度說明），以繁中回應。
* Claude 提示：

  ```
  撰寫 tests/unit/test_healthinfo_static.py：
  - /v1/health-info/topics 回固定清單（如就醫流程、健保查詢、急診就醫指引）。
  - 每一主題包含 title、summary、url（政府或機關站）。
  然後實作 routers/healthinfo.py（使用本地 YAML/JSON 作資料源）。
  ```

  > 來源示例：醫療院所統計、NHI/健保資源、MOHW 入口([衛生福利部][12])。

---

### 階段 F｜運維、安全與治理

**F1. 速率與失效保護**

* 測試重點：Places/Geocoding 之 429/5xx 回應要有退避（exponential backoff）與替代路徑（例如只回規則建議、不包含地圖結果）。
* Claude 提示：

  ```
  撰寫 tests/integration/test_rate_limit_and_fallbacks.py：
  - 模擬 Places 回 429，預期 API 回 200 但 results=[] 並提示稍後再試。
  - 模擬 Geocoding 逾時，預期直接返回 400 "無法辨識位置"。
  然後實作 retry & backoff（十進位秒數上限），確保測試通過。
  ```

**F2. 記錄與稽核**

* 測試重點：保留**最小化**的行為稽核（時間、路徑、結果級別），不可保存症狀原文與個資。
* Claude 提示：

  ```
  撰寫 tests/unit/test_audit_log.py：
  - 確保 log 僅含必要欄位；不包含 symptom 原文/電話/身分字段。
  - 提供可設定的保存天期（預設7天，測試用1秒）。
  完成後調整 privacy 中介層確保一致。
  ```

---

## 3) Claude Code CLI 操作建議（含 MCP）

* **互動模式**：`claude` 直接進 REPL；或以 `claude -p "指令"` 非互動印出。
* **常用旗標**：`--model sonnet` 選模型；`--verbose` 偵錯；`--max-turns 3` 限制代理迴圈；`--allowedTools "Read" "Write" "Edit" "Bash(pytest:*)"` 允許工具；`claude --continue` 延續最近會話([Claude 文檔][8])。
* **MCP 伺服器**：若未來要把「健保名冊查詢」或「院所登記比對」抽成工具，可自建 HTTP/stdio MCP 伺服器，並以
  `claude mcp add --transport http nhia https://<your-mcp>/mcp` 加入；可用 `claude mcp list/get/remove` 管理([Claude 文檔][13])。
* **在專案根目錄進行**：讓 Claude Code 直接看見檔案樹並以 /mcp 或 /tests 指令配合。
* **配套工作流**（範例）：

  * 撰寫測試 → `claude -p "請幫我依 TDD 補上最小實作與重構計畫"`
  * 跑測試：`pytest -q` 或 `claude -p "執行 pytest 並解析失敗，僅回傳修復建議與修補 patch"`（印出模式）。
  * 嚴禁 `@pytest.mark.skip`、嚴禁將外部 API 寫死於測試。

**Claude 專用提示（通用模板）**：

```
你是負責此專案的資深軟體工程師，遵循 TDD、Clean Code 與 PDPA。
限制：
- 所有測試不得 skip；不得連線真實外部 API。
- 嚴格使用 zh-TW / region TW 的在地化設定；不得輸出簡體中文。
- 所有醫療建議均需附上免責聲明與 119/112 指引。
請依下列測試檔與需求，先補齊測試，再產出最小實作與必要重構，最後給出完整 patch（統一 diff）。
```

---

## 4) API 契約（草案）

* `GET /healthz` → `{status:"ok"}`
* `GET /v1/meta/emergency` → `{numbers:[{code:"119",desc:"…"},…], updatedAt:"…"}`（繁中）
* `GET /v1/hospitals/nearby?lat&lng&radius=3000`（可選 `address`、`use_ip=true`）
  回傳：

  ```json
  {
    "results":[
      {
        "name":"臺大醫院",
        "address":"…",
        "tel":"+886-2-…",
        "rating":4.5,
        "openingHours":"24 小時",
        "is_contracted": true,
        "distance_m": 820
      }
    ],
    "emergencyNumbers":["119","112"],
    "locale":"zh-TW"
  }
  ```
* `POST /v1/triage`（body: `{ "symptomText":"胸痛冒冷汗" }`）
  回傳（例）：

  ```json
  {
    "level":"emergency",
    "advice":"您描述胸痛與出冷汗屬高度警訊，請立即撥打 119 / 前往就近急診。",
    "next_steps":["保持通話暢通","準備藥歷與病史"],
    "disclaimer":"本系統僅供一般資訊，非醫療診斷。緊急狀況請撥打 119 或 112。"
  }
  ```

---

## 5) 外部服務設定與在地化細節

* **Google Places Nearby（New）**：使用 `includedTypes=["hospital"]`、`locationRestriction`（circle.center + radius），`languageCode="zh-TW"`、`regionCode="TW"`，避免使用舊版 `rankby`；輸出以繁中為主([Google for Developers][3])。
* **Place Types**：醫院型別 `hospital` 可用；（Legacy 列表也收錄 hospital，供對照）。
* **Geocoding**：`language=zh-TW`；地址正規化輸出（避免簡繁混用）([Google for Developers][11])。
* **自動定位**：IP 推測結果需明示「粗略位置」並允許手動覆寫；官方文檔亦說明精度限制([ipapi][10])。
* **急救資訊**：以政府或機關網頁為準（119/110/112/113/165）([Taipei City Government][5])。
* **合規**：遵循 **PDPA**（目的特定化、最小必要、使用者權利）；API 與日誌不可存個資與症狀原文（已遮罩）([法規資料庫][7])。

---

## 6) 風險與緩解

* **外部 API 配額／失敗**：以 RESpx 模擬並設計回退（回傳規則建議＋提示稍後再試），防止單點失敗([GitHub][9])。
* **地理誤差**：IP 位置不精確→產品層面要求地址或地標再確認([ipapi][10])。
* **醫療責任**：所有輸出加註免責；碰觸危急詞彙一律引導 119／急診。
* **在地資料一致性**：以健保名冊做二次比對增加權威性（非必須但建議）([衛生福利部國民健康署][6])。

---

## 7) 「從零起步」的實際命令清單（建議次序）

1. **建立虛擬環境與依賴**

   ```
   uv venv && source .venv/bin/activate   # 或 pyenv/pipenv
   pip install fastapi "uvicorn[standard]" httpx pydantic python-dotenv pytest respx
   ```
2. **啟動 Claude Code（專案根目錄）**

   * `claude` 進入互動模式，或 `claude -p "建立 healthz 測試與最小實作"`（印出模式）([Claude 文檔][8])。
3. **逐子階段 TDD**：依本文「階段 A→F」之**每個提示詞**逐一執行。
4. **本地啟動**：`uvicorn app.main:app --reload`。
5. **執行全部測試**：`pytest -q`。
6. **（可選）新增 MCP**：若你將健保名冊查核做成 MCP 工具，則 `claude mcp add --transport http nhia https://<your-mcp>/mcp`；用 `claude mcp list/get/remove` 管理([Claude 文檔][13])。

---

## 8) 範例測試樣板（僅示意）

**tests/unit/test\_healthz.py**

```python
from fastapi.testclient import TestClient
from app.main import app

def test_healthz_ok():
    c = TestClient(app)
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status":"ok"}
    assert "X-Request-Id" in r.headers
```

> `TestClient` 用法見官方教學；pytest 基本語法與斷言見官方文件([fastapi.tiangolo.com][2])。

**tests/integration/test\_places\_nearby.py**（RESpx 範例）

```python
import httpx, respx
from app.services.places import nearby_hospitals

@respx.mock
def test_nearby_hospitals_basic():
    respx.post("https://places.googleapis.com/v1/places:searchNearby").mock(
        return_value=httpx.Response(200, json={
            "places":[{"displayName":{"text":"某醫院"},
                       "formattedAddress":"台北市…",
                       "internationalPhoneNumber":"+886-2-…",
                       "rating":4.2,
                       "currentOpeningHours":{"openNow": True},
                       "location":{"latitude":25.0339,"longitude":121.5645}}]
        })
    )
    results = nearby_hospitals(lat=25.04, lng=121.56, radius=3000)
    assert results[0]["name"] == "某醫院"
```

> RESpx 用法（mock httpx）([lundberg.github.io][14])。

---

## 9) 與原專案的對照與學習重點

* **多代理協調**：原專案以協調器代理分流到「症狀分析」與「醫院搜尋」兩子代理，並整合緊急引導與醫療資訊檢索；這種**路由型代理架構**值得沿用（我方以 routers + services 呈現）([GitHub][1])。
* **自動定位＋Places 整合**：核心價值在「**零摩擦**取得就近醫院資訊」；台灣版以 zh-TW/TW 參數與健保名冊比對提升可靠性([Google for Developers][3])。
* **安全優先**：原專案有「緊急情境優先、專業醫療為主」的取向；台灣版在訊息與 UI 中強化 **119/112** 指引與免責聲明，並遵循 **PDPA** 的最小化原則([GitHub][1])。
* **可部署性**：原專案提供 Vertex AI 部署腳本；我方先完成 API 與測試，再決定是否接入企業級 LLM／部署環境（例如以 Claude API 取代，或保持規則＋查詢）([GitHub][1])。

---

## 10) 後續延伸（Roadmap）

1. **LLM 上線（可控）**：將 `services/llm.py` 的介面接上 Anthropic（或企業閘道），**輸出嚴控樣式**（不得診斷、必附免責） 。
2. **RAG 健康知識**：將 MOHW／健保署常見問答整理成內建 KB（markdown/YAML），避免網路波動。
3. **E2E 測試**：以 Playwright（Pytest plugin）針對 Web 介面做端到端測試（若未來加 Web 前端）([playwright.dev][15])。
4. **資料品質**：持續更新健保名冊本地快取（排程）；比對異動。
5. **可用性**：增加手動地圖選點與位置微調，減少 IP 誤差影響([ipapi][10])。

---

### 重要參考（節選）

* **MediMind-AI-Agent** 專案說明（多代理、印度情境、Places 整合）([GitHub][1])
* **Claude Code CLI** 指令與 **MCP** 連線方式（`claude -p`, `claude mcp add` 等）([Claude 文檔][8])
* **Google Places（New）Nearby Search** 語言／區域與查詢參數；**Place Types** 說明；**Geocoding** 語系參數([Google for Developers][3])
* **FastAPI 測試**、**pytest** 文件；**RESpx**（httpx 模擬）([fastapi.tiangolo.com][2])
* **台灣急救與熱線**（119/110/112/113/165）與 **NCC** 緊急撥號說明([Taipei City Government][5])
* **PDPA** 法規（英譯／說明）([法規資料庫][7])

---

## 一句話總結

依本 **CLAUDE.md** 的階段化 TDD 指南與 Claude Code 專用提示，你可以**從零**建立一個**台灣在地化**、**可測試**、**可維運**的醫療助理：以 **Places+Geocoding（zh-TW/TW）** 提供就近院所、以**規則＋（可選）LLM** 強化症狀分級、以 **PDPA** 守則與**急救指引**確保安全與合規。

[1]: https://github.com/krupagaliya/MediMind-AI-Agent "GitHub - krupagaliya/MediMind-AI-Agent: A specialized healthcare assistant system built using Google's Agent Development Kit (ADK) framework featuring intelligent symptom analysis and hospital location services for India."
[2]: https://fastapi.tiangolo.com/tutorial/testing/?utm_source=chatgpt.com "Testing"
[3]: https://developers.google.com/maps/documentation/places/web-service/nearby-search "Nearby Search (New)  |  Places API  |  Google for Developers"
[4]: https://ipinfo.io/developers/?utm_source=chatgpt.com "Developer Resource - IPinfo.io"
[5]: https://english.gov.taipei/News_Content.aspx?n=2991F84A4FAF842F&s=58A14F503DDDA3D7&utm_source=chatgpt.com "Emergency Telephone Numbers"
[6]: https://info.nhi.gov.tw/IODE0000/IODE0000S09?id=1120&utm_source=chatgpt.com "健保特約醫療院所名冊"
[7]: https://law.moj.gov.tw/eng/LawClass/LawAll.aspx?PCode=I0050021&utm_source=chatgpt.com "Personal Data Protection Act - 全國法規資料庫"
[8]: https://docs.anthropic.com/en/docs/claude-code/cli-reference "CLI reference - Claude Docs"
[9]: https://github.com/lundberg/respx?utm_source=chatgpt.com "lundberg/respx: Mock HTTPX with awesome request ..."
[10]: https://ipapi.co/developers/?utm_source=chatgpt.com "ipapi | Developer - Tools, Docs and Reference"
[11]: https://developers.google.com/maps/documentation/places/web-service/place-types "Place Types (New)  |  Places API  |  Google for Developers"
[12]: https://www.mohw.gov.tw/cp-7155-79484-2.html?utm_source=chatgpt.com "Statistics of Medical Care Institution & Hospital Utilization ..."
[13]: https://docs.anthropic.com/en/docs/claude-code/mcp "Connect Claude Code to tools via MCP - Claude Docs"
[14]: https://lundberg.github.io/respx/versions/0.14.0/mocking/?utm_source=chatgpt.com "Mock HTTPX - RESPX"
[15]: https://playwright.dev/python/docs/test-runners?utm_source=chatgpt.com "Pytest Plugin Reference | Playwright Python"

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases

1. **Specification** - Requirements analysis (`sparc run spec-pseudocode`)
2. **Pseudocode** - Algorithm design (`sparc run spec-pseudocode`)
3. **Architecture** - System design (`sparc run architect`)
4. **Refinement** - TDD implementation (`sparc tdd`)
5. **Completion** - Integration (`sparc run integration`)

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Available Agents (54 Total)

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`, `collective-intelligence-coordinator`, `swarm-memory-manager`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`, `consensus-builder`, `crdt-synchronizer`, `quorum-manager`, `security-manager`

### Performance & Optimization
`perf-analyzer`, `performance-benchmarker`, `task-orchestrator`, `memory-coordinator`, `smart-agent`

### GitHub & Repository
`github-modes`, `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`, `workflow-automation`, `project-board-sync`, `repo-architect`, `multi-repo-swarm`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`

### Specialized Development
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `api-docs`, `system-architect`, `code-analyzer`, `base-template-generator`

### Testing & Validation
`tdd-london-swarm`, `production-validator`

### Migration & Planning
`migration-planner`, `swarm-init`

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION:
- **Task tool**: Spawn and run agents concurrently for actual work
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

## 🚀 Quick Setup

```bash
# Add MCP servers (Claude Flow required, others optional)
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm mcp start  # Optional: Enhanced coordination
claude mcp add flow-nexus npx flow-nexus@latest mcp start  # Optional: Cloud features
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

### Flow-Nexus MCP Tools (Optional Advanced Features)
Flow-Nexus extends MCP capabilities with 70+ cloud-based orchestration tools:

**Key MCP Tool Categories:**
- **Swarm & Agents**: `swarm_init`, `swarm_scale`, `agent_spawn`, `task_orchestrate`
- **Sandboxes**: `sandbox_create`, `sandbox_execute`, `sandbox_upload` (cloud execution)
- **Templates**: `template_list`, `template_deploy` (pre-built project templates)
- **Neural AI**: `neural_train`, `neural_patterns`, `seraphina_chat` (AI assistant)
- **GitHub**: `github_repo_analyze`, `github_pr_manage` (repository management)
- **Real-time**: `execution_stream_subscribe`, `realtime_subscribe` (live monitoring)
- **Storage**: `storage_upload`, `storage_list` (cloud file management)

**Authentication Required:**
- Register: `mcp__flow-nexus__user_register` or `npx flow-nexus@latest register`
- Login: `mcp__flow-nexus__user_login` or `npx flow-nexus@latest login`
- Access 70+ specialized MCP tools for advanced orchestration

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development:

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with Express. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design PostgreSQL schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")
  
  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }
  
  // All file operations together
  Write "backend/server.js"
  Write "frontend/App.jsx"
  Write "database/schema.sql"
```

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST:

**1️⃣ BEFORE Work:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**2️⃣ DURING Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

**3️⃣ AFTER Work:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Multiple Messages):
```javascript
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("agent 1")
Message 3: TodoWrite { todos: [single todo] }
Message 4: Write "file.js"
// This breaks parallel coordination!
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## Hooks Integration

### Pre-Operation
- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation
- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management
- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Flow-Nexus Platform: https://flow-nexus.ruv.io (registration required for cloud features)

---

Remember: **Claude Flow coordinates, Claude Code creates!**

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Never save working files, text/mds and tests to the root folder.