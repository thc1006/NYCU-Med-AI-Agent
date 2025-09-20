/**
 * 地理位置 Hook
 */

import { useState, useEffect, useCallback } from 'react';
import { locationApi } from '../services/api';
import { useLocation } from '../stores/useAppStore';
import toast from 'react-hot-toast';

interface UseGeolocationOptions {
  enableHighAccuracy?: boolean;
  timeout?: number;
  maximumAge?: number;
  onSuccess?: (position: { latitude: number; longitude: number }) => void;
  onError?: (error: string) => void;
}

interface UseGeolocationReturn {
  location: { latitude: number; longitude: number } | null;
  error: string | null;
  loading: boolean;
  getCurrentLocation: () => Promise<void>;
  clearLocation: () => void;
  isSupported: boolean;
}

export const useGeolocation = (options: UseGeolocationOptions = {}): UseGeolocationReturn => {
  const {
    userLocation,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    locationPermission,
    setUserLocation,
    setLocationPermission
  } = useLocation();

  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 檢查瀏覽器是否支援地理定位
  const isSupported = 'geolocation' in navigator;

  /**
   * 取得目前位置
   */
  const getCurrentLocation = useCallback(async () => {
    if (!isSupported) {
      const errorMsg = '此瀏覽器不支援地理定位功能';
      setError(errorMsg);
      options.onError?.(errorMsg);
      toast.error(errorMsg);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const position = await locationApi.getCurrentLocation();

      setUserLocation(position);
      setLocationPermission(true);
      setError(null);

      options.onSuccess?.(position);
      toast.success('已取得您的位置');

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '無法取得位置資訊';

      setError(errorMsg);
      setLocationPermission(false);
      options.onError?.(errorMsg);

      // 針對不同錯誤類型顯示不同訊息
      if (errorMsg.includes('拒絕')) {
        toast.error('請允許位置存取以搜尋附近醫院', {
          duration: 5000
        });
      } else if (errorMsg.includes('超時')) {
        toast.error('定位超時，請檢查GPS設定');
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  }, [isSupported, options, setUserLocation, setLocationPermission]);

  /**
   * 清除位置資訊
   */
  const clearLocation = useCallback(() => {
    setUserLocation(null);
    setError(null);
    setLocationPermission(false);
  }, [setUserLocation, setLocationPermission]);

  /**
   * 監聽位置權限變化
   */
  useEffect(() => {
    if (!isSupported) return;

    // 檢查位置權限狀態
    if ('permissions' in navigator) {
      navigator.permissions.query({ name: 'geolocation' }).then((result) => {
        setLocationPermission(result.state === 'granted');

        // 監聽權限變化
        result.addEventListener('change', () => {
          const hasPermission = result.state === 'granted';
          setLocationPermission(hasPermission);

          if (result.state === 'denied') {
            setUserLocation(null);
            setError('位置存取被拒絕');
          }
        });
      }).catch(() => {
        // 某些瀏覽器不支援 permissions API
        console.warn('Cannot check geolocation permission');
      });
    }
  }, [isSupported, setLocationPermission, setUserLocation]);

  return {
    location: userLocation,
    error,
    loading,
    getCurrentLocation,
    clearLocation,
    isSupported
  };
};