/**
 * 額外資訊輸入表單元件
 */

import React from 'react';
import { User, Clock, Pill, AlertCircle } from 'lucide-react';
import { SymptomQuery } from '../../types';

interface AdditionalInfoFormProps {
  query: SymptomQuery;
  onChange: (query: Partial<SymptomQuery>) => void;
  disabled?: boolean;
}

const AdditionalInfoForm: React.FC<AdditionalInfoFormProps> = ({
  query,
  onChange,
  disabled = false
}) => {
  // 處理年齡變更
  const handleAgeChange = (value: string) => {
    const age = value === '' ? undefined : parseInt(value, 10);
    onChange({ age });
  };

  // 處理症狀持續時間變更
  const handleDurationChange = (value: string) => {
    const duration = value === '' ? undefined : parseInt(value, 10);
    onChange({ duration_hours: duration });
  };

  // 處理藥物清單變更
  const handleMedicationsChange = (value: string) => {
    const medications = value
      .split(/[,，\n]/)
      .map(med => med.trim())
      .filter(med => med.length > 0);
    onChange({ medications });
  };

  return (
    <div className="bg-gray-50 rounded-lg p-4 space-y-4">
      <h3 className="text-sm font-medium text-gray-700 flex items-center">
        <User className="w-4 h-4 mr-1" />
        詳細資訊
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* 年齡 */}
        <div>
          <label htmlFor="age" className="block text-sm text-gray-600 mb-1">
            年齡
          </label>
          <input
            type="number"
            id="age"
            value={query.age || ''}
            onChange={(e) => handleAgeChange(e.target.value)}
            placeholder="請輸入年齡"
            min="0"
            max="150"
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
            disabled={disabled}
          />
        </div>

        {/* 性別 */}
        <div>
          <label htmlFor="gender" className="block text-sm text-gray-600 mb-1">
            性別
          </label>
          <select
            id="gender"
            value={query.gender || ''}
            onChange={(e) => onChange({ gender: e.target.value || undefined })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
            disabled={disabled}
          >
            <option value="">請選擇</option>
            <option value="M">男性</option>
            <option value="F">女性</option>
            <option value="O">其他</option>
          </select>
        </div>
      </div>

      {/* 症狀持續時間 */}
      <div>
        <label htmlFor="duration" className="block text-sm text-gray-600 mb-1 flex items-center">
          <Clock className="w-4 h-4 mr-1" />
          症狀持續時間（小時）
        </label>
        <input
          type="number"
          id="duration"
          value={query.duration_hours || ''}
          onChange={(e) => handleDurationChange(e.target.value)}
          placeholder="例如：2（持續2小時）"
          min="0"
          max="8760"
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500"
          disabled={disabled}
        />
        <p className="mt-1 text-xs text-gray-500">
          症狀從什麼時候開始？輸入大約的小時數
        </p>
      </div>

      {/* 慢性疾病 */}
      <div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={query.has_chronic_disease}
            onChange={(e) => onChange({ has_chronic_disease: e.target.checked })}
            className="rounded border-gray-300 text-red-600 focus:ring-red-500"
            disabled={disabled}
          />
          <span className="text-sm text-gray-700 flex items-center">
            <AlertCircle className="w-4 h-4 mr-1" />
            我有慢性疾病（糖尿病、高血壓、心臟病等）
          </span>
        </label>
      </div>

      {/* 目前用藥 */}
      <div>
        <label htmlFor="medications" className="block text-sm text-gray-600 mb-1 flex items-center">
          <Pill className="w-4 h-4 mr-1" />
          目前服用的藥物
        </label>
        <textarea
          id="medications"
          value={query.medications.join('，')}
          onChange={(e) => handleMedicationsChange(e.target.value)}
          placeholder="例如：阿斯匹靈，血壓藥，維他命..."
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-red-500 focus:border-red-500 resize-none"
          disabled={disabled}
        />
        <p className="mt-1 text-xs text-gray-500">
          請用逗號、中文逗號或換行分隔多個藥物
        </p>
      </div>

      {/* 資訊提醒 */}
      <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
        <p className="text-xs text-blue-800">
          <span className="font-medium">💡 提示：</span>
          提供這些資訊可以幫助系統給出更準確的建議，但都不是必填項目。
        </p>
      </div>
    </div>
  );
};

export default AdditionalInfoForm;