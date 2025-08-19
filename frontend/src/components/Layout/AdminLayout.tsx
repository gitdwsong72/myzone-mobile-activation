import React, { useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import { RootState, AppDispatch } from '../../store/store';
import { fetchAdminProfile } from '../../store/slices/adminSlice';
import AdminSidebar from './AdminSidebar';
import LoadingSpinner from '../Common/LoadingSpinner';
import './AdminLayout.css';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: React.FC<AdminLayoutProps> = ({ children }) => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, admin, token } = useSelector((state: RootState) => state.admin);

  useEffect(() => {
    // 토큰이 있지만 관리자 정보가 없는 경우 프로필 조회
    if (token && !admin) {
      dispatch(fetchAdminProfile());
    }
    
    // 인증되지 않은 경우 로그인 페이지로 리다이렉트
    if (!isAuthenticated && !token) {
      navigate('/admin/login');
    }
  }, [dispatch, navigate, isAuthenticated, token, admin]);

  // 로딩 중이거나 인증되지 않은 경우
  if (!isAuthenticated || !admin) {
    return (
      <div className="admin-layout__loading">
        <LoadingSpinner size="large" />
        <p>관리자 정보를 확인하는 중...</p>
      </div>
    );
  }

  const getPageTitle = () => {
    const path = location.pathname;
    switch (path) {
      case '/admin/dashboard':
        return '대시보드';
      case '/admin/orders':
        return '주문 관리';
      case '/admin/statistics':
        return '통계 및 리포트';
      case '/admin/users':
        return '사용자 관리';
      case '/admin/plans':
        return '요금제 관리';
      case '/admin/devices':
        return '단말기 관리';
      case '/admin/support':
        return '고객 지원';
      case '/admin/settings':
        return '시스템 설정';
      default:
        return '관리자';
    }
  };

  return (
    <div className="admin-layout">
      <AdminSidebar />
      <div className="admin-layout__content">
        <header className="admin-layout__header">
          <div className="admin-layout__breadcrumb">
            <span className="breadcrumb-home">🏠</span>
            <span className="breadcrumb-separator">/</span>
            <span className="breadcrumb-current">{getPageTitle()}</span>
          </div>
          <div className="admin-layout__header-actions">
            <button className="header-action-btn" title="알림">
              🔔
              <span className="notification-badge">3</span>
            </button>
            <button className="header-action-btn" title="설정">
              ⚙️
            </button>
          </div>
        </header>
        <main className="admin-layout__main">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;