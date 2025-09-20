/**
 * 歷史記錄頁面元件
 */

import React, { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

import SymptomHistory from '../components/SymptomHistory/SymptomHistory';
import { useSymptomQuery } from '../stores/useAppStore';
import { SymptomHistory as SymptomHistoryType } from '../types';

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentQuery } = useSymptomQuery();

  // 處理歷史記錄選擇
  const handleHistorySelect = useCallback((history: SymptomHistoryType) => {
    // 將歷史記錄的症狀文字填入當前查詢
    setCurrentQuery({
      symptom_text: history.symptom_text,
      age: undefined,
      gender: undefined,
      duration_hours: undefined,
      has_chronic_disease: false,
      medications: []
    });

    // 顯示提示並導航回首頁
    toast.success('已將症狀填入表單');
    navigate('/');
  }, [setCurrentQuery, navigate]);

  // 處理返回首頁
  const handleBack = useCallback(() => {
    navigate('/');
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 標題列 */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-md mx-auto px-4 py-3">
          <div className="flex items-center">
            <button
              onClick={handleBack}
              className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-gray-100 transition-colors mr-3"
              title="返回首頁"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600" />
            </button>
            <div>
              <h1 className="text-lg font-bold text-gray-900">
                症狀查詢歷史
              </h1>
              <p className="text-xs text-gray-500">
                點擊記錄可重新填入症狀
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* 主要內容 */}
      <main className="container-responsive py-6">
        <div className="animate-fade-in">
          <SymptomHistory onHistorySelect={handleHistorySelect} />
        </div>
      </main>

      {/* 底部安全區域 */}
      <div className="safe-bottom"></div>
    </div>
  );
};

export default HistoryPage;