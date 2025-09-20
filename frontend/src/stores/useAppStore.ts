/**
 * 應用程式狀態管理 - 使用 Zustand
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import {
  AppState,
  SymptomQuery,
  TriageResponse,
  Hospital,
  SymptomHistory
} from '../types';

interface AppActions {
  // 症狀查詢相關
  setCurrentQuery: (query: Partial<SymptomQuery>) => void;
  clearCurrentQuery: () => void;

  // 分級結果相關
  setLatestResult: (result: TriageResponse) => void;
  clearLatestResult: () => void;

  // 醫院相關
  setNearbyHospitals: (hospitals: Hospital[]) => void;
  clearNearbyHospitals: () => void;

  // 症狀歷史相關
  addSymptomHistory: (history: Omit<SymptomHistory, 'id'>) => void;
  removeSymptomHistory: (id: string) => void;
  clearSymptomHistory: () => void;

  // 載入狀態相關
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;

  // 位置相關
  setUserLocation: (location: { latitude: number; longitude: number } | null) => void;
  setLocationPermission: (permission: boolean) => void;

  // 重置狀態
  reset: () => void;
}

type AppStore = AppState & AppActions;

// 初始狀態
const initialState: AppState = {
  currentQuery: {
    symptom_text: '',
    age: undefined,
    gender: undefined,
    duration_hours: undefined,
    has_chronic_disease: false,
    medications: []
  },
  latestResult: null,
  nearbyHospitals: [],
  symptomHistory: [],
  isLoading: false,
  error: null,
  userLocation: null,
  locationPermission: false
};

/**
 * 主要應用程式 Store
 */
export const useAppStore = create<AppStore>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        // 症狀查詢相關
        setCurrentQuery: (query) =>
          set(
            (state) => ({
              currentQuery: { ...state.currentQuery, ...query }
            }),
            false,
            'setCurrentQuery'
          ),

        clearCurrentQuery: () =>
          set(
            () => ({ currentQuery: initialState.currentQuery }),
            false,
            'clearCurrentQuery'
          ),

        // 分級結果相關
        setLatestResult: (result) =>
          set(
            () => ({ latestResult: result }),
            false,
            'setLatestResult'
          ),

        clearLatestResult: () =>
          set(
            () => ({ latestResult: null }),
            false,
            'clearLatestResult'
          ),

        // 醫院相關
        setNearbyHospitals: (hospitals) =>
          set(
            () => ({ nearbyHospitals: hospitals }),
            false,
            'setNearbyHospitals'
          ),

        clearNearbyHospitals: () =>
          set(
            () => ({ nearbyHospitals: [] }),
            false,
            'clearNearbyHospitals'
          ),

        // 症狀歷史相關
        addSymptomHistory: (historyItem) =>
          set(
            (state) => {
              const newHistory: SymptomHistory = {
                ...historyItem,
                id: `history_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
              };

              // 最多保留 50 筆歷史記錄
              const updatedHistory = [newHistory, ...state.symptomHistory].slice(0, 50);

              return { symptomHistory: updatedHistory };
            },
            false,
            'addSymptomHistory'
          ),

        removeSymptomHistory: (id) =>
          set(
            (state) => ({
              symptomHistory: state.symptomHistory.filter(h => h.id !== id)
            }),
            false,
            'removeSymptomHistory'
          ),

        clearSymptomHistory: () =>
          set(
            () => ({ symptomHistory: [] }),
            false,
            'clearSymptomHistory'
          ),

        // 載入狀態相關
        setLoading: (loading) =>
          set(
            () => ({ isLoading: loading }),
            false,
            'setLoading'
          ),

        setError: (error) =>
          set(
            () => ({ error }),
            false,
            'setError'
          ),

        // 位置相關
        setUserLocation: (location) =>
          set(
            () => ({ userLocation: location }),
            false,
            'setUserLocation'
          ),

        setLocationPermission: (permission) =>
          set(
            () => ({ locationPermission: permission }),
            false,
            'setLocationPermission'
          ),

        // 重置狀態
        reset: () =>
          set(
            () => ({ ...initialState }),
            false,
            'reset'
          )
      }),
      {
        name: 'taiwan-med-ai-store',
        partialize: (state) => ({
          // 只持久化這些欄位
          symptomHistory: state.symptomHistory,
          userLocation: state.userLocation,
          locationPermission: state.locationPermission
        })
      }
    ),
    {
      name: 'taiwan-med-ai-store'
    }
  )
);

/**
 * 症狀查詢相關的 hooks
 */
export const useSymptomQuery = () => {
  const currentQuery = useAppStore((state) => state.currentQuery);
  const setCurrentQuery = useAppStore((state) => state.setCurrentQuery);
  const clearCurrentQuery = useAppStore((state) => state.clearCurrentQuery);

  return {
    currentQuery,
    setCurrentQuery,
    clearCurrentQuery
  };
};

/**
 * 分級結果相關的 hooks
 */
export const useTriageResult = () => {
  const latestResult = useAppStore((state) => state.latestResult);
  const setLatestResult = useAppStore((state) => state.setLatestResult);
  const clearLatestResult = useAppStore((state) => state.clearLatestResult);

  return {
    latestResult,
    setLatestResult,
    clearLatestResult
  };
};

/**
 * 醫院搜尋相關的 hooks
 */
export const useHospitals = () => {
  const nearbyHospitals = useAppStore((state) => state.nearbyHospitals);
  const setNearbyHospitals = useAppStore((state) => state.setNearbyHospitals);
  const clearNearbyHospitals = useAppStore((state) => state.clearNearbyHospitals);

  return {
    nearbyHospitals,
    setNearbyHospitals,
    clearNearbyHospitals
  };
};

/**
 * 載入狀態相關的 hooks
 */
export const useLoadingState = () => {
  const isLoading = useAppStore((state) => state.isLoading);
  const error = useAppStore((state) => state.error);
  const setLoading = useAppStore((state) => state.setLoading);
  const setError = useAppStore((state) => state.setError);

  return {
    isLoading,
    error,
    setLoading,
    setError
  };
};

/**
 * 位置相關的 hooks
 */
export const useLocation = () => {
  const userLocation = useAppStore((state) => state.userLocation);
  const locationPermission = useAppStore((state) => state.locationPermission);
  const setUserLocation = useAppStore((state) => state.setUserLocation);
  const setLocationPermission = useAppStore((state) => state.setLocationPermission);

  return {
    userLocation,
    locationPermission,
    setUserLocation,
    setLocationPermission
  };
};

/**
 * 症狀歷史相關的 hooks
 */
export const useSymptomHistory = () => {
  const symptomHistory = useAppStore((state) => state.symptomHistory);
  const addSymptomHistory = useAppStore((state) => state.addSymptomHistory);
  const removeSymptomHistory = useAppStore((state) => state.removeSymptomHistory);
  const clearSymptomHistory = useAppStore((state) => state.clearSymptomHistory);

  return {
    symptomHistory,
    addSymptomHistory,
    removeSymptomHistory,
    clearSymptomHistory
  };
};