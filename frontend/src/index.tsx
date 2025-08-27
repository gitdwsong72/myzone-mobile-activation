import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import './index.css';
import App from './App';
import { store } from './store/store';
import reportWebVitals from './reportWebVitals';
import * as serviceWorker from './utils/serviceWorker';
import { performanceMonitor } from './utils/performance';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter basename={process.env.PUBLIC_URL}>
        <App />
      </BrowserRouter>
    </Provider>
  </React.StrictMode>
);

// 서비스 워커 등록 (프로덕션 환경에서만)
if (process.env.NODE_ENV === 'production') {
  serviceWorker.register({
    onSuccess: () => {
      console.log('Service Worker registered successfully');
    },
    onUpdate: (registration) => {
      console.log('New content available, please refresh');
      // 사용자에게 업데이트 알림 표시
      if (window.confirm('새로운 버전이 있습니다. 페이지를 새로고침하시겠습니까?')) {
        window.location.reload();
      }
    }
  });
}

// 성능 모니터링 시작
if (process.env.NODE_ENV === 'development') {
  // 개발 환경에서 성능 리포트 출력
  setTimeout(() => {
    console.log(performanceMonitor.generateReport());
  }, 5000);
}

reportWebVitals();