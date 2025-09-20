/**
 * 健康資訊服務層 - 處理健康知識和資源相關 API
 */

import { API_CONFIG, buildApiUrl } from '../config/api';
import { API_ENDPOINTS } from '../types';

// 健康主題介面
export interface HealthTopic {
  id: string;
  title: string;
  description: string;
  content: string;
  category: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

// 健康資源介面
export interface HealthResource {
  id: string;
  title: string;
  type: string; // 'article', 'video', 'pdf', 'link'
  url: string;
  description: string;
  category: string;
  language: string;
  created_at: string;
}

// 健康服務 API
export const healthService = {
  /**
   * 取得健康主題列表
   */
  async getHealthTopics(params?: {
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<HealthTopic[]> {
    try {
      const url = new URL(buildApiUrl(API_ENDPOINTS.HEALTH_TOPICS));

      if (params?.category) {
        url.searchParams.append('category', params.category);
      }
      if (params?.limit) {
        url.searchParams.append('limit', params.limit.toString());
      }
      if (params?.offset) {
        url.searchParams.append('offset', params.offset.toString());
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Accept-Language': 'zh-TW'
        },
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[Health Topics API Error]', error);
      throw error;
    }
  },

  /**
   * 取得健康資源列表
   */
  async getHealthResources(params?: {
    type?: string;
    category?: string;
    limit?: number;
    offset?: number;
  }): Promise<HealthResource[]> {
    try {
      const url = new URL(buildApiUrl(API_ENDPOINTS.HEALTH_RESOURCES));

      if (params?.type) {
        url.searchParams.append('type', params.type);
      }
      if (params?.category) {
        url.searchParams.append('category', params.category);
      }
      if (params?.limit) {
        url.searchParams.append('limit', params.limit.toString());
      }
      if (params?.offset) {
        url.searchParams.append('offset', params.offset.toString());
      }

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Accept-Language': 'zh-TW'
        },
        signal: AbortSignal.timeout(API_CONFIG.TIMEOUT)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('[Health Resources API Error]', error);
      throw error;
    }
  }
};

export default healthService;