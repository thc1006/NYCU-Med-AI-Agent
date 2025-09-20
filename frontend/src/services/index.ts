/**
 * 服務層統一匯出入口
 */

// 主要 API 服務
export * from './api';

// 健康資訊服務
export * from './healthService';

// 監控服務
export * from './monitoringService';

// 重新匯出主要服務實例以方便使用
export { default as api } from './api';
export { default as healthService } from './healthService';
export { default as monitoringService } from './monitoringService';

// 統一的服務配置
export const SERVICES_CONFIG = {
  // 重試配置
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000,

  // 超時配置
  DEFAULT_TIMEOUT: 10000,
  HEALTH_CHECK_TIMEOUT: 5000,

  // 快取配置
  CACHE_TTL: 300000, // 5分鐘

  // 錯誤處理
  ERROR_REPORTING: true,

  // API 版本
  API_VERSION: 'v1'
} as const;