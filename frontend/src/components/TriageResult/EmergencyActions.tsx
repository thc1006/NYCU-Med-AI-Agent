/**
 * 緊急處理動作元件
 */

import React from 'react';
import { Phone, AlertTriangle, Zap } from 'lucide-react';
import { EMERGENCY_NUMBERS } from '../../types';

interface EmergencyActionsProps {
  emergencyNumbers: string[];
  onCall?: (number: string) => void;
  isEmergency?: boolean;
}

const EmergencyActions: React.FC<EmergencyActionsProps> = ({
  emergencyNumbers,
  onCall,
  isEmergency = false
}) => {
  // 取得緊急電話詳細資訊
  const getEmergencyContactInfo = (number: string) => {
    return EMERGENCY_NUMBERS.find(contact => contact.number === number) || {
      number,
      label: number,
      description: '緊急聯絡',
      icon: '📞'
    };
  };

  // 處理撥號
  const handleCall = (number: string) => {
    onCall?.(number);
  };

  if (!emergencyNumbers || emergencyNumbers.length === 0) {
    return null;
  }

  return (
    <div className={`
      rounded-lg p-4 border-2
      ${isEmergency
        ? 'bg-red-50 border-red-300'
        : 'bg-orange-50 border-orange-300'
      }
    `}>
      {/* 緊急標題 */}
      <div className="flex items-center mb-3">
        {isEmergency ? (
          <Zap className="w-5 h-5 text-red-600 mr-2" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-orange-600 mr-2" />
        )}
        <h3 className={`font-bold text-sm ${
          isEmergency ? 'text-red-800' : 'text-orange-800'
        }`}>
          {isEmergency ? '🚨 立即撥打緊急電話' : '⚠️ 建議盡快聯絡'}
        </h3>
      </div>

      {/* 緊急電話按鈕群組 */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {emergencyNumbers.map((number) => {
          const contactInfo = getEmergencyContactInfo(number);
          return (
            <button
              key={number}
              onClick={() => handleCall(number)}
              className={`
                flex flex-col items-center justify-center p-3 rounded-lg border-2 transition-all duration-200 hover:shadow-md
                ${isEmergency
                  ? 'bg-red-500 hover:bg-red-600 border-red-600 text-white'
                  : 'bg-orange-500 hover:bg-orange-600 border-orange-600 text-white'
                }
                focus:outline-none focus:ring-4 focus:ring-opacity-50
                ${isEmergency ? 'focus:ring-red-300' : 'focus:ring-orange-300'}
              `}
            >
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-lg">{contactInfo.icon}</span>
                <Phone className="w-4 h-4" />
              </div>
              <div className="text-center">
                <div className="font-bold text-lg">{number}</div>
                <div className="text-xs opacity-90">{contactInfo.label}</div>
              </div>
            </button>
          );
        })}
      </div>

      {/* 緊急提醒文字 */}
      <div className={`mt-3 text-xs ${
        isEmergency ? 'text-red-800' : 'text-orange-800'
      }`}>
        {isEmergency ? (
          <p className="font-medium">
            ⚡ 這是緊急狀況！請立即撥打上述任一號碼尋求協助。
          </p>
        ) : (
          <p>
            📱 建議您盡快聯絡醫療單位或前往就近醫院。
          </p>
        )}
      </div>

      {/* 撥號提示 */}
      <div className="mt-2 text-xs text-gray-600 bg-white bg-opacity-50 rounded p-2">
        <p>
          💡 <strong>撥號提示：</strong>
          在手機上會直接開啟撥號程式，在電腦上會顯示電話號碼供您使用其他裝置撥打。
        </p>
      </div>
    </div>
  );
};

export default EmergencyActions;