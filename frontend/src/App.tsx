/**
 * 台灣醫療 AI 助手 - 現代化玻璃擬態設計
 */

import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { Heart, Sparkles, Shield } from 'lucide-react';

// 頁面元件 - 使用懶加載
const HomePage = React.lazy(() => import('./pages/HomePage'));
const HistoryPage = React.lazy(() => import('./pages/HistoryPage'));
const EmergencyInfo = React.lazy(() => import('./components/EmergencyInfo'));
const HealthResources = React.lazy(() => import('./components/HealthResources'));

// 現代化載入元件
const ModernLoadingSpinner: React.FC = () => (
  <div className="min-h-screen bg-gradient-medical flex items-center justify-center p-4">
    <div className="text-center">
      {/* 主要載入圖示 */}
      <div className="relative mb-8">
        {/* 背景光環 */}
        <div className="absolute inset-0 w-20 h-20 mx-auto animate-pulse-glow">
          <div className="w-full h-full rounded-full bg-gradient-brand opacity-20"></div>
        </div>

        {/* 玻璃擬態容器 */}
        <div className="relative glass-card w-20 h-20 rounded-full mx-auto flex items-center justify-center animate-float">
          <Heart className="w-10 h-10 text-brand-600 animate-bounce-soft" />
        </div>

        {/* 旋轉光環 */}
        <div className="absolute inset-0 w-20 h-20 mx-auto">
          <div className="loading-modern"></div>
        </div>
      </div>

      {/* 載入文字 */}
      <div className="glass-card rounded-2xl px-6 py-4 animate-fade-in animate-delay-300">
        <h3 className="text-lg font-semibold text-gray-800 mb-2 flex items-center justify-center gap-2">
          <Sparkles className="w-5 h-5 text-brand-500" />
          正在啟動醫療助手
        </h3>
        <p className="text-gray-600 text-sm">請稍候，為您準備最佳的醫療諮詢體驗...</p>

        {/* 進度條 */}
        <div className="mt-4 w-full bg-glass-light rounded-full h-2 overflow-hidden">
          <div className="h-full bg-gradient-brand animate-shimmer"></div>
        </div>
      </div>

      {/* 裝飾性元素 */}
      <div className="absolute top-1/4 left-1/4 w-32 h-32 bg-brand-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float animate-delay-700"></div>
      <div className="absolute bottom-1/4 right-1/4 w-24 h-24 bg-accent-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float animate-delay-1000"></div>
    </div>
  </div>
);

