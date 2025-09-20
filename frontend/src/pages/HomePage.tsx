/**
 * 首頁元件 - 症狀評估主介面
 */

import React, { useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

import Header from '../components/Layout/Header';
import SymptomForm from '../components/SymptomForm/SymptomForm';
import TriageResult from '../components/TriageResult/TriageResult';
import HospitalList from '../components/HospitalList/HospitalList';

import { useGeolocation } from '../hooks/useGeolocation';
import {
  useTriageResult,
  useHospitals,
  useLoadingState,
  useSymptomHistory,
  useLocation
} from '../stores/useAppStore';

import { triageApi, hospitalApi, emergencyApi, locationApi } from '../services/api';
import { TriageRequest, Hospital } from '../types';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  // 狀態管理
  const { latestResult, setLatestResult, clearLatestResult } = useTriageResult();
  const { nearbyHospitals, setNearbyHospitals, clearNearbyHospitals } = useHospitals();
  const { isLoading, error, setLoading, setError } = useLoadingState();
  const { addSymptomHistory } = useSymptomHistory();
  const { userLocation } = useLocation();

  // 地理位置
  const {
    getCurrentLocation,
    loading: locationLoading,
    error: locationError
  } = useGeolocation({
    onSuccess: (location) => {
      console.log('Location obtained:', location);
    },
    onError: (error) => {
      console.warn('Location error:', error);
    }
  });

  // 處理症狀評估提交
  const handleSymptomSubmit = useCallback(async (request: TriageRequest) => {
    setLoading(true);
    setError(null);
    clearLatestResult();
    clearNearbyHospitals();

    try {
      // 如果需要位置資訊但尚未取得，先嘗試取得位置
      if (request.include_nearby_hospitals && !request.location && userLocation) {
        request.location = userLocation;
      }

      // 執行症狀評估
      const result = await triageApi.quickTriage(request);
      setLatestResult(result);

      // 加入歷史記錄
      addSymptomHistory({
        symptom_text: request.symptom_text,
        triage_level: result.triage_level,
        timestamp: new Date().toISOString(),
        location: request.location
      });

      // 如果有附近醫院資料，直接設定
      if (result.nearby_hospitals) {
        setNearbyHospitals(result.nearby_hospitals);
      }

      // 成功提示
      toast.success('症狀評估完成');

      // 如果是緊急情況，顯示特別提醒
      if (result.triage_level === 'emergency') {
        toast.error('檢測到緊急狀況！請立即撥打119', {
          duration: 10000,
          position: 'top-center'
        });
      }

    } catch (err) {
      const message = err instanceof Error ? err.message : '評估失敗，請重試';
      setError(message);
      toast.error(message);
      console.error('Triage submission error:', err);
    } finally {
      setLoading(false);
    }
  }, [
    setLoading,
    setError,
    clearLatestResult,
    clearNearbyHospitals,
    setLatestResult,
    addSymptomHistory,
    setNearbyHospitals,
    userLocation
  ]);

  // 處理尋找附近醫院
  const handleFindHospitals = useCallback(async () => {
    if (!userLocation) {
      toast.error('請先允許位置存取');
      return;
    }

    setLoading(true);
    try {
      const hospitals = await hospitalApi.searchNearby({
        latitude: userLocation.latitude,
        longitude: userLocation.longitude,
        radius: 10000, // 10km
        limit: 20,
        departments: latestResult?.recommended_departments
      });

      // 計算距離並排序
      const hospitalsWithDistance = hospitals.map(hospital => ({
        ...hospital,
        distance: locationApi.calculateDistance(
          userLocation.latitude,
          userLocation.longitude,
          hospital.lat,
          hospital.lng
        )
      })).sort((a, b) => a.distance - b.distance);

      setNearbyHospitals(hospitalsWithDistance);
      toast.success(`找到 ${hospitals.length} 家附近醫院`);

    } catch (err) {
      const message = err instanceof Error ? err.message : '搜尋醫院失敗';
      toast.error(message);
      console.error('Hospital search error:', err);
    } finally {
      setLoading(false);
    }
  }, [userLocation, latestResult?.recommended_departments, setLoading, setNearbyHospitals]);

  // 處理緊急撥號
  const handleEmergencyCall = useCallback((number: string) => {
    emergencyApi.call(number);

    // 記錄緊急撥號事件
    console.log(`Emergency call initiated: ${number}`);
    toast.success(`正在撥打 ${number}`, {
      icon: '📞'
    });
  }, []);

  // 處理醫院選擇
  const handleHospitalSelect = useCallback((hospital: Hospital) => {
    console.log('Hospital selected:', hospital);
    toast.success(`已選擇：${hospital.name}`);
  }, []);

  // 處理醫院電話撥打
  const handleHospitalCall = useCallback((phone: string) => {
    emergencyApi.call(phone);
    toast.success(`正在撥打：${phone}`, {
      icon: '📞'
    });
  }, []);

  // 處理醫院導航
  const handleHospitalNavigate = useCallback((hospital: Hospital) => {
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${hospital.lat},${hospital.lng}&destination_place_id=${hospital.id}`;

    try {
      window.open(googleMapsUrl, '_blank');
      toast.success(`正在開啟導航至：${hospital.name}`);
    } catch (err) {
      // 如果無法開啟，複製地址到剪貼簿
      navigator.clipboard?.writeText(hospital.address);
      toast.success(`地址已複製：${hospital.address}`);
    }
  }, []);

  // 處理位置點擊
  const handleLocationClick = useCallback(() => {
    if (locationLoading) return;
    getCurrentLocation();
  }, [getCurrentLocation, locationLoading]);

  // 處理歷史記錄點擊
  const handleHistoryClick = useCallback(() => {
    navigate('/history');
  }, [navigate]);

  // 自動取得位置（首次載入）
  useEffect(() => {
    if (!userLocation && !locationError) {
      // 延遲一下再自動取得位置，避免干擾使用者
      const timer = setTimeout(() => {
        getCurrentLocation();
      }, 1000);

      return () => clearTimeout(timer);
    }
  }, [userLocation, locationError, getCurrentLocation]);

  return (
    <div className="min-h-screen relative">
      {/* 標題列 */}
      <Header
        onLocationClick={handleLocationClick}
        onHistoryClick={handleHistoryClick}
      />

      {/* 主要內容區域 */}
      <main className="container-glass py-8 space-y-8 relative z-10">
        {/* 歡迎區域 */}
        <section className="text-center space-y-4 animate-fade-in">
          <div className="inline-flex items-center gap-3 glass-card rounded-2xl px-6 py-3">
            <div className="w-3 h-3 bg-medical-500 rounded-full animate-ping"></div>
            <span className="text-medical-700 font-medium text-sm">AI 醫療助手已就緒</span>
          </div>

          <h2 className="text-2xl md:text-3xl font-bold text-gray-800 animate-fade-in animate-delay-200">
            描述您的症狀，
            <span className="text-gradient">立即獲得智能分級</span>
          </h2>

          <p className="text-gray-600 max-w-lg mx-auto leading-relaxed animate-fade-in animate-delay-300">
            基於台灣醫療標準的AI分級系統，提供即時症狀評估與就醫建議
          </p>
        </section>

        {/* 錯誤訊息 - 現代化版本 */}
        {error && (
          <div className="emergency-glass rounded-2xl p-6 animate-scale-in">
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 bg-red-500 rounded-full flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-red-800 mb-1">系統提示</h3>
                <p className="text-red-700">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* 症狀輸入表單 */}
        <section className="animate-fade-in animate-delay-100">
          <SymptomForm onSubmit={handleSymptomSubmit} />
        </section>

        {/* 分級結果 */}
        {latestResult && (
          <section className="animate-slide-up">
            <TriageResult
              result={latestResult}
              onFindHospitals={handleFindHospitals}
              onEmergencyCall={handleEmergencyCall}
            />
          </section>
        )}

        {/* 附近醫院列表 */}
        {nearbyHospitals.length > 0 && (
          <section className="animate-slide-up animate-delay-200">
            <HospitalList
              hospitals={nearbyHospitals}
              userLocation={userLocation}
              loading={isLoading}
              onHospitalSelect={handleHospitalSelect}
              onCallHospital={handleHospitalCall}
              onNavigate={handleHospitalNavigate}
            />
          </section>
        )}

        {/* 現代化載入狀態 */}
        {isLoading && !latestResult && (
          <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
            <div className="glass-card rounded-3xl p-8 text-center space-y-4">
              <div className="loading-modern mx-auto"></div>
              <div className="space-y-2">
                <h3 className="text-lg font-semibold text-gray-800">AI 正在分析您的症狀</h3>
                <p className="text-gray-600 text-sm">
                  運用深度學習模型進行醫療級評估...
                </p>
              </div>
              <div className="flex justify-center space-x-1">
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-75"></div>
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-150"></div>
              </div>
            </div>
          </div>
        )}

        {/* 功能介紹區域 (當沒有評估結果時顯示) */}
        {!latestResult && !isLoading && (
          <section className="grid md:grid-cols-3 gap-6 animate-fade-in animate-delay-500">
            <div className="glass-card rounded-2xl p-6 text-center space-y-3 hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-brand rounded-xl mx-auto flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-800">智能分級</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                AI 分析症狀嚴重程度，提供標準化醫療分級建議
              </p>
            </div>

            <div className="glass-card rounded-2xl p-6 text-center space-y-3 hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-accent rounded-xl mx-auto flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-800">就近就醫</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                即時定位附近醫療院所，提供距離與科別資訊
              </p>
            </div>

            <div className="glass-card rounded-2xl p-6 text-center space-y-3 hover:scale-105 transition-all duration-300">
              <div className="w-12 h-12 bg-gradient-to-br from-medical-400 to-medical-600 rounded-xl mx-auto flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-800">隱私保護</h3>
              <p className="text-sm text-gray-600 leading-relaxed">
                符合 PDPA 規範，不儲存個人資料，僅供即時評估
              </p>
            </div>
          </section>
        )}
      </main>

      {/* 底部安全區域 */}
      <div className="safe-bottom"></div>
    </div>
  );
};

export default HomePage;