/**
 * 快速症狀選擇元件
 */

import React, { useState } from 'react';
import { COMMON_SYMPTOMS } from '../../types';

interface QuickSymptomSelectProps {
  onSymptomSelect: (symptom: string) => void;
  disabled?: boolean;
}

const QuickSymptomSelect: React.FC<QuickSymptomSelectProps> = ({
  onSymptomSelect,
  disabled = false
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('全部');

  // 取得症狀分類
  const categories = ['全部', ...Array.from(new Set(COMMON_SYMPTOMS.map(s => s.category)))];

  // 根據分類篩選症狀
  const filteredSymptoms = selectedCategory === '全部'
    ? COMMON_SYMPTOMS
    : COMMON_SYMPTOMS.filter(s => s.category === selectedCategory);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">
          常見症狀快選
        </span>

        {/* 分類篩選 */}
        <div className="flex space-x-1">
          {categories.map((category) => (
            <button
              key={category}
              type="button"
              onClick={() => setSelectedCategory(category)}
              disabled={disabled}
              className={`
                px-2 py-1 text-xs rounded-full border transition-colors
                ${selectedCategory === category
                  ? 'bg-red-500 text-white border-red-500'
                  : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                }
                ${category === '緊急' ? 'text-red-600 border-red-300' : ''}
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      {/* 症狀選項 */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {filteredSymptoms.map((symptom) => (
          <button
            key={symptom.value}
            type="button"
            onClick={() => onSymptomSelect(symptom.value)}
            disabled={disabled}
            className={`
              flex items-center justify-center px-3 py-2 text-sm border rounded-lg transition-all duration-200
              ${symptom.category === '緊急'
                ? 'border-red-200 text-red-700 bg-red-50 hover:bg-red-100 hover:border-red-300'
                : 'border-gray-200 text-gray-700 bg-gray-50 hover:bg-gray-100 hover:border-gray-300'
              }
              disabled:opacity-50 disabled:cursor-not-allowed
              hover:shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-opacity-50
            `}
            title={`點擊新增「${symptom.label}」到症狀描述`}
          >
            <span className="mr-1">{symptom.icon}</span>
            <span>{symptom.label}</span>
          </button>
        ))}
      </div>

      {filteredSymptoms.length === 0 && (
        <p className="text-center text-sm text-gray-500 py-4">
          此分類沒有症狀選項
        </p>
      )}

      {/* 緊急症狀提醒 */}
      {selectedCategory === '緊急' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-xs text-red-800">
            <span className="font-medium">🚨 緊急症狀提醒：</span>
            如果您有以上任何症狀，建議立即撥打 119 或前往最近的急診室。
          </p>
        </div>
      )}
    </div>
  );
};

export default QuickSymptomSelect;