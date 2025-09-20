/**
 * API 配置檔案
 * 根據環境自動選擇 API 基礎 URL
 */

// 取得環境變數或使用預設值
const getApiBaseUrl = (): string => {
  // 從環境變數取得 API URL
  const envApiUrl = process.env.REACT_APP_API_BASE_URL;

  if (envApiUrl) {
    return envApiUrl;
  }

  // 根據當前環境自動判斷
  if (process.env.NODE_ENV === 'production') {
    // 生產環境：部署在 PythonAnywhere
    return 'https://thc1006.pythonanywhere.com';
  } else {
    // 開發環境：本地後端
    return 'http://localhost:8000';
  }
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  ENDPOINTS: {
    // 症狀分析
    TRIAGE: '/v1/triage',
    TRIAGE_QUICK: '/v1/triage/quick',

    // 醫院搜尋
    HOSPITALS_NEARBY: '/v1/hospitals/nearby',
    HOSPITALS_EMERGENCY: '/v1/hospitals/emergency-info',

    // 健康資訊
    HEALTH_TOPICS: '/v1/healthinfo/topics',
    HEALTH_RESOURCES: '/v1/healthinfo/resources',

    // 監控
    HEALTH_CHECK: '/v1/monitoring/health',
    METRICS: '/v1/monitoring/metrics'
  },

  // 請求超時設定（毫秒）
  TIMEOUT: 10000,

  // 重試次數
  RETRY_COUNT: 3
} as const;

// 完整的 API URL 建構函數
export const buildApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// API 狀態檢查
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.HEALTH_CHECK), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(5000) // 5秒超時
    });

    return response.ok;
  } catch (error) {
    console.warn('API 健康檢查失敗:', error);
    return false;
  }
};

// 環境資訊（用於除錯）
export const ENV_INFO = {
  NODE_ENV: process.env.NODE_ENV,
  API_BASE_URL: API_CONFIG.BASE_URL,
  BUILD_TIME: new Date().toISOString()
};

console.log('🔧 API 配置:', ENV_INFO);