/**
 * 醫院篩選器元件
 */

import React from 'react';
import { X, Sliders } from 'lucide-react';

interface FilterOptions {
  departments: string[];
  emergencyOnly: boolean;
  maxDistance: number;
  sortBy: 'distance' | 'rating' | 'name';
}

interface HospitalFiltersProps {
  filters: FilterOptions;
  allDepartments: string[];
  onChange: (filters: Partial<FilterOptions>) => void;
  onClear: () => void;
}

const HospitalFilters: React.FC<HospitalFiltersProps> = ({
  filters,
  allDepartments,
  onChange,
  onClear
}) => {
  // 處理科別選擇
  const handleDepartmentToggle = (department: string) => {
    const newDepartments = filters.departments.includes(department)
      ? filters.departments.filter(d => d !== department)
      : [...filters.departments, department];

    onChange({ departments: newDepartments });
  };

  // 處理距離變更
  const handleDistanceChange = (distance: number) => {
    onChange({ maxDistance: distance });
  };

  // 處理排序變更
  const handleSortChange = (sortBy: FilterOptions['sortBy']) => {
    onChange({ sortBy });
  };

  // 檢查是否有活動篩選
  const hasActiveFilters =
    filters.departments.length > 0 ||
    filters.emergencyOnly ||
    filters.maxDistance !== 10 ||
    filters.sortBy !== 'distance';

  return (
    <div className="border-b border-gray-200 bg-gray-50">
      <div className="px-6 py-4 space-y-4">
        {/* 標題和清除按鈕 */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium text-gray-700 flex items-center">
            <Sliders className="w-4 h-4 mr-1" />
            篩選條件
          </h3>
          {hasActiveFilters && (
            <button
              onClick={onClear}
              className="flex items-center text-xs text-gray-500 hover:text-gray-700 transition-colors"
            >
              <X className="w-3 h-3 mr-1" />
              清除全部
            </button>
          )}
        </div>

        {/* 急診篩選 */}
        <div>
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={filters.emergencyOnly}
              onChange={(e) => onChange({ emergencyOnly: e.target.checked })}
              className="rounded border-gray-300 text-red-600 focus:ring-red-500"
            />
            <span className="text-sm text-gray-700">只顯示有急診的醫院</span>
          </label>
        </div>

        {/* 距離篩選 */}
        <div>
          <label className="block text-sm text-gray-700 mb-2">
            最大距離：{filters.maxDistance}km
          </label>
          <input
            type="range"
            min="1"
            max="20"
            step="1"
            value={filters.maxDistance}
            onChange={(e) => handleDistanceChange(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1km</span>
            <span>10km</span>
            <span>20km</span>
          </div>
        </div>

        {/* 排序方式 */}
        <div>
          <label className="block text-sm text-gray-700 mb-2">排序方式</label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { value: 'distance', label: '距離' },
              { value: 'rating', label: '評分' },
              { value: 'name', label: '名稱' }
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => handleSortChange(option.value as FilterOptions['sortBy'])}
                className={`
                  px-3 py-2 text-xs rounded-lg border transition-colors
                  ${filters.sortBy === option.value
                    ? 'bg-red-500 text-white border-red-500'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                  }
                `}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* 科別篩選 */}
        {allDepartments.length > 0 && (
          <div>
            <label className="block text-sm text-gray-700 mb-2">
              科別篩選 ({filters.departments.length}個已選)
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 max-h-32 overflow-y-auto">
              {allDepartments.map((department) => (
                <button
                  key={department}
                  onClick={() => handleDepartmentToggle(department)}
                  className={`
                    px-2 py-1 text-xs rounded border transition-colors text-left
                    ${filters.departments.includes(department)
                      ? 'bg-blue-500 text-white border-blue-500'
                      : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }
                  `}
                >
                  {department}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* 篩選結果摘要 */}
        {hasActiveFilters && (
          <div className="pt-2 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {filters.emergencyOnly && (
                <span className="inline-flex items-center px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                  僅急診
                  <button
                    onClick={() => onChange({ emergencyOnly: false })}
                    className="ml-1 text-red-600 hover:text-red-800"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}

              {filters.maxDistance !== 10 && (
                <span className="inline-flex items-center px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                  ≤{filters.maxDistance}km
                  <button
                    onClick={() => onChange({ maxDistance: 10 })}
                    className="ml-1 text-blue-600 hover:text-blue-800"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              )}

              {filters.departments.map((dept) => (
                <span
                  key={dept}
                  className="inline-flex items-center px-2 py-1 text-xs bg-green-100 text-green-800 rounded"
                >
                  {dept}
                  <button
                    onClick={() => handleDepartmentToggle(dept)}
                    className="ml-1 text-green-600 hover:text-green-800"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HospitalFilters;