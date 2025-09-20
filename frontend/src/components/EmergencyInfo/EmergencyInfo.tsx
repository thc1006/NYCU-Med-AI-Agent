/**
 * 緊急資訊元件 - 現代化玻璃擬態設計
 */

import React, { useState } from 'react';
import { AlertTriangle, Phone, MapPin, Clock, Shield, ChevronRight, Heart, Activity, Siren } from 'lucide-react';
import { EMERGENCY_NUMBERS } from '../../types';

const EmergencyInfo: React.FC = () => {
  const [hoveredCard, setHoveredCard] = useState<string | null>(null);

  // 額外的緊急資源
  const additionalResources = [
    { number: '113', label: '婦幼保護', description: '家暴及性侵害防治', icon: '👨‍👩‍👧' },
    { number: '165', label: '反詐騙', description: '詐騙案件諮詢', icon: '🛡️' },
    { number: '1925', label: '安心專線', description: '24小時心理諮詢', icon: '💚' },
    { number: '1922', label: '防疫專線', description: 'COVID-19疫情諮詢', icon: '😷' }
  ];

  // 緊急情況指引
  const emergencyGuides = [
    {
      title: '心臟停止',
      icon: Heart,
      color: 'red',
      steps: ['立即撥打119', '開始CPR心肺復甦', '使用AED電擊器', '持續急救直到救護人員抵達']
    },
    {
      title: '中風症狀',
      icon: Activity,
      color: 'orange',
      steps: ['F.A.S.T.檢查', 'F-臉部下垂', 'A-手臂無力', 'S-言語不清', 'T-立即送醫']
    },
    {
      title: '嚴重過敏',
      icon: AlertTriangle,
      color: 'purple',
      steps: ['檢查呼吸道', '使用腎上腺素筆', '撥打119', '保持患者平躺']
    }
  ];

  const handleEmergencyCall = (number: string) => {
    if (window.confirm(`確定要撥打 ${number} 嗎？`)) {
      window.location.href = `tel:${number}`;
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 主要緊急號碼 - 超大卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {EMERGENCY_NUMBERS.map((contact) => (
          <div
            key={contact.number}
            onMouseEnter={() => setHoveredCard(contact.number)}
            onMouseLeave={() => setHoveredCard(null)}
            className={`
              relative overflow-hidden cursor-pointer
              transform transition-all duration-500 ease-out
              ${hoveredCard === contact.number ? 'scale-105' : 'scale-100'}
            `}
            onClick={() => handleEmergencyCall(contact.number)}
          >
            {/* 玻璃卡片背景 */}
            <div className="absolute inset-0 bg-gradient-to-br from-white/40 to-white/20 backdrop-blur-xl rounded-3xl" />

            {/* 動態光暈效果 */}
            <div className={`
              absolute inset-0 opacity-0 transition-opacity duration-500
              ${hoveredCard === contact.number ? 'opacity-100' : ''}
            `}>
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-red-500/30 rounded-full blur-3xl animate-pulse-glow" />
            </div>

            {/* 卡片內容 */}
            <div className="relative p-8 text-center">
              {/* 超大圖標 */}
              <div className="text-6xl mb-4 animate-float">{contact.icon}</div>

              {/* 號碼 - 超大字體 */}
              <div className="text-5xl font-bold text-red-600 mb-3 tracking-wider">
                {contact.number}
              </div>

              {/* 標籤 */}
              <div className="text-xl font-semibold text-gray-800 mb-2">
                {contact.label}
              </div>

              {/* 描述 */}
              <div className="text-sm text-gray-600">
                {contact.description}
              </div>

              {/* 撥打按鈕指示 */}
              <div className={`
                mt-4 flex items-center justify-center space-x-2
                text-red-600 transition-all duration-300
                ${hoveredCard === contact.number ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'}
              `}>
                <Phone className="w-5 h-5 animate-bounce-soft" />
                <span className="font-medium">點擊撥打</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </div>

            {/* 邊框發光效果 */}
            <div className={`
              absolute inset-0 rounded-3xl border-2 transition-all duration-500
              ${hoveredCard === contact.number
                ? 'border-red-400 shadow-glow-accent'
                : 'border-white/30'
              }
            `} />
          </div>
        ))}
      </div>

      {/* 其他緊急資源 */}
      <div className="glass-card rounded-3xl p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Shield className="w-6 h-6 text-brand-600 mr-3" />
          其他緊急資源
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {additionalResources.map((resource) => (
            <button
              key={resource.number}
              onClick={() => handleEmergencyCall(resource.number)}
              className="group relative overflow-hidden rounded-2xl p-4 text-left
                         bg-white/50 hover:bg-white/70 backdrop-blur-sm
                         border border-white/50 hover:border-brand-300
                         transform transition-all duration-300 hover:scale-102 hover:shadow-card"
            >
              <div className="flex items-start space-x-3">
                <span className="text-2xl">{resource.icon}</span>
                <div className="flex-1">
                  <div className="font-bold text-gray-800 group-hover:text-brand-600 transition-colors">
                    {resource.number}
                  </div>
                  <div className="text-sm font-medium text-gray-700">{resource.label}</div>
                  <div className="text-xs text-gray-500 mt-1">{resource.description}</div>
                </div>
              </div>

              {/* Hover 效果箭頭 */}
              <ChevronRight className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5
                                       text-brand-400 opacity-0 group-hover:opacity-100
                                       transform translate-x-2 group-hover:translate-x-0
                                       transition-all duration-300" />
            </button>
          ))}
        </div>
      </div>

      {/* 緊急情況處理指引 */}
      <div className="space-y-6">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center">
          <Siren className="w-7 h-7 text-red-500 mr-3 animate-pulse" />
          緊急情況處理指引
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {emergencyGuides.map((guide, index) => (
            <div
              key={index}
              className="group glass-card rounded-2xl p-6 hover:shadow-float
                         transform transition-all duration-500 hover:scale-102"
            >
              {/* 圖標和標題 */}
              <div className="flex items-center mb-4">
                <div className={`p-3 rounded-xl bg-${guide.color}-50
                                group-hover:bg-${guide.color}-100 transition-colors`}>
                  <guide.icon className={`w-6 h-6 text-${guide.color}-600`} />
                </div>
                <h4 className="ml-4 text-lg font-bold text-gray-800">{guide.title}</h4>
              </div>

              {/* 步驟列表 */}
              <ol className="space-y-2">
                {guide.steps.map((step, stepIndex) => (
                  <li key={stepIndex}
                      className="flex items-start space-x-3 text-sm
                                opacity-0 animate-fade-in"
                      style={{ animationDelay: `${(index * 100) + (stepIndex * 50)}ms` }}
                  >
                    <span className={`flex-shrink-0 w-6 h-6 rounded-full
                                     bg-${guide.color}-100 text-${guide.color}-700
                                     flex items-center justify-center text-xs font-bold`}>
                      {stepIndex + 1}
                    </span>
                    <span className="text-gray-700 leading-relaxed">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      </div>

      {/* 重要提醒 */}
      <div className="glass-card rounded-2xl p-6 bg-gradient-to-r from-red-50/50 to-orange-50/50
                      border-2 border-red-200/50">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-red-100 rounded-xl">
            <AlertTriangle className="w-6 h-6 text-red-600 animate-pulse" />
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-gray-800 mb-2">緊急狀況提醒</h4>
            <ul className="space-y-1 text-sm text-gray-600">
              <li>• 保持冷靜，清楚描述地址和狀況</li>
              <li>• 遵循調度員指示，不要擅自掛斷電話</li>
              <li>• 如可能，請他人協助撥打緊急電話</li>
              <li>• 準備好相關醫療資訊（藥物過敏、慢性病等）</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 最近醫院快速連結 */}
      <div className="glass-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h4 className="font-bold text-gray-800 flex items-center">
            <MapPin className="w-5 h-5 text-brand-600 mr-2" />
            附近急診醫院
          </h4>
          <button className="text-sm text-brand-600 hover:text-brand-700 font-medium
                           flex items-center space-x-1 hover:underline transition-all">
            <span>查看全部</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-center py-8 text-gray-500">
          <Clock className="w-5 h-5 mr-2 animate-pulse" />
          <span className="text-sm">請先允許定位以顯示附近醫院</span>
        </div>
      </div>
    </div>
  );
};

export default EmergencyInfo;