// 現代化錯誤邊界元件
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): { hasError: boolean; error: Error } {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Application error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-medical flex items-center justify-center p-4">
          <div className="text-center max-w-lg">
            {/* 錯誤圖示 */}
            <div className="relative mb-8">
              <div className="glass-card w-24 h-24 rounded-full mx-auto flex items-center justify-center animate-scale-in">
                <Shield className="w-12 h-12 text-red-500" />
              </div>
              <div className="absolute inset-0 w-24 h-24 mx-auto">
                <div className="w-full h-full rounded-full border-4 border-red-200 animate-ping"></div>
              </div>
            </div>

            {/* 錯誤內容 */}
            <div className="glass-card rounded-3xl p-8 animate-fade-in animate-delay-200">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                🚨 系統暫時無法使用
              </h1>

              <p className="text-gray-700 mb-6 leading-relaxed">
                很抱歉，醫療助手遇到了技術問題。我們正在努力修復中，請稍後再試。
              </p>

              <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 mb-6">
                <p className="text-amber-800 text-sm flex items-center gap-2">
                  <Sparkles className="w-4 h-4" />
                  <strong>緊急情況請撥打:</strong> 119 (救護車) | 112 (緊急電話)
                </p>
              </div>

              <div className="space-y-4">
                <button
                  onClick={() => window.location.reload()}
                  className="w-full btn-primary"
                >
                  🔄 重新整理頁面
                </button>

                <button
                  onClick={() => this.setState({ hasError: false })}
                  className="w-full btn-secondary"
                >
                  🔄 重新嘗試
                </button>
              </div>

              {/* 開發模式錯誤詳情 */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer font-medium text-gray-700 mb-3 glass-card rounded-lg p-3 hover:bg-glass-medium transition-all">
                    🔧 錯誤詳情 (開發模式)
                  </summary>
                  <div className="glass-card rounded-xl p-4 bg-red-50/50">
                    <pre className="text-xs text-red-700 overflow-auto whitespace-pre-wrap">
                      {this.state.error.toString()}
                      {this.state.error.stack && (
                        <>
                          {'\n\n--- Stack Trace ---\n'}
                          {this.state.error.stack}
                        </>
                      )}
                    </pre>
                  </div>
                </details>
              )}
            </div>

            {/* 裝飾元素 */}
            <div className="absolute top-1/3 left-1/3 w-20 h-20 bg-red-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float"></div>
            <div className="absolute bottom-1/3 right-1/3 w-16 h-16 bg-orange-200 rounded-full mix-blend-multiply filter blur-xl opacity-30 animate-float animate-delay-500"></div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// 現代化主應用程式元件
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <div className="App min-h-screen bg-gradient-medical relative overflow-hidden">
          {/* 背景裝飾元素 */}
          <div className="fixed inset-0 pointer-events-none">
            <div className="absolute top-0 left-0 w-96 h-96 bg-brand-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float"></div>
            <div className="absolute top-1/2 right-0 w-80 h-80 bg-accent-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float animate-delay-700"></div>
            <div className="absolute bottom-0 left-1/3 w-72 h-72 bg-medical-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-float animate-delay-1000"></div>
          </div>

          {/* 主要路由 */}
          <Suspense fallback={<ModernLoadingSpinner />}>
            <Routes>
              {/* 首頁 - 症狀評估 */}
              <Route path="/" element={<HomePage />} />

              {/* 歷史記錄頁面 */}
              <Route path="/history" element={<HistoryPage />} />

              {/* 緊急資訊頁面 */}
              <Route path="/emergency" element={<EmergencyInfo />} />

              {/* 健康資源頁面 */}
              <Route path="/resources" element={<HealthResources />} />

              {/* 重新導向未知路由到首頁 */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>

          {/* 現代化全域通知系統 */}
          <Toaster
            position="top-center"
            containerStyle={{
              top: '2rem',
              zIndex: 9999,
            }}
            toastOptions={{
              duration: 5000,
              style: {
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(16px)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                borderRadius: '1rem',
                padding: '1rem 1.25rem',
                maxWidth: '90vw',
                fontSize: '0.875rem',
                fontWeight: '500',
                color: '#374151',
                boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.2)',
              },
              success: {
                style: {
                  background: 'linear-gradient(135deg, rgba(34, 197, 94, 0.9), rgba(22, 163, 74, 0.8))',
                  color: '#fff',
                  boxShadow: '0 8px 32px rgba(34, 197, 94, 0.3)',
                },
                iconTheme: {
                  primary: '#fff',
                  secondary: '#22C55E'
                }
              },
              error: {
                style: {
                  background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.9), rgba(220, 38, 38, 0.8))',
                  color: '#fff',
                  boxShadow: '0 8px 32px rgba(239, 68, 68, 0.3)',
                },
                iconTheme: {
                  primary: '#fff',
                  secondary: '#EF4444'
                },
                duration: 6000
              },
              loading: {
                style: {
                  background: 'linear-gradient(135deg, rgba(8, 145, 178, 0.9), rgba(6, 182, 212, 0.8))',
                  color: '#fff',
                  boxShadow: '0 8px 32px rgba(8, 145, 178, 0.3)',
                },
                iconTheme: {
                  primary: '#fff',
                  secondary: '#0891B2'
                }
              },
              // 警告樣式
              blank: {
                style: {
                  background: 'linear-gradient(135deg, rgba(249, 115, 22, 0.9), rgba(234, 88, 12, 0.8))',
                  color: '#fff',
                  boxShadow: '0 8px 32px rgba(249, 115, 22, 0.3)',
                },
              }
            }}
          />

          {/* 全域無障礙輔助 */}
          <div className="sr-only">
            <div aria-live="polite" aria-atomic="true" id="announcements"></div>
          </div>

          {/* 現代化捲軸樣式 */}
          <style dangerouslySetInnerHTML={{__html: `
            .Toastify__toast {
              border-radius: 1rem !important;
              backdrop-filter: blur(16px) !important;
            }
          `}} />
        </div>
      </Router>
    </ErrorBoundary>
  );
};

export default App;