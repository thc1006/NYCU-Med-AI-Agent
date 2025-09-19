# 台灣醫療 AI 助理使用方法指南

> **免責聲明：本系統僅供一般健康資訊參考，不取代專業醫療診斷與治療。緊急狀況請立即撥打 119 或 112。**

## 目錄

1. [系統概述](#系統概述)
2. [用戶指南](#用戶指南)
3. [API 使用範例](#api-使用範例)
4. [常見使用場景](#常見使用場景)
5. [整合指南](#整合指南)
6. [最佳實踐](#最佳實踐)
7. [故障排除](#故障排除)
8. [安全與隱私](#安全與隱私)

---

## 系統概述

台灣醫療 AI 助理是一個專為台灣醫療環境設計的智慧型醫療助理系統，提供以下核心功能：

### 🩺 核心功能
- **症狀評估與分級**：智慧分析症狀嚴重程度，提供就醫建議
- **就近醫院搜尋**：基於位置的醫療院所搜尋與導航
- **緊急狀況辨識**：自動識別危險症狀，提供急救指引
- **健康資訊查詢**：提供衛福部認證的健康教育資訊

### 🛡️ 安全特性
- **PDPA 合規**：符合個人資料保護法規範
- **隱私保護**：敏感資訊自動遮罩與最小化處理
- **台灣在地化**：使用繁體中文與台灣緊急聯絡方式

### 📊 監控功能
- **即時健康監控**：API 服務狀態與效能監控
- **結構化日誌**：完整的操作審計追蹤
- **效能分析**：回應時間與系統資源使用分析

---

## 用戶指南

### 👩‍⚕️ 醫療從業人員

醫護人員可以利用系統進行：

#### 快速症狀分流
- 輔助病患初步分級
- 緊急狀況快速識別
- 轉診建議參考

#### 使用範例
```bash
# 查看服務狀態
curl http://localhost:8000/v1/monitoring/health

# 快速症狀評估
curl -X POST http://localhost:8000/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_text": "胸痛並伴隨呼吸困難",
    "age": 45,
    "gender": "M"
  }'
```

### 💻 軟體開發者

開發者可以整合系統 API 至現有應用程式：

#### 基本整合步驟
1. **環境設定**
2. **API 金鑰配置**
3. **端點測試**
4. **錯誤處理實作**

#### 開發工具
- **API 文件**：`http://localhost:8000/docs`
- **監控儀表板**：`http://localhost:8000/v1/monitoring/dashboard`
- **健康檢查**：`http://localhost:8000/healthz`

### 🔧 系統管理員

管理員負責系統部署、監控與維護：

#### 部署檢查清單
- [ ] 環境變數配置
- [ ] Google API 金鑰設定
- [ ] 資料庫連線測試
- [ ] 防火牆規則配置
- [ ] SSL 憑證安裝
- [ ] 日誌輪轉設定

#### 監控重點
```bash
# 系統健康檢查
curl http://localhost:8000/v1/monitoring/health

# 效能度量查詢
curl http://localhost:8000/v1/monitoring/metrics

# 日誌分析
tail -f logs/app.log | grep ERROR
```

### 👨‍👩‍👧‍👦 一般民眾

透過前端應用程式或行動 APP 使用：

#### 主要功能
1. **症狀自我評估**
2. **就近醫院搜尋**
3. **緊急聯絡資訊**
4. **健康教育資源**

---

## API 使用範例

### 🏥 醫院搜尋 API

#### 基本搜尋（使用座標）
```bash
curl -X GET "http://localhost:8000/v1/hospitals/nearby?latitude=25.0330&longitude=121.5654&radius=3000" \
  -H "Accept: application/json"
```

**回應範例：**
```json
{
  "results": [
    {
      "name": "臺大醫院",
      "address": "台北市中正區常德街1號",
      "tel": "+886-2-23123456",
      "rating": 4.5,
      "opening_hours": "24 小時急診",
      "is_contracted": true,
      "distance_m": 820,
      "place_id": "ChIJXx1234...",
      "location": {
        "lat": 25.0330,
        "lng": 121.5654
      }
    }
  ],
  "emergency_numbers": ["119", "112"],
  "locale": "zh-TW",
  "request_id": "req_12345678"
}
```

#### 地址搜尋
```bash
curl -X GET "http://localhost:8000/v1/hospitals/nearby?address=台北市信義區&radius=5000" \
  -H "Accept: application/json"
```

#### Python 範例
```python
import requests
import json

# 醫院搜尋
def search_nearby_hospitals(latitude, longitude, radius=3000):
    url = "http://localhost:8000/v1/hospitals/nearby"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "radius": radius,
        "max_results": 10
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"搜尋醫院時發生錯誤: {e}")
        return None

# 使用範例
hospitals = search_nearby_hospitals(25.0330, 121.5654)
if hospitals:
    for hospital in hospitals['results']:
        print(f"醫院：{hospital['name']}")
        print(f"地址：{hospital['address']}")
        print(f"距離：{hospital['distance_m']} 公尺")
        print("---")
```

### 🩺 症狀分級 API

#### 基本症狀評估
```bash
curl -X POST http://localhost:8000/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_text": "頭痛已持續三天，伴隨發燒",
    "age": 35,
    "gender": "F",
    "duration_hours": 72,
    "has_chronic_disease": false
  }'
```

**回應範例：**
```json
{
  "level": "outpatient",
  "advice": "建議安排門診就醫檢查，持續發燒超過三天需要專業評估。",
  "next_steps": [
    "測量並記錄體溫變化",
    "充分休息與補充水分",
    "避免服用過量退燒藥",
    "如症狀惡化請立即就醫"
  ],
  "urgency_score": 6,
  "reasoning": "持續發燒合併頭痛需要排除感染或其他疾病",
  "disclaimer": "本評估僅供參考，不取代醫師診斷。如有疑慮請諮詢醫療專業人員。",
  "emergency_numbers": {
    "119": "消防救護車",
    "112": "行動電話緊急求救",
    "110": "警察局"
  },
  "request_id": "req_87654321"
}
```

#### 緊急症狀評估
```bash
curl -X POST http://localhost:8000/v1/triage \
  -H "Content-Type: application/json" \
  -d '{
    "symptom_text": "胸痛、呼吸困難、冒冷汗",
    "age": 55,
    "gender": "M"
  }'
```

**緊急狀況回應：**
```json
{
  "level": "emergency",
  "advice": "⚠️ 立即撥打 119 或前往最近急診室！這些症狀可能表示心臟疾病或其他嚴重狀況。",
  "next_steps": [
    "立即撥打 119 求救",
    "保持鎮靜，勿劇烈活動",
    "準備病歷與藥物清單",
    "通知家屬或緊急聯絡人"
  ],
  "urgency_score": 10,
  "reasoning": "胸痛合併呼吸困難和冒汗是心臟病發作的典型症狀",
  "disclaimer": "⚠️ 緊急狀況！請立即尋求專業醫療協助。",
  "emergency_numbers": {
    "119": "消防救護車 - 立即撥打",
    "112": "行動電話緊急求救"
  },
  "nearest_hospitals": [
    {
      "name": "台北榮總急診",
      "distance_m": 1200,
      "tel": "+886-2-28712121"
    }
  ]
}
```

#### Python 範例
```python
import requests

def assess_symptoms(symptom_text, age=None, gender=None):
    """症狀評估函數"""
    url = "http://localhost:8000/v1/triage"
    payload = {
        "symptom_text": symptom_text,
        "age": age,
        "gender": gender
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

        # 處理回應
        print(f"分級等級：{result['level']}")
        print(f"建議：{result['advice']}")

        if result['level'] == 'emergency':
            print("⚠️ 緊急狀況！請立即就醫！")

        return result

    except requests.exceptions.RequestException as e:
        print(f"評估症狀時發生錯誤: {e}")
        return None

# 使用範例
result = assess_symptoms("頭痛發燒", age=30, gender="F")
```

### 📊 監控 API

#### 系統健康檢查
```bash
curl http://localhost:8000/v1/monitoring/health
```

#### 效能度量
```bash
curl http://localhost:8000/v1/monitoring/metrics
```

#### 儀表板資料
```bash
curl http://localhost:8000/v1/monitoring/dashboard
```

### 🌐 元資料 API

#### 緊急聯絡資訊
```bash
curl http://localhost:8000/v1/meta/emergency
```

**回應範例：**
```json
{
  "numbers": [
    {
      "code": "119",
      "name": "消防救護車",
      "description": "火災、救護、救助服務"
    },
    {
      "code": "112",
      "name": "國際緊急求救",
      "description": "行動電話緊急求救，無卡亦可撥打"
    },
    {
      "code": "110",
      "name": "警察局",
      "description": "刑事案件、交通事故報案"
    }
  ],
  "updated_at": "2024-09-19T12:00:00Z"
}
```

---

## 常見使用場景

### 🚨 場景一：急診分流

**情境**：醫院急診科需要快速評估病患急迫性

```python
# 急診分流系統整合
class EmergencyTriage:
    def __init__(self, api_base_url):
        self.api_url = api_base_url

    async def quick_assessment(self, patient_data):
        """快速評估病患狀況"""
        symptoms = patient_data.get('chief_complaint', '')
        age = patient_data.get('age')

        # 呼叫症狀評估 API
        response = await self.assess_symptoms(symptoms, age)

        if response['level'] == 'emergency':
            # 立即分配至急救區
            await self.assign_to_emergency_bay(patient_data)
        elif response['level'] == 'urgent':
            # 優先處理隊列
            await self.add_to_priority_queue(patient_data)
        else:
            # 一般候診
            await self.add_to_regular_queue(patient_data)

        return response
```

### 🏥 場景二：遠端醫療諮詢

**情境**：遠端醫療平台需要初步症狀篩檢

```javascript
// 遠端醫療前端整合
class TelemedicineConsult {
    constructor(apiEndpoint) {
        this.apiEndpoint = apiEndpoint;
    }

    async consultPatient(patientInput) {
        // 症狀評估
        const assessment = await this.assessSymptoms(patientInput);

        // 根據評估結果決定後續動作
        if (assessment.level === 'emergency') {
            return this.handleEmergency(assessment);
        } else if (assessment.level === 'urgent') {
            return this.scheduleUrgentConsult(assessment);
        } else {
            return this.provideGeneralAdvice(assessment);
        }
    }

    handleEmergency(assessment) {
        return {
            message: '建議您立即前往急診室或撥打119',
            nearbyHospitals: assessment.nearest_hospitals,
            immediateAction: true
        };
    }
}
```

### 📱 場景三：健康管理 APP

**情境**：個人健康管理應用程式的症狀記錄功能

```python
# 健康日記應用程式
class HealthDiary:
    def __init__(self):
        self.api_client = MedicalAIClient()

    def log_symptoms(self, user_id, symptom_description):
        """記錄症狀並獲得建議"""

        # 取得使用者基本資料
        user_profile = self.get_user_profile(user_id)

        # 症狀評估
        assessment = self.api_client.assess_symptoms(
            symptom_text=symptom_description,
            age=user_profile.age,
            gender=user_profile.gender,
            has_chronic_disease=user_profile.has_chronic_conditions
        )

        # 儲存記錄
        symptom_record = {
            'user_id': user_id,
            'timestamp': datetime.now(),
            'symptoms': symptom_description,
            'assessment': assessment,
            'action_taken': None
        }

        self.save_symptom_record(symptom_record)

        # 發送通知
        if assessment['level'] in ['emergency', 'urgent']:
            self.send_alert_notification(user_id, assessment)

        return assessment
```

### 🏢 場景四：企業健康管理

**情境**：公司健康管理系統的員工健康監控

```python
# 企業健康管理系統
class CorporateHealthSystem:
    def __init__(self, company_id):
        self.company_id = company_id
        self.medical_ai = MedicalAIClient()

    def employee_health_check(self, employee_id, health_report):
        """員工健康狀況檢查"""

        # 分析健康報告
        symptoms = self.extract_symptoms(health_report)

        if symptoms:
            assessment = self.medical_ai.assess_symptoms(
                symptom_text=symptoms,
                age=self.get_employee_age(employee_id)
            )

            # 根據評估結果採取行動
            if assessment['level'] == 'emergency':
                self.trigger_emergency_protocol(employee_id)
            elif assessment['level'] == 'urgent':
                self.recommend_medical_leave(employee_id)

            # 記錄到健康管理系統
            self.log_health_assessment(employee_id, assessment)

            return assessment

        return None
```

---

## 整合指南

### 🔧 技術整合

#### REST API 整合
```python
# API 客戶端封裝
import requests
from typing import Optional, Dict, Any

class TaiwanMedicalAIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # 設定 headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaiwanMedicalAI-Client/1.0'
        })

        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'

    def assess_symptoms(self, symptom_text: str, **kwargs) -> Dict[str, Any]:
        """症狀評估"""
        url = f"{self.base_url}/v1/triage"
        payload = {
            'symptom_text': symptom_text,
            **kwargs
        }

        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    def find_nearby_hospitals(self, latitude: float, longitude: float,
                            radius: int = 3000) -> Dict[str, Any]:
        """搜尋附近醫院"""
        url = f"{self.base_url}/v1/hospitals/nearby"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'radius': radius
        }

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def get_health_info(self, topic: str) -> Dict[str, Any]:
        """取得健康資訊"""
        url = f"{self.base_url}/v1/health-info/topics"
        params = {'topic': topic}

        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
```

#### 非同步整合
```python
import asyncio
import aiohttp
from typing import Optional, Dict, Any

class AsyncTaiwanMedicalAIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def assess_symptoms_async(self, symptom_text: str, **kwargs) -> Dict[str, Any]:
        """非同步症狀評估"""
        url = f"{self.base_url}/v1/triage"
        payload = {
            'symptom_text': symptom_text,
            **kwargs
        }

        async with self.session.post(url, json=payload) as response:
            response.raise_for_status()
            return await response.json()

# 使用範例
async def main():
    async with AsyncTaiwanMedicalAIClient('http://localhost:8000') as client:
        result = await client.assess_symptoms_async('頭痛發燒')
        print(result)

# 執行
asyncio.run(main())
```

### 🌐 前端整合

#### JavaScript/TypeScript
```typescript
// TypeScript 介面定義
interface SymptomAssessmentRequest {
    symptom_text: string;
    age?: number;
    gender?: 'M' | 'F' | 'O';
    duration_hours?: number;
    has_chronic_disease?: boolean;
    medications?: string[];
}

interface TriageResponse {
    level: 'emergency' | 'urgent' | 'outpatient' | 'self-care';
    advice: string;
    next_steps: string[];
    urgency_score: number;
    reasoning: string;
    disclaimer: string;
    emergency_numbers: Record<string, string>;
    request_id: string;
}

class TaiwanMedicalAPI {
    private baseUrl: string;

    constructor(baseUrl: string = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }

    async assessSymptoms(request: SymptomAssessmentRequest): Promise<TriageResponse> {
        const response = await fetch(`${this.baseUrl}/v1/triage`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }

    async findNearbyHospitals(lat: number, lng: number, radius: number = 3000) {
        const params = new URLSearchParams({
            latitude: lat.toString(),
            longitude: lng.toString(),
            radius: radius.toString()
        });

        const response = await fetch(`${this.baseUrl}/v1/hospitals/nearby?${params}`);

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} ${response.statusText}`);
        }

        return await response.json();
    }
}
```

#### React Hook 範例
```jsx
import { useState, useCallback } from 'react';
import { TaiwanMedicalAPI } from './api/TaiwanMedicalAPI';

// 自定義 Hook
export const useMedicalAssessment = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [result, setResult] = useState(null);

    const api = new TaiwanMedicalAPI();

    const assessSymptoms = useCallback(async (symptomData) => {
        setLoading(true);
        setError(null);

        try {
            const response = await api.assessSymptoms(symptomData);
            setResult(response);
            return response;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        assessSymptoms,
        loading,
        error,
        result
    };
};

// React 元件範例
export const SymptomChecker = () => {
    const { assessSymptoms, loading, error, result } = useMedicalAssessment();
    const [symptomText, setSymptomText] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!symptomText.trim()) {
            alert('請輸入症狀描述');
            return;
        }

        try {
            await assessSymptoms({ symptom_text: symptomText });
        } catch (err) {
            console.error('症狀評估失敗:', err);
        }
    };

    return (
        <div className="symptom-checker">
            <form onSubmit={handleSubmit}>
                <textarea
                    value={symptomText}
                    onChange={(e) => setSymptomText(e.target.value)}
                    placeholder="請描述您的症狀..."
                    rows={4}
                    disabled={loading}
                />
                <button type="submit" disabled={loading || !symptomText.trim()}>
                    {loading ? '評估中...' : '開始評估'}
                </button>
            </form>

            {error && (
                <div className="error">
                    錯誤：{error}
                </div>
            )}

            {result && (
                <div className={`result level-${result.level}`}>
                    <h3>評估結果</h3>
                    <p><strong>級別：</strong>{result.level}</p>
                    <p><strong>建議：</strong>{result.advice}</p>

                    {result.level === 'emergency' && (
                        <div className="emergency-alert">
                            ⚠️ 緊急狀況！請立即撥打 119
                        </div>
                    )}

                    <details>
                        <summary>詳細建議</summary>
                        <ul>
                            {result.next_steps.map((step, index) => (
                                <li key={index}>{step}</li>
                            ))}
                        </ul>
                    </details>
                </div>
            )}
        </div>
    );
};
```

### 🏥 醫療系統整合

#### HIS (Hospital Information System) 整合
```python
# 醫院資訊系統整合範例
class HISIntegration:
    def __init__(self, his_database, medical_ai_client):
        self.his_db = his_database
        self.ai_client = medical_ai_client

    def enhanced_admission_triage(self, patient_id, chief_complaint):
        """增強型入院分流"""

        # 從 HIS 取得病患資料
        patient = self.his_db.get_patient(patient_id)

        # AI 症狀評估
        assessment = self.ai_client.assess_symptoms(
            symptom_text=chief_complaint,
            age=patient.age,
            gender=patient.gender,
            has_chronic_disease=len(patient.chronic_conditions) > 0,
            medications=[med.name for med in patient.current_medications]
        )

        # 結合 HIS 資料與 AI 評估
        enhanced_triage = {
            'patient_id': patient_id,
            'ai_assessment': assessment,
            'medical_history': patient.medical_history,
            'vital_signs': patient.latest_vitals,
            'recommended_department': self.determine_department(assessment),
            'priority_score': self.calculate_priority(assessment, patient)
        }

        # 更新 HIS 分流資料
        self.his_db.update_triage_data(patient_id, enhanced_triage)

        return enhanced_triage

    def determine_department(self, assessment):
        """根據評估結果決定科室"""
        if assessment['level'] == 'emergency':
            return 'emergency_department'
        elif 'chest_pain' in assessment.get('detected_symptoms', []):
            return 'cardiology'
        elif 'headache' in assessment.get('detected_symptoms', []):
            return 'neurology'
        else:
            return 'general_medicine'
```

---

## 最佳實踐

### 🎯 症狀輸入最佳實踐

#### 詳細描述症狀
```python
# ❌ 不好的範例
symptom_text = "不舒服"

# ✅ 好的範例
symptom_text = "右下腹疼痛持續6小時，伴隨噁心和輕微發燒37.5°C"
```

#### 提供相關背景資訊
```python
# 完整的症狀評估請求
assessment_request = {
    "symptom_text": "胸痛並延伸至左臂，持續約30分鐘",
    "age": 55,
    "gender": "M",
    "duration_hours": 0.5,
    "has_chronic_disease": True,  # 有高血壓病史
    "medications": ["降血壓藥", "阿斯匹靈"],
    "activity_when_started": "爬樓梯時開始",
    "pain_scale": 8  # 1-10分疼痛量表
}
```

### 🚨 緊急狀況處理流程

#### 自動緊急狀況檢測
```python
def handle_emergency_assessment(assessment_result):
    """處理緊急評估結果"""

    if assessment_result['level'] == 'emergency':
        # 1. 立即記錄警報
        log_emergency_alert(assessment_result)

        # 2. 觸發通知機制
        notify_emergency_contacts(assessment_result)

        # 3. 提供最近醫院資訊
        if 'nearest_hospitals' in assessment_result:
            display_emergency_hospitals(assessment_result['nearest_hospitals'])

        # 4. 顯示緊急指引
        show_emergency_instructions(assessment_result['emergency_numbers'])

        return {
            'immediate_action': True,
            'message': '⚠️ 緊急狀況！請立即撥打119或前往急診',
            'hospitals': assessment_result.get('nearest_hospitals', []),
            'emergency_numbers': assessment_result['emergency_numbers']
        }

    return None
```

### 🏥 醫院搜尋優化方法

#### 智慧半徑調整
```python
def smart_hospital_search(latitude, longitude, initial_radius=3000):
    """智慧醫院搜尋，自動調整搜尋半徑"""

    radius = initial_radius
    max_radius = 20000  # 最大20公里
    min_results = 3     # 最少醫院數量

    while radius <= max_radius:
        hospitals = search_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            radius=radius
        )

        if len(hospitals['results']) >= min_results:
            return hospitals

        # 擴大搜尋範圍
        radius += 2000

    # 如果仍找不到足夠醫院，返回最大範圍的結果
    return search_nearby_hospitals(latitude, longitude, max_radius)
```

#### 醫院篩選與排序
```python
def filter_and_sort_hospitals(hospitals, preferences=None):
    """篩選和排序醫院結果"""

    if not preferences:
        preferences = {
            'emergency_only': False,
            'contracted_only': True,  # 只顯示健保特約
            'min_rating': 3.0,
            'max_distance_m': 10000
        }

    filtered = []

    for hospital in hospitals['results']:
        # 篩選條件
        if preferences['emergency_only'] and not hospital.get('has_emergency', False):
            continue

        if preferences['contracted_only'] and not hospital.get('is_contracted', False):
            continue

        if hospital.get('rating', 0) < preferences['min_rating']:
            continue

        if hospital.get('distance_m', float('inf')) > preferences['max_distance_m']:
            continue

        filtered.append(hospital)

    # 排序：急診醫院優先，然後按距離
    def sort_key(hospital):
        has_emergency = hospital.get('has_emergency', False)
        distance = hospital.get('distance_m', float('inf'))
        rating = hospital.get('rating', 0)

        # 急診醫院優先權重
        emergency_weight = 0 if has_emergency else 10000

        return emergency_weight + distance - (rating * 100)

    filtered.sort(key=sort_key)

    return {
        'results': filtered,
        'total_found': len(filtered),
        'search_criteria': preferences
    }
```

### 📊 系統監控使用方法

#### 自動健康檢查
```python
import asyncio
import aiohttp
from datetime import datetime, timedelta

class SystemHealthMonitor:
    def __init__(self, api_base_url):
        self.api_url = api_base_url
        self.check_interval = 60  # 每分鐘檢查一次
        self.alert_thresholds = {
            'response_time_ms': 5000,
            'error_rate_percent': 5.0,
            'memory_usage_percent': 85.0
        }

    async def continuous_monitoring(self):
        """持續監控系統狀態"""
        while True:
            try:
                health_status = await self.check_system_health()

                # 檢查警報條件
                if self.should_alert(health_status):
                    await self.send_alert(health_status)

                # 記錄狀態
                self.log_health_status(health_status)

            except Exception as e:
                await self.handle_monitoring_error(e)

            await asyncio.sleep(self.check_interval)

    async def check_system_health(self):
        """檢查系統健康狀態"""
        async with aiohttp.ClientSession() as session:
            start_time = datetime.now()

            # 健康檢查
            async with session.get(f'{self.api_url}/v1/monitoring/health') as response:
                response_time = (datetime.now() - start_time).total_seconds() * 1000
                health_data = await response.json()

                # 取得詳細度量
                async with session.get(f'{self.api_url}/v1/monitoring/metrics') as metrics_response:
                    metrics_data = await metrics_response.json()

                return {
                    'timestamp': datetime.now().isoformat(),
                    'response_time_ms': response_time,
                    'status_code': response.status,
                    'health_data': health_data,
                    'metrics': metrics_data
                }

    def should_alert(self, health_status):
        """判斷是否需要發送警報"""
        if health_status['status_code'] != 200:
            return True

        if health_status['response_time_ms'] > self.alert_thresholds['response_time_ms']:
            return True

        metrics = health_status.get('metrics', {})
        error_rate = metrics.get('error_rate_percent', 0)
        if error_rate > self.alert_thresholds['error_rate_percent']:
            return True

        return False
```

### ⚡ 效能優化建議

#### 請求快取策略
```python
import redis
import json
from functools import wraps
from datetime import timedelta

class APICache:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 300  # 5分鐘

    def cache_result(self, key_prefix, ttl=None):
        """API 結果快取裝飾器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 產生快取鍵
                cache_key = f"{key_prefix}:{hash(str(args) + str(kwargs))}"

                # 嘗試從快取取得
                cached_result = self.redis.get(cache_key)
                if cached_result:
                    return json.loads(cached_result)

                # 執行原函數
                result = await func(*args, **kwargs)

                # 儲存到快取
                ttl_seconds = ttl or self.default_ttl
                self.redis.setex(
                    cache_key,
                    ttl_seconds,
                    json.dumps(result, ensure_ascii=False)
                )

                return result

            return wrapper
        return decorator

# 使用範例
cache = APICache(redis.Redis(host='localhost', port=6379, db=0))

@cache.cache_result('hospital_search', ttl=600)  # 快取10分鐘
async def cached_hospital_search(lat, lng, radius):
    return await search_nearby_hospitals(lat, lng, radius)
```

#### 批次請求處理
```python
class BatchRequestProcessor:
    def __init__(self, batch_size=10, timeout_seconds=5):
        self.batch_size = batch_size
        self.timeout = timeout_seconds
        self.pending_requests = []

    async def add_request(self, request_data):
        """新增請求到批次處理佇列"""
        self.pending_requests.append(request_data)

        # 如果達到批次大小，立即處理
        if len(self.pending_requests) >= self.batch_size:
            return await self.process_batch()

        # 否則等待超時
        await asyncio.sleep(self.timeout)
        if self.pending_requests:
            return await self.process_batch()

    async def process_batch(self):
        """處理一批請求"""
        if not self.pending_requests:
            return []

        current_batch = self.pending_requests.copy()
        self.pending_requests.clear()

        # 並行處理多個請求
        tasks = [
            self.process_single_request(req)
            for req in current_batch
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

---

## 故障排除

### 🔍 常見問題診斷

#### API 連線問題
```bash
# 檢查服務狀態
curl -I http://localhost:8000/healthz

# 檢查網路連通性
ping localhost

# 檢查埠口占用
netstat -tulpn | grep :8000

# 檢查防火牆設定
sudo ufw status
```

#### 效能問題診斷
```python
import time
import psutil
import requests
from datetime import datetime

def diagnose_performance_issues(api_url):
    """診斷 API 效能問題"""

    # 1. 測試回應時間
    start_time = time.time()
    try:
        response = requests.get(f"{api_url}/healthz", timeout=10)
        response_time = (time.time() - start_time) * 1000

        print(f"API 回應時間: {response_time:.2f} ms")

        if response_time > 5000:
            print("⚠️ 回應時間過慢")
    except requests.Timeout:
        print("❌ API 回應超時")
    except requests.ConnectionError:
        print("❌ 無法連線到 API")

    # 2. 檢查系統資源
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    print(f"CPU 使用率: {cpu_usage}%")
    print(f"記憶體使用率: {memory.percent}%")
    print(f"磁碟使用率: {disk.percent}%")

    # 3. 警告條件
    if cpu_usage > 80:
        print("⚠️ CPU 使用率過高")
    if memory.percent > 85:
        print("⚠️ 記憶體使用率過高")
    if disk.percent > 90:
        print("⚠️ 磁碟空間不足")

    return {
        'response_time_ms': response_time,
        'cpu_usage_percent': cpu_usage,
        'memory_usage_percent': memory.percent,
        'disk_usage_percent': disk.percent
    }
```

### 🚨 錯誤處理

#### 標準錯誤回應格式
```json
{
  "error": {
    "code": "SYMPTOM_ASSESSMENT_FAILED",
    "message": "症狀評估服務暫時無法使用",
    "details": "外部 API 回應超時",
    "timestamp": "2024-09-19T12:00:00Z",
    "request_id": "req_12345678",
    "suggested_action": "請稍後再試，或直接撥打119尋求協助"
  }
}
```

#### 錯誤處理最佳實踐
```python
class MedicalAIErrorHandler:
    def __init__(self):
        self.error_codes = {
            'API_UNAVAILABLE': '服務暫時無法使用',
            'INVALID_SYMPTOMS': '症狀描述格式無效',
            'GEOCODING_FAILED': '地址解析失敗',
            'NO_HOSPITALS_FOUND': '附近未找到醫院',
            'RATE_LIMIT_EXCEEDED': '請求頻率過高'
        }

    def handle_api_error(self, error, request_context=None):
        """處理 API 錯誤"""

        if isinstance(error, requests.ConnectionError):
            return self.create_error_response(
                'API_UNAVAILABLE',
                '無法連線到醫療評估服務',
                suggested_action='請檢查網路連線或稍後再試'
            )

        elif isinstance(error, requests.Timeout):
            return self.create_error_response(
                'API_TIMEOUT',
                '服務回應超時',
                suggested_action='請稍後再試，緊急情況請撥打119'
            )

        elif hasattr(error, 'response') and error.response:
            status_code = error.response.status_code

            if status_code == 400:
                return self.create_error_response(
                    'INVALID_REQUEST',
                    '請求格式錯誤',
                    suggested_action='請檢查輸入的症狀描述'
                )

            elif status_code == 429:
                return self.create_error_response(
                    'RATE_LIMIT_EXCEEDED',
                    '請求過於頻繁',
                    suggested_action='請稍後再試'
                )

            elif status_code >= 500:
                return self.create_error_response(
                    'SERVER_ERROR',
                    '服務器內部錯誤',
                    suggested_action='請稍後再試或聯絡技術支援'
                )

        # 預設錯誤處理
        return self.create_error_response(
            'UNKNOWN_ERROR',
            '發生未知錯誤',
            suggested_action='請稍後再試，緊急情況請撥打119'
        )

    def create_error_response(self, code, message, suggested_action=None):
        """建立標準錯誤回應"""
        return {
            'error': {
                'code': code,
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'suggested_action': suggested_action or '請稍後再試'
            }
        }
```

### 📋 故障排除檢查清單

#### 服務啟動問題
- [ ] 環境變數是否正確設定
- [ ] Google API 金鑰是否有效
- [ ] 埠口 8000 是否被占用
- [ ] Python 依賴套件是否完整安裝
- [ ] 資料庫連線是否正常

#### API 呼叫問題
- [ ] API 端點 URL 是否正確
- [ ] 請求格式是否符合規範
- [ ] 必要參數是否完整提供
- [ ] Content-Type 標頭是否正確
- [ ] 網路防火牆是否允許連線

#### 效能問題
- [ ] 服務器 CPU 和記憶體使用率
- [ ] 網路延遲和頻寬
- [ ] 外部 API (Google Places) 配額
- [ ] 資料庫查詢效能
- [ ] 快取機制是否正常運作

---

## 安全與隱私

### 🔒 PDPA 合規要求

#### 個人資料最小化
```python
class PrivacyManager:
    def __init__(self):
        self.sensitive_fields = [
            'phone', 'id_number', 'address', 'email',
            'full_name', 'birthday'
        ]

    def sanitize_input(self, data):
        """清理敏感資料"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key in self.sensitive_fields:
                    data[key] = self.mask_sensitive_data(value)
                elif isinstance(value, (dict, list)):
                    data[key] = self.sanitize_input(value)

        elif isinstance(data, list):
            data = [self.sanitize_input(item) for item in data]

        return data

    def mask_sensitive_data(self, value):
        """遮罩敏感資料"""
        if not value:
            return value

        value_str = str(value)

        # 電話號碼遮罩
        if re.match(r'^\d{4}-?\d{3}-?\d{3}$', value_str):
            return value_str[:4] + '***' + value_str[-3:]

        # 身分證號遮罩
        if re.match(r'^[A-Z]\d{9}$', value_str):
            return value_str[:2] + '*****' + value_str[-2:]

        # 一般遮罩
        if len(value_str) > 3:
            return value_str[:2] + '*' * (len(value_str) - 3) + value_str[-1:]

        return '***'
```

#### 審計日誌記錄
```python
import json
import hashlib
from datetime import datetime

class AuditLogger:
    def __init__(self, log_file_path):
        self.log_file = log_file_path

    def log_medical_query(self, request_data, response_data, user_context=None):
        """記錄醫療查詢審計日誌"""

        # 不記錄敏感內容，只記錄必要的審計資訊
        audit_record = {
            'timestamp': datetime.now().isoformat(),
            'request_id': request_data.get('request_id'),
            'query_type': self.determine_query_type(request_data),
            'response_level': response_data.get('level'),
            'user_age_group': self.anonymize_age(request_data.get('age')),
            'symptom_hash': self.hash_symptom(request_data.get('symptom_text')),
            'ip_hash': self.hash_ip(user_context.get('ip_address') if user_context else None),
            'processing_time_ms': response_data.get('processing_time_ms'),
            'emergency_triggered': response_data.get('level') == 'emergency'
        }

        self.write_audit_log(audit_record)

    def hash_symptom(self, symptom_text):
        """症狀文字雜湊化"""
        if not symptom_text:
            return None

        # 使用 SHA-256 雜湊，無法還原原始文字
        return hashlib.sha256(symptom_text.encode('utf-8')).hexdigest()[:16]

    def anonymize_age(self, age):
        """年齡匿名化"""
        if not age:
            return None

        # 將年齡分組，避免精確年齡資訊
        if age < 18:
            return 'minor'
        elif age < 30:
            return '18-29'
        elif age < 50:
            return '30-49'
        elif age < 65:
            return '50-64'
        else:
            return '65+'

    def write_audit_log(self, record):
        """寫入審計日誌"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

### 🛡️ API 安全措施

#### 速率限制
```python
from fastapi import HTTPException
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self, max_requests=100, time_window=3600):
        self.max_requests = max_requests
        self.time_window = time_window  # 秒
        self.requests = defaultdict(list)

    def check_rate_limit(self, client_id):
        """檢查速率限制"""
        now = time.time()
        client_requests = self.requests[client_id]

        # 移除過期的請求記錄
        client_requests[:] = [
            req_time for req_time in client_requests
            if now - req_time < self.time_window
        ]

        # 檢查是否超過限制
        if len(client_requests) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail={
                    'error': 'Rate limit exceeded',
                    'message': f'每小時最多 {self.max_requests} 次請求',
                    'retry_after': self.time_window - (now - client_requests[0])
                }
            )

        # 記錄新請求
        client_requests.append(now)

        return True
```

#### 輸入驗證與清理
```python
import re
from typing import Any, Dict

class InputValidator:
    def __init__(self):
        self.max_symptom_length = 1000
        self.forbidden_patterns = [
            r'<script[^>]*>.*?</script>',  # XSS 防護
            r'javascript:',
            r'on\w+\s*=',  # 事件處理器
        ]

    def validate_symptom_input(self, symptom_text: str) -> str:
        """驗證並清理症狀輸入"""
        if not symptom_text:
            raise ValueError('症狀描述不能為空')

        if len(symptom_text) > self.max_symptom_length:
            raise ValueError(f'症狀描述過長，最多 {self.max_symptom_length} 字元')

        # 檢查惡意模式
        for pattern in self.forbidden_patterns:
            if re.search(pattern, symptom_text, re.IGNORECASE):
                raise ValueError('輸入包含不允許的內容')

        # 清理 HTML 標籤
        clean_text = re.sub(r'<[^>]+>', '', symptom_text)

        # 移除多餘空白
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        return clean_text

    def validate_coordinates(self, latitude: float, longitude: float) -> bool:
        """驗證座標範圍（台灣地區）"""
        # 台灣座標範圍
        taiwan_bounds = {
            'lat_min': 21.0, 'lat_max': 26.0,
            'lng_min': 119.0, 'lng_max': 122.5
        }

        if not (taiwan_bounds['lat_min'] <= latitude <= taiwan_bounds['lat_max']):
            raise ValueError('緯度超出台灣地區範圍')

        if not (taiwan_bounds['lng_min'] <= longitude <= taiwan_bounds['lng_max']):
            raise ValueError('經度超出台灣地區範圍')

        return True
```

### 🔐 資料保護措施

#### 敏感資料加密
```python
from cryptography.fernet import Fernet
import base64
import os

class DataProtection:
    def __init__(self, encryption_key=None):
        if encryption_key:
            self.key = encryption_key.encode()
        else:
            self.key = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())

        self.cipher = Fernet(self.key)

    def encrypt_sensitive_data(self, data: str) -> str:
        """加密敏感資料"""
        if not data:
            return data

        encrypted = self.cipher.encrypt(data.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """解密敏感資料"""
        if not encrypted_data:
            return encrypted_data

        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode('utf-8')
        except Exception:
            raise ValueError('解密失敗，資料可能已損壞')

    def secure_hash(self, data: str) -> str:
        """安全雜湊"""
        import hashlib
        import secrets

        salt = secrets.token_hex(16)
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode('utf-8'), salt.encode('utf-8'), 100000)
        return f"{salt}:{hash_obj.hex()}"
```

---

## 結語

本使用指南涵蓋了台灣醫療 AI 助理的全面使用方法，從基本 API 操作到進階整合應用。請根據您的具體需求選擇適合的整合方式，並務必遵循最佳實踐以確保系統安全與效能。

### 📞 技術支援

如遇到技術問題，請依照以下順序處理：

1. **查閱本使用指南的故障排除章節**
2. **檢查 API 文件：** `http://localhost:8000/docs`
3. **查看系統監控：** `http://localhost:8000/v1/monitoring/dashboard`
4. **聯絡技術支援團隊**

### ⚠️ 重要提醒

- 本系統僅供醫療資訊參考，不取代專業醫療診斷
- 緊急狀況請立即撥打 119 或 112
- 遵循 PDPA 個人資料保護法規範
- 定期更新系統以確保安全性

---

*最後更新：2024年9月19日*