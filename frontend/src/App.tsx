import React, { Suspense } from 'react';
import { Routes, Route, useLocation } from 'react-router-dom';
import './App.css';

// 레이아웃 및 공통 컴포넌트
import MainLayout from './components/Layout/MainLayout';
import ErrorBoundary from './components/Common/ErrorBoundary';
import ToastContainer from './components/Common/Toast';
import LoadingSpinner from './components/Common/LoadingSpinner';

// 커스텀 훅
import { useScreenSize } from './hooks/useScreenSize';

// 코드 스플리팅을 위한 lazy loading
// 고객 대면 페이지
const HomePage = React.lazy(() => import('./pages/HomePage'));
const PlanSelectionPage = React.lazy(() => import('./pages/PlanSelectionPage'));
const UserInfoPage = React.lazy(() => import('./pages/UserInfoPage'));
const DeviceSelectionPage = React.lazy(() => import('./pages/DeviceSelectionPage'));
const NumberSelectionPage = React.lazy(() => import('./pages/NumberSelectionPage'));
const OrderSummaryPage = React.lazy(() => import('./pages/OrderSummaryPage'));
const PaymentPage = React.lazy(() => import('./pages/PaymentPage'));
const PaymentCompletePage = React.lazy(() => import('./pages/PaymentCompletePage'));
const OrderStatusPage = React.lazy(() => import('./pages/OrderStatusPage'));
const SupportPage = React.lazy(() => import('./pages/SupportPage'));

// 관리자 페이지 (별도 청크로 분리)
const AdminLogin = React.lazy(() => import('./pages/AdminLogin'));
const AdminDashboard = React.lazy(() => import('./pages/AdminDashboard'));
const AdminOrders = React.lazy(() => import('./pages/AdminOrders'));
const AdminStatistics = React.lazy(() => import('./pages/AdminStatistics'));

// 레이아웃 컴포넌트 (관리자 레이아웃은 필요시에만 로드)
const AdminLayout = React.lazy(() => import('./components/Layout/AdminLayout'));

// 로딩 컴포넌트
const PageLoader = () => (
  <div className="page-loader">
    <LoadingSpinner />
    <p>페이지를 불러오는 중...</p>
  </div>
);

function App() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith('/admin');
  
  // 화면 크기 감지
  useScreenSize();

  return (
    <ErrorBoundary>
      <div className="App">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* 고객 대면 페이지 */}
            <Route path="/" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <HomePage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/plans" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <PlanSelectionPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/user-info" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <UserInfoPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/devices" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <DeviceSelectionPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/numbers" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <NumberSelectionPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/order-summary" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <OrderSummaryPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/payment" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <PaymentPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/payment-complete" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <PaymentCompletePage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/order-status" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <OrderStatusPage />
                </Suspense>
              </MainLayout>
            } />
            <Route path="/support" element={
              <MainLayout>
                <Suspense fallback={<LoadingSpinner />}>
                  <SupportPage />
                </Suspense>
              </MainLayout>
            } />
            
            {/* 관리자 로그인 페이지 (레이아웃 없음) */}
            <Route path="/admin/login" element={
              <Suspense fallback={<PageLoader />}>
                <AdminLogin />
              </Suspense>
            } />
            
            {/* 관리자 페이지 - 관리자 레이아웃 적용 */}
            <Route path="/admin/dashboard" element={
              <Suspense fallback={<PageLoader />}>
                <AdminLayout>
                  <Suspense fallback={<LoadingSpinner />}>
                    <AdminDashboard />
                  </Suspense>
                </AdminLayout>
              </Suspense>
            } />
            <Route path="/admin/orders" element={
              <Suspense fallback={<PageLoader />}>
                <AdminLayout>
                  <Suspense fallback={<LoadingSpinner />}>
                    <AdminOrders />
                  </Suspense>
                </AdminLayout>
              </Suspense>
            } />
            <Route path="/admin/statistics" element={
              <Suspense fallback={<PageLoader />}>
                <AdminLayout>
                  <Suspense fallback={<LoadingSpinner />}>
                    <AdminStatistics />
                  </Suspense>
                </AdminLayout>
              </Suspense>
            } />
            
            {/* 404 페이지 */}
            <Route 
              path="*" 
              element={
                <MainLayout>
                  <div className="not-found">
                    <h1>404</h1>
                    <p>페이지를 찾을 수 없습니다.</p>
                  </div>
                </MainLayout>
              } 
            />
          </Routes>
        </Suspense>
        
        {/* 토스트 알림 */}
        <ToastContainer />
      </div>
    </ErrorBoundary>
  );
}

export default App;