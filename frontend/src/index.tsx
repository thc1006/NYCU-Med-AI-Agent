/**
 * 台灣醫療 AI 助手 - 應用程式入口點
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

// 註冊 Service Worker（PWA 支援）
if ('serviceWorker' in navigator && process.env.NODE_ENV === 'production') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((registration) => {
        console.log('SW registered: ', registration);
      })
      .catch((registrationError) => {
        console.log('SW registration failed: ', registrationError);
      });
  });
}

// 錯誤報告（僅開發環境）
if (process.env.NODE_ENV === 'development') {
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
  });

  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason);
  });
}

// 取得根元素
const container = document.getElementById('root');

if (!container) {
  throw new Error('Failed to find the root element');
}

// 建立 React Root
const root = ReactDOM.createRoot(container);

// 渲染應用程式
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// 性能監控（可選）
if (process.env.NODE_ENV === 'production') {
  // 可以在這裡加入 Web Vitals 或其他分析工具
  import('web-vitals').then(({ getCLS, getFID, getFCP, getLCP, getTTFB }) => {
    getCLS(console.log);
    getFID(console.log);
    getFCP(console.log);
    getLCP(console.log);
    getTTFB(console.log);
  });
}