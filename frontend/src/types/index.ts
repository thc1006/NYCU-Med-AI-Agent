/**
 * 台灣醫療 AI 助手 - 類型定義
 */

export enum TriageLevel {
  EMERGENCY = "emergency",
  URGENT = "urgent",
  OUTPATIENT = "outpatient",
  SELF_CARE = "self-care"
}

export interface SymptomQuery {
  symptom_text: string;
  age?: number;
  gender?: string;
  duration_hours?: number;
  has_chronic_disease: boolean;
  medications: string[];
}

export interface TriageRequest extends SymptomQuery {
  include_nearby_hospitals: boolean;
  location?: {
    latitude: number;
    longitude: number;
  };
}

export interface TriageResponse {
  triage_level: string;
  advice: string;
  detected_symptoms: string[];
  next_steps: string[];
  disclaimer: string;
  emergency_numbers: string[];
  recommended_departments?: string[];
  estimated_wait_time?: string;
  confidence_score?: number;
  nearby_hospitals?: Hospital[];
  request_id: string;
  timestamp: string;
  locale: string;
}

export interface Hospital {
  id: string;
  name: string;
  address: string;
  phone: string;
  departments: string[];
  distance?: number;
  emergency_services: boolean;
  lat: number;
  lng: number;
  rating?: number;
  hours?: string;
}

export interface EmergencyInfo {
  numbers: string[];
  instructions: string[];
  hospitals: Hospital[];
}

export interface SymptomHistory {
  id: string;
  symptom_text: string;
  triage_level: string;
  timestamp: string;
  location?: {
    latitude: number;
    longitude: number;
  };
}

export interface AppState {
  // 當前症狀查詢
  currentQuery: SymptomQuery;
  // 最新分級結果
  latestResult: TriageResponse | null;
  // 附近醫院
  nearbyHospitals: Hospital[];
  // 症狀歷史
  symptomHistory: SymptomHistory[];
  // 載入狀態
  isLoading: boolean;
  // 錯誤訊息
  error: string | null;
  // 使用者位置
  userLocation: {
    latitude: number;
    longitude: number;
  } | null;
  // 是否允許定位
  locationPermission: boolean;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
  error?: string;
}

// 常見症狀選項
export interface CommonSymptom {
  label: string;
  value: string;
  category: string;
  icon?: string;
}

// 緊急聯絡選項
export interface EmergencyContact {
  number: string;
  label: string;
  description: string;
  icon: string;
}

// 地理位置類型
export interface Coordinates {
  latitude: number;
  longitude: number;
}

// 本地儲存鍵名
export const LOCAL_STORAGE_KEYS = {
  SYMPTOM_HISTORY: 'taiwan-med-ai-symptom-history',
  USER_PREFERENCES: 'taiwan-med-ai-preferences',
  LAST_LOCATION: 'taiwan-med-ai-last-location'
} as const;

// API 端點
export const API_ENDPOINTS = {
  TRIAGE: '/v1/triage',
  TRIAGE_QUICK: '/v1/triage/quick',
  HOSPITALS_NEARBY: '/v1/hospitals/nearby',
  HOSPITALS_EMERGENCY: '/v1/hospitals/emergency-info',
  HEALTH_TOPICS: '/v1/healthinfo/topics',
  HEALTH_RESOURCES: '/v1/healthinfo/resources',
  HEALTH_CHECK: '/v1/monitoring/health',
  METRICS: '/v1/monitoring/metrics'
} as const;

// 緊急電話清單
export const EMERGENCY_NUMBERS: EmergencyContact[] = [
  {
    number: '119',
    label: '救護車',
    description: '醫療緊急狀況',
    icon: '🚑'
  },
  {
    number: '110',
    label: '警察',
    description: '治安緊急狀況',
    icon: '🚔'
  },
  {
    number: '112',
    label: '手機緊急',
    description: '手機緊急撥號',
    icon: '📱'
  }
];

// 常見症狀分類
export const COMMON_SYMPTOMS: CommonSymptom[] = [
  // 緊急症狀
  { label: '胸痛', value: '胸痛', category: '緊急', icon: '💔' },
  { label: '呼吸困難', value: '呼吸困難', category: '緊急', icon: '🫁' },
  { label: '意識不清', value: '意識不清', category: '緊急', icon: '😵' },
  { label: '大量出血', value: '大量出血', category: '緊急', icon: '🩸' },

  // 常見症狀
  { label: '發燒', value: '發燒', category: '一般', icon: '🤒' },
  { label: '頭痛', value: '頭痛', category: '一般', icon: '🤕' },
  { label: '咳嗽', value: '咳嗽', category: '一般', icon: '😷' },
  { label: '腹痛', value: '腹痛', category: '一般', icon: '🤢' },
  { label: '噁心嘔吐', value: '噁心嘔吐', category: '一般', icon: '🤮' },
  { label: '腹瀉', value: '腹瀉', category: '一般', icon: '💩' },
  { label: '流鼻涕', value: '流鼻涕', category: '一般', icon: '🤧' },
  { label: '喉嚨痛', value: '喉嚨痛', category: '一般', icon: '😣' }
];

// 分級等級對應的顏色和圖示
export const TRIAGE_LEVEL_CONFIG = {
  [TriageLevel.EMERGENCY]: {
    color: 'red',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    textColor: 'text-red-800',
    icon: '🚨',
    label: '緊急'
  },
  [TriageLevel.URGENT]: {
    color: 'orange',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-200',
    textColor: 'text-orange-800',
    icon: '⚠️',
    label: '緊急'
  },
  [TriageLevel.OUTPATIENT]: {
    color: 'yellow',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-200',
    textColor: 'text-yellow-800',
    icon: '🏥',
    label: '門診'
  },
  [TriageLevel.SELF_CARE]: {
    color: 'green',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    textColor: 'text-green-800',
    icon: '🏠',
    label: '自我照護'
  }
};