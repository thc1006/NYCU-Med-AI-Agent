/**
 * 單一症狀歷史記錄項目元件
 */

import React from 'react';
import { Clock, MapPin, Trash2, ChevronRight } from 'lucide-react';
import { SymptomHistory, TRIAGE_LEVEL_CONFIG, TriageLevel } from '../../types';

interface SymptomHistoryItemProps {
  history: SymptomHistory;
  onSelect: () => void;
  onDelete: () => void;
  formatDate: (timestamp: string) => string;
}

const SymptomHistoryItem: React.FC<SymptomHistoryItemProps> = ({
  history,
  onSelect,
  onDelete,
  formatDate
}) => {
  const levelConfig = TRIAGE_LEVEL_CONFIG[history.triage_level as TriageLevel] ||
    TRIAGE_LEVEL_CONFIG[TriageLevel.OUTPATIENT];

  // 處理刪除點擊
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('確定要刪除這筆記錄嗎？')) {
      onDelete();
    }
  };

  return (
    <div
      className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        {/* 左側內容 */}
        <div className="flex-1 min-w-0">
          {/* 症狀文字 */}
          <div className="flex items-start space-x-3 mb-2">
            <span className="text-lg">{levelConfig.icon}</span>
            <div className="flex-1 min-w-0">
              <h3 className="font-medium text-gray-900 line-clamp-2">
                {history.symptom_text}
              </h3>
              <div className="flex items-center mt-1">
                <span className={`
                  inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
                  ${levelConfig.bgColor} ${levelConfig.textColor}
                `}>
                  {levelConfig.label}
                </span>
              </div>
            </div>
          </div>

          {/* 時間和位置資訊 */}
          <div className="flex items-center space-x-4 text-sm text-gray-500">
            <div className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              <span>{formatDate(history.timestamp)}</span>
            </div>

            {history.location && (
              <div className="flex items-center">
                <MapPin className="w-4 h-4 mr-1" />
                <span>
                  已定位 ({history.location.latitude.toFixed(4)}, {history.location.longitude.toFixed(4)})
                </span>
              </div>
            )}
          </div>
        </div>

        {/* 右側操作按鈕 */}
        <div className="flex items-center space-x-2 ml-4">
          {/* 刪除按鈕 */}
          <button
            onClick={handleDelete}
            className="p-1 text-gray-400 hover:text-red-600 transition-colors"
            title="刪除此記錄"
          >
            <Trash2 className="w-4 h-4" />
          </button>

          {/* 查看詳細按鈕 */}
          <button
            onClick={onSelect}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="查看詳細資訊"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default SymptomHistoryItem;