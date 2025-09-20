/**
 * 醫院列表顯示元件
 */

import React, { useState } from 'react';
import { MapPin, Clock, Navigation, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { Hospital } from '../../types';
import HospitalCard from './HospitalCard';
import HospitalFilters from './HospitalFilters';

interface HospitalListProps {
  hospitals: Hospital[];
  userLocation?: { latitude: number; longitude: number } | null;
  loading?: boolean;
  onHospitalSelect?: (hospital: Hospital) => void;
  onCallHospital?: (phone: string) => void;
  onNavigate?: (hospital: Hospital) => void;
}

interface FilterOptions {
  departments: string[];
  emergencyOnly: boolean;
  maxDistance: number;
  sortBy: 'distance' | 'rating' | 'name';
}

const HospitalList: React.FC<HospitalListProps> = ({
  hospitals,
  userLocation,
  loading = false,
  onHospitalSelect,
  onCallHospital,
  onNavigate
}) => {
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterOptions>({
    departments: [],
    emergencyOnly: false,
    maxDistance: 10,
    sortBy: 'distance'
  });

  // 取得所有可用科別
  const allDepartments = Array.from(
    new Set(hospitals.flatMap(h => h.departments))
  ).sort();

  // 過濾和排序醫院
  const filteredHospitals = React.useMemo(() => {
    let filtered = hospitals.filter(hospital => {
      // 科別篩選
      if (filters.departments.length > 0) {
        const hasMatchingDept = filters.departments.some(dept =>
          hospital.departments.some(hDept =>
            hDept.toLowerCase().includes(dept.toLowerCase())
          )
        );
        if (!hasMatchingDept) return false;
      }

      // 急診篩選
      if (filters.emergencyOnly && !hospital.emergency_services) {
        return false;
      }

      // 距離篩選
      if (hospital.distance && hospital.distance > filters.maxDistance) {
        return false;
      }

      return true;
    });

    // 排序
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'distance':
          return (a.distance || 999) - (b.distance || 999);
        case 'rating':
          return (b.rating || 0) - (a.rating || 0);
        case 'name':
          return a.name.localeCompare(b.name, 'zh-TW');
        default:
          return 0;
      }
    });

    return filtered;
  }, [hospitals, filters]);

  // 處理篩選變更
  const handleFilterChange = (newFilters: Partial<FilterOptions>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // 清除篩選
  const clearFilters = () => {
    setFilters({
      departments: [],
      emergencyOnly: false,
      maxDistance: 10,
      sortBy: 'distance'
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="animate-pulse space-y-4">
          <div className="flex items-center justify-between">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
          {[...Array(3)].map((_, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-4">
              <div className="space-y-3">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200">
      {/* 標題和統計 */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <MapPin className="w-5 h-5 mr-2 text-red-500" />
              附近醫院
            </h2>
            <p className="text-sm text-gray-600">
              找到 {filteredHospitals.length} 家醫院
              {hospitals.length !== filteredHospitals.length && (
                <span>（共 {hospitals.length} 家）</span>
              )}
            </p>
          </div>

          {/* 篩選按鈕 */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Filter className="w-4 h-4 mr-1" />
            篩選
            {showFilters ? (
              <ChevronUp className="w-4 h-4 ml-1" />
            ) : (
              <ChevronDown className="w-4 h-4 ml-1" />
            )}
          </button>
        </div>
      </div>

      {/* 篩選器 */}
      {showFilters && (
        <HospitalFilters
          filters={filters}
          allDepartments={allDepartments}
          onChange={handleFilterChange}
          onClear={clearFilters}
        />
      )}

      {/* 醫院列表 */}
      <div className="divide-y divide-gray-200">
        {filteredHospitals.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <MapPin className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              沒有找到符合條件的醫院
            </h3>
            <p className="text-gray-600 mb-4">
              請嘗試調整篩選條件或擴大搜尋範圍
            </p>
            <button
              onClick={clearFilters}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
            >
              清除篩選條件
            </button>
          </div>
        ) : (
          filteredHospitals.map((hospital, index) => (
            <HospitalCard
              key={hospital.id}
              hospital={hospital}
              userLocation={userLocation}
              onSelect={() => onHospitalSelect?.(hospital)}
              onCall={() => onCallHospital?.(hospital.phone)}
              onNavigate={() => onNavigate?.(hospital)}
              priority={index < 3 ? 'high' : 'normal'}
            />
          ))
        )}
      </div>

      {/* 底部資訊 */}
      {filteredHospitals.length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <div className="flex items-center">
              <Navigation className="w-3 h-3 mr-1" />
              <span>距離以直線距離計算</span>
            </div>
            <div className="flex items-center">
              <Clock className="w-3 h-3 mr-1" />
              <span>建議致電確認營業時間</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HospitalList;