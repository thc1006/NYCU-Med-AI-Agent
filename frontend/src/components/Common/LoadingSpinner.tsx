/**
 * 現代化載入動畫元件
 */

import React from 'react';
import { Heart, Sparkles } from 'lucide-react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'glass' | 'minimal';
  message?: string;
  showProgress?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'glass',
  message,
  showProgress = false
}) => {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const containerSizeClasses = {
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  };

  if (variant === 'minimal') {
    return (
      <div className="flex items-center justify-center">
        <div className={`loading-modern ${sizeClasses[size]}`}></div>
        {message && (
          <span className="ml-3 text-gray-600 text-sm">{message}</span>
        )}
      </div>
    );
  }

  if (variant === 'primary') {
    return (
      <div className="flex flex-col items-center justify-center space-y-4">
        <div className="relative">
          {/* 背景光環 */}
          <div className={`absolute inset-0 ${sizeClasses[size]} animate-pulse-glow`}>
            <div className="w-full h-full rounded-full bg-gradient-brand opacity-20"></div>
          </div>

          {/* 玻璃擬態容器 */}
          <div className={`relative glass-card ${sizeClasses[size]} rounded-full flex items-center justify-center animate-float`}>
            <Heart className={`${size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'} text-brand-600 animate-bounce-soft`} />
          </div>

          {/* 旋轉光環 */}
          <div className={`absolute inset-0 ${sizeClasses[size]}`}>
            <div className="loading-modern w-full h-full"></div>
          </div>
        </div>

        {message && (
          <div className="text-center space-y-2">
            <p className="text-gray-700 font-medium">{message}</p>
            {showProgress && (
              <div className="flex justify-center space-x-1">
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-75"></div>
                <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-150"></div>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Default: glass variant
  return (
    <div className={`glass-card rounded-3xl ${containerSizeClasses[size]} text-center space-y-4 animate-scale-in`}>
      <div className="relative mx-auto flex items-center justify-center">
        {/* 主要圖示 */}
        <div className={`glass-card ${sizeClasses[size]} rounded-full flex items-center justify-center animate-pulse-glow`}>
          <Heart className={`${size === 'lg' ? 'w-8 h-8' : size === 'md' ? 'w-6 h-6' : 'w-4 h-4'} text-brand-600`} />
        </div>

        {/* 裝飾性火花 */}
        <div className="absolute -top-2 -right-2">
          <Sparkles className="w-4 h-4 text-accent-500 animate-bounce-soft" />
        </div>

        {/* 旋轉載入圈 */}
        <div className={`absolute inset-0 ${sizeClasses[size]}`}>
          <div className="loading-modern w-full h-full"></div>
        </div>
      </div>

      {message && (
        <div className="space-y-2">
          <h3 className={`${size === 'lg' ? 'text-lg' : 'text-base'} font-semibold text-gray-800`}>
            {message}
          </h3>
          <p className="text-gray-600 text-sm">
            運用深度學習模型進行醫療級評估...
          </p>
        </div>
      )}

      {showProgress && (
        <div className="flex justify-center space-x-1">
          <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-75"></div>
          <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce animate-delay-150"></div>
        </div>
      )}

      {/* 進度條 (可選) */}
      {showProgress && (
        <div className="w-full bg-glass-light rounded-full h-2 overflow-hidden">
          <div className="h-full bg-gradient-brand animate-shimmer"></div>
        </div>
      )}
    </div>
  );
};

export default LoadingSpinner;