/**
 * 分級結果顯示元件
 */

import React from 'react';
import { AlertTriangle, Clock, MapPin, Info } from 'lucide-react';
import { TriageResponse, TRIAGE_LEVEL_CONFIG, TriageLevel } from '../../types';
import EmergencyActions from './EmergencyActions';

interface TriageResultProps {
  result: TriageResponse;
  onFindHospitals?: () => void;
  onEmergencyCall?: (number: string) => void;
}

const TriageResult: React.FC<TriageResultProps> = ({
  result,
  onFindHospitals,
  onEmergencyCall
}) => {
  const levelConfig = TRIAGE_LEVEL_CONFIG[result.triage_level as TriageLevel] ||
    TRIAGE_LEVEL_CONFIG[TriageLevel.OUTPATIENT];

  const isEmergency = result.triage_level === TriageLevel.EMERGENCY;
  const isUrgent = result.triage_level === TriageLevel.URGENT;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* 分級等級標題 */}
      <div className={`${levelConfig.bgColor} ${levelConfig.borderColor} border-b px-6 py-4`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{levelConfig.icon}</span>
            <div>
              <h2 className={`text-lg font-bold ${levelConfig.textColor}`}>
                {levelConfig.label}等級
              </h2>
              {result.confidence_score && (
                <p className="text-sm text-gray-600">
                  信心度：{Math.round(result.confidence_score * 100)}%
                </p>
              )}
            </div>
          </div>

          {result.estimated_wait_time && (
            <div className="flex items-center text-sm text-gray-600">
              <Clock className="w-4 h-4 mr-1" />
              預估等候：{result.estimated_wait_time}
            </div>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 緊急處理 */}
        {(isEmergency || isUrgent) && (
          <EmergencyActions
            emergencyNumbers={result.emergency_numbers}
            onCall={onEmergencyCall}
            isEmergency={isEmergency}
          />
        )}

        {/* 主要建議 */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
            <Info className="w-4 h-4 mr-1" />
            醫療建議
          </h3>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-gray-800">{result.advice}</p>
          </div>
        </div>

        {/* 檢測到的症狀 */}
        {result.detected_symptoms.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              檢測到的症狀
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.detected_symptoms.map((symptom, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800"
                >
                  {symptom}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 建議科別 */}
        {result.recommended_departments && result.recommended_departments.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              建議科別
            </h3>
            <div className="flex flex-wrap gap-2">
              {result.recommended_departments.map((dept, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800"
                >
                  🏥 {dept}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 下一步驟 */}
        {result.next_steps.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">
              建議處理步驟
            </h3>
            <div className="space-y-2">
              {result.next_steps.map((step, index) => (
                <div key={index} className="flex items-start space-x-2">
                  <div className={`
                    flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium text-white
                    ${isEmergency ? 'bg-red-500' : isUrgent ? 'bg-orange-500' : 'bg-blue-500'}
                  `}>
                    {index + 1}
                  </div>
                  <p className="text-sm text-gray-800 flex-1">{step}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 尋找附近醫院按鈕 */}
        {!isEmergency && onFindHospitals && (
          <div className="pt-4 border-t border-gray-100">
            <button
              onClick={onFindHospitals}
              className="w-full flex items-center justify-center px-4 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <MapPin className="w-4 h-4 mr-2" />
              尋找附近醫院
            </button>
          </div>
        )}

        {/* 免責聲明 */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <div className="flex items-start">
            <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-xs text-yellow-800">
              <p className="font-medium mb-1">免責聲明：</p>
              <p>{result.disclaimer}</p>
            </div>
          </div>
        </div>

        {/* 評估資訊 */}
        <div className="text-xs text-gray-500 flex items-center justify-between border-t border-gray-100 pt-4">
          <span>評估ID: {result.request_id}</span>
          <span>{new Date(result.timestamp).toLocaleString('zh-TW')}</span>
        </div>
      </div>
    </div>
  );
};

export default TriageResult;