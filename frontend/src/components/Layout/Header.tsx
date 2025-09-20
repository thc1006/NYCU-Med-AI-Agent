/**
 * 現代化玻璃擬態應用程式標題列元件
 */

import React from 'react';
import { Heart, MapPin, History, Sparkles, Shield, Navigation, AlertTriangle, BookHeart } from 'lucide-react';
import { Link, useLocation as useRouterLocation } from 'react-router-dom';
import { useLocation } from '../../stores/useAppStore';

interface HeaderProps {
  onLocationClick?: () => void;
  onHistoryClick?: () => void;
}

const Header: React.FC<HeaderProps> = ({ onLocationClick, onHistoryClick }) => {
  const { userLocation, locationPermission } = useLocation();
  const routerLocation = useRouterLocation();

  return (
    <header className="sticky top-0 z-50 safe-top">
      {/* 玻璃擬態背景 */}
      <div className="glass-card border-0 border-b border-white/20 rounded-none backdrop-blur-2xl">
        <div className="container-glass py-4">
          <div className="flex items-center justify-between">
            {/* Logo 和品牌標識 */}
            <div className="flex items-center space-x-4">
              {/* 現代化 Logo */}
              <div className="relative">
                <div className="glass-card w-14 h-14 rounded-2xl flex items-center justify-center animate-pulse-glow">
                  <Heart className="w-7 h-7 text-brand-600" />
                </div>
                <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-accent rounded-full flex items-center justify-center">
                  <Sparkles className="w-2.5 h-2.5 text-white" />
                </div>
              </div>

              {/* 品牌名稱和標語 */}
              <div className="space-y-1">
                <h1 className="text-xl font-bold bg-gradient-to-r from-brand-600 to-medical-600 bg-clip-text text-transparent">
                  台灣醫療AI助手
                </h1>
                <div className="flex items-center space-x-2 text-xs text-gray-600">
                  <Shield className="w-3 h-3 text-medical-500" />
                  <span>智能分級 • 精準就醫 • 即時守護</span>
                </div>
              </div>
            </div>

            {/* 現代化功能按鈕群組 */}
            <div className="flex items-center space-x-3">
              {/* 導航連結 */}
              <nav className="hidden md:flex items-center space-x-2 mr-4">
                <Link
                  to="/"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
                    ${routerLocation.pathname === '/'
                      ? 'glass-card bg-gradient-brand text-white shadow-glow'
                      : 'text-gray-600 hover:bg-glass-medium hover:text-brand-600'}`}
                >
                  <div className="flex items-center space-x-2">
                    <Heart className="w-4 h-4" />
                    <span>症狀評估</span>
                  </div>
                </Link>

                <Link
                  to="/emergency"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
                    ${routerLocation.pathname === '/emergency'
                      ? 'glass-card bg-gradient-brand text-white shadow-glow'
                      : 'text-gray-600 hover:bg-glass-medium hover:text-brand-600'}`}
                >
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span>緊急資訊</span>
                  </div>
                </Link>

                <Link
                  to="/resources"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
                    ${routerLocation.pathname === '/resources'
                      ? 'glass-card bg-gradient-brand text-white shadow-glow'
                      : 'text-gray-600 hover:bg-glass-medium hover:text-brand-600'}`}
                >
                  <div className="flex items-center space-x-2">
                    <BookHeart className="w-4 h-4" />
                    <span>健康資源</span>
                  </div>
                </Link>

                <Link
                  to="/history"
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-300
                    ${routerLocation.pathname === '/history'
                      ? 'glass-card bg-gradient-brand text-white shadow-glow'
                      : 'text-gray-600 hover:bg-glass-medium hover:text-brand-600'}`}
                >
                  <div className="flex items-center space-x-2">
                    <History className="w-4 h-4" />
                    <span>歷史記錄</span>
                  </div>
                </Link>
              </nav>

              {/* 位置定位按鈕 */}
              <button
                onClick={onLocationClick}
                className={`
                  glass-card p-3 rounded-xl transition-all duration-300 transform hover:scale-105 micro-interaction
                  ${locationPermission && userLocation
                    ? 'bg-gradient-to-br from-medical-100 to-medical-50 text-medical-700 shadow-glow'
                    : 'text-gray-600 hover:bg-glass-medium'
                  }
                `}
                title={
                  locationPermission && userLocation
                    ? '位置已定位 ✓'
                    : '點擊進行定位'
                }
              >
                <div className="relative">
                  <MapPin className={`w-5 h-5 ${locationPermission && userLocation ? 'animate-bounce-soft' : ''}`} />
                  {locationPermission && userLocation && (
                    <div className="absolute -top-1 -right-1 w-2 h-2 bg-medical-500 rounded-full animate-ping"></div>
                  )}
                </div>
              </button>
            </div>
          </div>

          {/* 位置狀態指示器 */}
          {userLocation && (
            <div className="mt-4 animate-fade-in">
              <div className="glass-card rounded-xl p-3 bg-medical-50/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2 text-sm text-medical-700">
                    <Navigation className="w-4 h-4 text-medical-500" />
                    <span className="font-medium">定位成功</span>
                  </div>
                  <div className="text-xs text-gray-500 font-mono">
                    {userLocation.latitude.toFixed(4)}, {userLocation.longitude.toFixed(4)}
                  </div>
                </div>
                <div className="mt-2 w-full bg-medical-200 rounded-full h-1">
                  <div className="bg-gradient-to-r from-medical-500 to-brand-500 h-1 rounded-full w-full animate-shimmer"></div>
                </div>
              </div>
            </div>
          )}

          {/* 未定位時的提示 */}
          {!userLocation && (
            <div className="mt-4 animate-fade-in">
              <div className="glass-card rounded-xl p-3 bg-amber-50/30 border border-amber-200/50">
                <div className="flex items-center space-x-2 text-sm text-amber-700">
                  <MapPin className="w-4 h-4 text-amber-500" />
                  <span>點擊定位圖示以獲得更精準的醫院推薦</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 裝飾性光效 */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-32 h-8 bg-gradient-to-r from-transparent via-brand-200/20 to-transparent blur-sm"></div>
        <div className="absolute bottom-0 right-1/4 w-24 h-6 bg-gradient-to-l from-transparent via-medical-200/20 to-transparent blur-sm"></div>
      </div>
    </header>
  );
};

export default Header;