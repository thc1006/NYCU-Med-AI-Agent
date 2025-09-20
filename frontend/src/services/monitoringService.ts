/**
 * 監控服務層 - 處理系統健康狀態和指標監控
 */

import { API_CONFIG, buildApiUrl, checkApiHealth } from '../config/api';
import { API_ENDPOINTS } from '../types';

// 系統健康狀態介面
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  uptime: number;
  checks: {
    database: boolean;
    external_apis: boolean;
    memory_usage: number;
    cpu_usage: number;
  };
}

// 系統指標介面
export interface SystemMetrics {
  timestamp: string;
  request_count: number;
  average_response_time: number;
  error_rate: number;
  active_users: number;
  memory_usage: {
    used: number;
    total: number;
    percentage: number;
  };
  cpu_usage: {
    percentage: number;
  };
}

// 監控服務 API
export const monitoringService = {
  /**
   * 檢查系統健康狀態
   */
  async getHealthStatus(): Promise<HealthStatus> {
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.HEALTH_CHECK), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        signal: AbortSignal.timeout(5000) // 健康檢查使用較短的超時時間
      });

      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[Health Check API Error]', error);

      // 回傳降級狀態
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        version: 'unknown',
        uptime: 0,
        checks: {
          database: false,
          external_apis: false,
          memory_usage: 0,
          cpu_usage: 0
        }
      };
    }
  },

  /**
   * 取得系統指標
   */
  async getSystemMetrics(): Promise<SystemMetrics> {
    try {
      const response = await fetch(buildApiUrl(API_ENDPOINTS.METRICS), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });

      if (!response.ok) {
        throw new Error(`Metrics fetch failed: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[Metrics API Error]', error);
      throw error;
    }
  },

  /**
   * 檢查 API 連線狀態（使用 config/api.ts 的功能）
   */
  async checkConnection(): Promise<boolean> {
    return await checkApiHealth();
  },

  /**
   * 監控 API 回應時間
   */
  async measureApiResponseTime(endpoint: string): Promise<number> {
    const startTime = performance.now();

    try {
      const response = await fetch(buildApiUrl(endpoint), {
        method: 'HEAD', // 只檢查標頭，不需要回應內容
        signal: AbortSignal.timeout(5000)
      });

      const endTime = performance.now();

      if (response.ok) {
        return endTime - startTime;
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error(`[API Response Time Error] ${endpoint}:`, error);
      return -1; // 表示測量失敗
    }
  },

  /**
   * 批量檢查多個端點的健康狀態
   */
  async checkMultipleEndpoints(): Promise<{[endpoint: string]: boolean}> {
    const endpoints = [
      API_ENDPOINTS.HEALTH_CHECK,
      API_ENDPOINTS.TRIAGE_QUICK,
      API_ENDPOINTS.HOSPITALS_NEARBY
    ];

    const results: {[endpoint: string]: boolean} = {};

    await Promise.allSettled(
      endpoints.map(async (endpoint) => {
        try {
          const response = await fetch(buildApiUrl(endpoint), {
            method: 'HEAD',
            signal: AbortSignal.timeout(5000)
          });
          results[endpoint] = response.ok;
        } catch (error) {
          results[endpoint] = false;
        }
      })
    );

    return results;
  }
};

export default monitoringService;