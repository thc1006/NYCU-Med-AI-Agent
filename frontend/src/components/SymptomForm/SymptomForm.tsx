/**
 * 症狀輸入表單元件
 */

import React, { useState, useCallback } from 'react';
import { Search, Send, AlertTriangle, User } from 'lucide-react';
import { useSymptomQuery, useLoadingState } from '../../stores/useAppStore';
import { TriageRequest } from '../../types';
import QuickSymptomSelect from './QuickSymptomSelect';
import AdditionalInfoForm from './AdditionalInfoForm';

interface SymptomFormProps {
  onSubmit: (request: TriageRequest) => Promise<void>;
}

const SymptomForm: React.FC<SymptomFormProps> = ({ onSubmit }) => {
  const { currentQuery, setCurrentQuery } = useSymptomQuery();
  const { isLoading } = useLoadingState();

  const [showAdditionalInfo, setShowAdditionalInfo] = useState(false);
  const [isFormValid, setIsFormValid] = useState(false);

  // 檢查表單是否有效
  const validateForm = useCallback(() => {
    const isValid = currentQuery.symptom_text.trim().length >= 2;
    setIsFormValid(isValid);
    return isValid;
  }, [currentQuery.symptom_text]);

  // 症狀文字變更處理
  const handleSymptomTextChange = (value: string) => {
    setCurrentQuery({ symptom_text: value });
    validateForm();
  };

  // 快速選擇症狀
  const handleQuickSymptomSelect = (symptom: string) => {
    const currentText = currentQuery.symptom_text.trim();
    const newText = currentText
      ? `${currentText}，${symptom}`
      : symptom;

    handleSymptomTextChange(newText);
  };

  // 提交表單
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm() || isLoading) {
      return;
    }

    try {
      const request: TriageRequest = {
        ...currentQuery,
        include_nearby_hospitals: true
      };

      await onSubmit(request);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  // 清除表單
  const handleClear = () => {
    setCurrentQuery({
      symptom_text: '',
      age: undefined,
      gender: undefined,
      duration_hours: undefined,
      has_chronic_disease: false,
      medications: []
    });
    setShowAdditionalInfo(false);
    setIsFormValid(false);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 主要症狀輸入 */}
        <div>
          <label htmlFor="symptom-text" className="block text-sm font-medium text-gray-700 mb-2">
            <Search className="inline w-4 h-4 mr-1" />
            請描述您的症狀
          </label>
          <div className="relative">
            <textarea
              id="symptom-text"
              value={currentQuery.symptom_text}
              onChange={(e) => handleSymptomTextChange(e.target.value)}
              placeholder="例如：頭痛、發燒、咳嗽..."
              className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 resize-none"
              rows={3}
              maxLength={500}
              disabled={isLoading}
            />
            <div className="absolute bottom-2 right-2 text-xs text-gray-500">
              {currentQuery.symptom_text.length}/500
            </div>
          </div>
          {currentQuery.symptom_text.length > 0 && currentQuery.symptom_text.length < 2 && (
            <p className="mt-1 text-xs text-orange-600">
              請至少輸入 2 個字元
            </p>
          )}
        </div>

        {/* 快速症狀選擇 */}
        <QuickSymptomSelect
          onSymptomSelect={handleQuickSymptomSelect}
          disabled={isLoading}
        />

        {/* 其他資訊切換 */}
        <div className="border-t border-gray-100 pt-4">
          <button
            type="button"
            onClick={() => setShowAdditionalInfo(!showAdditionalInfo)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors"
            disabled={isLoading}
          >
            <User className="w-4 h-4 mr-1" />
            {showAdditionalInfo ? '隱藏' : '提供'}額外資訊（可提高評估準確度）
            <span className="ml-1 text-xs">
              {showAdditionalInfo ? '▲' : '▼'}
            </span>
          </button>
        </div>

        {/* 額外資訊表單 */}
        {showAdditionalInfo && (
          <AdditionalInfoForm
            query={currentQuery}
            onChange={setCurrentQuery}
            disabled={isLoading}
          />
        )}

        {/* 提交按鈕群組 */}
        <div className="flex space-x-3 pt-4">
          <button
            type="submit"
            disabled={!isFormValid || isLoading}
            className={`
              flex-1 flex items-center justify-center px-4 py-3 rounded-lg font-medium text-white transition-all duration-200
              ${isFormValid && !isLoading
                ? 'bg-red-500 hover:bg-red-600 hover:shadow-md'
                : 'bg-gray-300 cursor-not-allowed'
              }
            `}
          >
            {isLoading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                評估中...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                開始評估
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handleClear}
            disabled={isLoading}
            className="px-4 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            清除
          </button>
        </div>

        {/* 免責聲明 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start">
            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-xs text-yellow-800">
              <p className="font-medium mb-1">重要提醒：</p>
              <ul className="space-y-1">
                <li>• 本系統僅供症狀分級參考，不可取代專業醫療診斷</li>
                <li>• 如有生命危險症狀，請立即撥打 119</li>
                <li>• 慢性疾病患者請遵循醫師指示</li>
              </ul>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
};

export default SymptomForm;