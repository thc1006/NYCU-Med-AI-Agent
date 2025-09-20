/**
 * 單一醫院卡片元件
 */

import React from 'react';
import { MapPin, Phone, Star, Navigation, Clock, AlertCircle, ChevronRight } from 'lucide-react';
import { Hospital } from '../../types';

interface HospitalCardProps {
  hospital: Hospital;
  userLocation?: { latitude: number; longitude: number } | null;
  onSelect?: () => void;
  onCall?: () => void;
  onNavigate?: () => void;
  priority?: 'high' | 'normal';
}

const HospitalCard: React.FC<HospitalCardProps> = ({
  hospital,
  userLocation,
  onSelect,
  onCall,
  onNavigate,
  priority = 'normal'
}) => {
  // 格式化距離顯示
  const formatDistance = (distance?: number): string => {
    if (!distance) return '';
    if (distance < 1) {
      return `${Math.round(distance * 1000)}m`;
    }
    return `${distance.toFixed(1)}km`;
  };

  // 格式化評分顯示
  const formatRating = (rating?: number): string => {
    if (!rating) return '';
    return rating.toFixed(1);
  };

  // 檢查是否為推薦醫院（距離近或評分高）
  const isRecommended = (hospital.distance && hospital.distance <= 2) || (hospital.rating && hospital.rating >= 4.5);

  return (
    <div className={`
      p-4 hover:bg-gray-50 transition-colors cursor-pointer
      ${priority === 'high' ? 'bg-blue-50' : ''}
    `} onClick={onSelect}>
      <div className="flex items-start justify-between">
        {/* 左側醫院資訊 */}
        <div className="flex-1 min-w-0">
          {/* 醫院名稱和標籤 */}
          <div className="flex items-start space-x-2 mb-2">
            <h3 className="font-medium text-gray-900 truncate flex-1">
              {hospital.name}
            </h3>

            {/* 標籤 */}
            <div className="flex flex-wrap gap-1">
              {hospital.emergency_services && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                  急診
                </span>
              )}
              {isRecommended && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                  推薦
                </span>
              )}
              {priority === 'high' && (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                  就近
                </span>
              )}
            </div>
          </div>

          {/* 地址 */}
          <div className="flex items-start text-sm text-gray-600 mb-2">
            <MapPin className="w-4 h-4 mt-0.5 mr-1 flex-shrink-0" />
            <span className="truncate">{hospital.address}</span>
          </div>

          {/* 距離和評分 */}
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-2">
            {hospital.distance && (
              <div className="flex items-center">
                <Navigation className="w-4 h-4 mr-1" />
                <span>{formatDistance(hospital.distance)}</span>
              </div>
            )}

            {hospital.rating && (
              <div className="flex items-center">
                <Star className="w-4 h-4 mr-1 text-yellow-500" />
                <span>{formatRating(hospital.rating)}</span>
              </div>
            )}

            {hospital.hours && (
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                <span className="truncate">{hospital.hours}</span>
              </div>
            )}
          </div>

          {/* 科別 */}
          {hospital.departments.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {hospital.departments.slice(0, 4).map((dept, index) => (
                <span
                  key={index}
                  className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded"
                >
                  {dept}
                </span>
              ))}
              {hospital.departments.length > 4 && (
                <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-500 rounded">
                  +{hospital.departments.length - 4}
                </span>
              )}
            </div>
          )}
        </div>

        {/* 右側操作按鈕 */}
        <div className="flex flex-col space-y-2 ml-4">
          {/* 電話按鈕 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onCall?.();
            }}
            className="flex items-center justify-center px-3 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
            title={`撥打：${hospital.phone}`}
          >
            <Phone className="w-4 h-4" />
          </button>

          {/* 導航按鈕 */}
          {userLocation && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onNavigate?.();
              }}
              className="flex items-center justify-center px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              title="開啟導航"
            >
              <Navigation className="w-4 h-4" />
            </button>
          )}

          {/* 詳細資訊按鈕 */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSelect?.();
            }}
            className="flex items-center justify-center px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            title="查看詳細資訊"
          >
            <ChevronRight className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* 特殊提醒 */}
      {hospital.emergency_services && (
        <div className="mt-3 flex items-center px-3 py-2 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-4 h-4 text-red-600 mr-2" />
          <span className="text-xs text-red-800">
            24小時急診服務，建議致電確認目前狀況
          </span>
        </div>
      )}
    </div>
  );
};

export default HospitalCard;