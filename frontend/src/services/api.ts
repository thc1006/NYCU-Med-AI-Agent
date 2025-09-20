/**
 * API 服務層 - 與後端 FastAPI 通訊
 */

import axios, { AxiosResponse } from 'axios';
import {
  TriageRequest,
  TriageResponse,
  Hospital,
  EmergencyInfo,
  API_ENDPOINTS
} from '../types';

// 建立 axios 實例
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Accept-Language': 'zh-TW'
  }
});

// 請求攔截器 - 加入請求 ID 和時間戳
api.interceptors.request.use(
  (config) => {
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    config.headers['X-Request-ID'] = requestId;
    config.headers['X-Client-Timestamp'] = new Date().toISOString();

    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      requestId,
      data: config.data
    });

    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// 回應攔截器 - 統一錯誤處理
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log(`[API Response] ${response.status}`, {
      requestId: response.headers['x-request-id'],
      data: response.data
    });
    return response;
  },
  (error) => {
    console.error('[API Response Error]', {
      status: error.response?.status,
      message: error.response?.data?.message || error.message,
      url: error.config?.url
    });

    // 轉換錯誤訊息為繁體中文
    const errorMessage = getErrorMessage(error);
    error.message = errorMessage;

    return Promise.reject(error);
  }
);

/**
 * 將錯誤訊息轉換為使用者友善的繁體中文訊息
 */
function getErrorMessage(error: any): string {
  if (error.response?.data?.message) {
    return error.response.data.message;
  }

  switch (error.response?.status) {
    case 400:
      return '請求參數有誤，請檢查輸入資料';
    case 401:
      return '未授權存取，請重新登入';
    case 403:
      return '沒有權限執行此操作';
    case 404:
      return '找不到相關資源';
    case 429:
      return '請求過於頻繁，請稍後再試';
    case 500:
      return '伺服器發生錯誤，請稍後再試';
    case 502:
    case 503:
    case 504:
      return '服務暫時無法使用，請稍後再試';
    default:
      if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
        return '網路連線異常，請檢查網路設定';
      }
      if (error.code === 'ECONNABORTED') {
        return '請求超時，請重試';
      }
      return '系統發生未知錯誤，請聯絡技術支援';
  }
}

/**
 * 症狀分級評估 API
 */
export const triageApi = {
  /**
   * 快速症狀評估
   */
  async quickTriage(request: TriageRequest): Promise<TriageResponse> {
    try {
      const response = await api.post<TriageResponse>(
        API_ENDPOINTS.TRIAGE_QUICK,
        request
      );
      return response.data;
    } catch (error) {
      console.error('[Triage API Error]', error);
      throw error;
    }
  }
};

/**
 * 醫院搜尋 API
 */
export const hospitalApi = {
  /**
   * 搜尋附近醫院
   */
  async searchNearby(params: {
    latitude: number;
    longitude: number;
    radius?: number;
    limit?: number;
    departments?: string[];
    emergency_only?: boolean;
  }): Promise<Hospital[]> {
    try {
      const response = await api.get<Hospital[]>(API_ENDPOINTS.HOSPITALS_NEARBY, {
        params: {
          lat: params.latitude,
          lng: params.longitude,
          radius: params.radius || 5000,
          limit: params.limit || 20,
          departments: params.departments?.join(','),
          emergency_only: params.emergency_only || false
        }
      });
      return response.data;
    } catch (error) {
      console.error('[Hospital Search API Error]', error);
      throw error;
    }
  },

  /**
   * 取得緊急醫療資訊
   */
  async getEmergencyInfo(): Promise<EmergencyInfo> {
    try {
      const response = await api.get<EmergencyInfo>(API_ENDPOINTS.EMERGENCY_INFO);
      return response.data;
    } catch (error) {
      console.error('[Emergency Info API Error]', error);
      throw error;
    }
  }
};

/**
 * 地理位置服務
 */
export const locationApi = {
  /**
   * 取得使用者目前位置
   */
  async getCurrentLocation(): Promise<{ latitude: number; longitude: number }> {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) {
        reject(new Error('此瀏覽器不支援地理定位功能'));
        return;
      }

      const options: PositionOptions = {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000 // 1分鐘內的快取位置可接受
      };

      navigator.geolocation.getCurrentPosition(
        (position) => {
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          });
        },
        (error) => {
          let message = '無法取得位置資訊';

          switch (error.code) {
            case error.PERMISSION_DENIED:
              message = '使用者拒絕了地理定位請求';
              break;
            case error.POSITION_UNAVAILABLE:
              message = '位置資訊不可用';
              break;
            case error.TIMEOUT:
              message = '定位請求超時';
              break;
          }

          reject(new Error(message));
        },
        options
      );
    });
  },

  /**
   * 計算兩點間距離（公里）
   */
  calculateDistance(
    lat1: number,
    lon1: number,
    lat2: number,
    lon2: number
  ): number {
    const R = 6371; // 地球半徑（公里）
    const dLat = this.degToRad(lat2 - lat1);
    const dLon = this.degToRad(lon2 - lon1);

    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(this.degToRad(lat1)) * Math.cos(this.degToRad(lat2)) *
      Math.sin(dLon / 2) * Math.sin(dLon / 2);

    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  },

  degToRad(deg: number): number {
    return deg * (Math.PI / 180);
  }
};

/**
 * 緊急撥號服務
 */
export const emergencyApi = {
  /**
   * 撥打緊急電話
   * 注意：在網頁環境中，只能開啟撥號程式，無法直接撥號
   */
  call(number: string): void {
    try {
      // 檢查是否為行動裝置
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
        navigator.userAgent
      );

      if (isMobile) {
        // 行動裝置直接撥號
        window.location.href = `tel:${number}`;
      } else {
        // 桌面裝置顯示電話號碼
        alert(`請撥打：${number}\n\n如果您在緊急狀況中，請使用手機撥打此號碼。`);
      }
    } catch (error) {
      console.error('[Emergency Call Error]', error);
      alert(`緊急電話：${number}\n請立即使用電話撥打此號碼。`);
    }
  }
};

export default api;