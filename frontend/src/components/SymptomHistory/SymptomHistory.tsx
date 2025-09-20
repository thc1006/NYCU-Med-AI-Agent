/**
 * 症狀歷史記錄元件
 */

import React, { useState } from 'react';
import { History, Trash2, Search, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { useSymptomHistory } from '../../stores/useAppStore';
import { SymptomHistory as SymptomHistoryType, TRIAGE_LEVEL_CONFIG, TriageLevel } from '../../types';
import SymptomHistoryItem from './SymptomHistoryItem';

interface SymptomHistoryProps {
  onHistorySelect?: (history: SymptomHistoryType) => void;
}

const SymptomHistory: React.FC<SymptomHistoryProps> = ({ onHistorySelect }) => {
  const { symptomHistory, clearSymptomHistory, removeSymptomHistory } = useSymptomHistory();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest'>('newest');
  const [showFilters, setShowFilters] = useState(false);

  // 過濾和排序歷史記錄
  const filteredHistory = React.useMemo(() => {
    let filtered = symptomHistory.filter(history => {
      // 搜尋篩選
      if (searchTerm && !history.symptom_text.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }

      // 等級篩選
      if (filterLevel !== 'all' && history.triage_level !== filterLevel) {
        return false;
      }

      return true;
    });

    // 排序
    filtered.sort((a, b) => {
      const dateA = new Date(a.timestamp).getTime();
      const dateB = new Date(b.timestamp).getTime();

      return sortBy === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return filtered;
  }, [symptomHistory, searchTerm, filterLevel, sortBy]);

  // 取得等級統計
  const levelStats = React.useMemo(() => {
    const stats: Record<string, number> = {};
    symptomHistory.forEach(history => {
      stats[history.triage_level] = (stats[history.triage_level] || 0) + 1;
    });
    return stats;
  }, [symptomHistory]);

  // 格式化時間
  const formatDate = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return '今天 ' + date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return '昨天 ' + date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays < 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString('zh-TW');
    }
  };

  if (symptomHistory.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <History className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          尚無症狀查詢歷史
        </h3>
        <p className="text-gray-600">
          當您使用症狀評估功能後，歷史記錄會顯示在這裡
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* 標題和統計 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <History className="w-5 h-5 mr-2 text-blue-500" />
              症狀查詢歷史
            </h2>
            <p className="text-sm text-gray-600">
              共 {symptomHistory.length} 筆記錄
              {filteredHistory.length !== symptomHistory.length && (
                <span>，顯示 {filteredHistory.length} 筆</span>
              )}
            </p>
          </div>

          {/* 清除按鈕 */}
          <button
            onClick={clearSymptomHistory}
            className="flex items-center px-3 py-2 text-sm text-red-600 hover:text-red-800 transition-colors"
            title="清除所有歷史記錄"
          >
            <Trash2 className="w-4 h-4 mr-1" />
            清除全部
          </button>
        </div>

        {/* 搜尋框 */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="搜尋症狀..."
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 篩選和排序 */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center text-sm text-gray-600 hover:text-gray-800 transition-colors"
          >
            <Filter className="w-4 h-4 mr-1" />
            篩選
            {showFilters ? (
              <ChevronUp className="w-4 h-4 ml-1" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-1" />
            )}
          </button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest')}
            className="text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="newest">最新優先</option>
            <option value="oldest">最舊優先</option>
          </select>
        </div>

        {/* 篩選選項 */}
        {showFilters && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setFilterLevel('all')}
                className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                  filterLevel === 'all'
                    ? 'bg-blue-500 text-white border-blue-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                全部 ({symptomHistory.length})
              </button>

              {Object.entries(levelStats).map(([level, count]) => {
                const config = TRIAGE_LEVEL_CONFIG[level as TriageLevel];
                if (!config) return null;

                return (
                  <button
                    key={level}
                    onClick={() => setFilterLevel(level)}
                    className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                      filterLevel === level
                        ? `bg-${config.color}-500 text-white border-${config.color}-500`
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {config.label} ({count})
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* 歷史記錄列表 */}
      <div className="divide-y divide-gray-200">
        {filteredHistory.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <Search className="w-8 h-8 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-600">找不到符合條件的記錄</p>
          </div>
        ) : (
          filteredHistory.map((history) => (
            <SymptomHistoryItem
              key={history.id}
              history={history}
              onSelect={() => onHistorySelect?.(history)}
              onDelete={() => removeSymptomHistory(history.id)}
              formatDate={formatDate}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default SymptomHistory;