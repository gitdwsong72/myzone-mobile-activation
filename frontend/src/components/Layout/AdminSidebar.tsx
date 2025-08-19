import React, { useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useLocation } from 'react-router-dom';
import { RootState, AppDispatch } from '../../store/store';
import { adminLogout } from '../../store/slices/adminSlice';
import './AdminSidebar.css';

interface MenuItem {
  id: string;
  label: string;
  icon: string;
  path: string;
  badge?: number;
}

const AdminSidebar: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const location = useLocation();
  const { admin } = useSelector((state: RootState) => state.admin);
  
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems: MenuItem[] = [
    {
      id: 'dashboard',
      label: '대시보드',
      icon: '📊',
      path: '/admin/dashboard'
    },
    {
      id: 'orders',
      label: '주문 관리',
      icon: '📋',
      path: '/admin/orders',
      badge: 5 // 처리 대기 건수 (실제로는 상태에서 가져와야 함)
    },
    {
      id: 'statistics',
      label: '통계 및 리포트',
      icon: '📈',
      path: '/admin/statistics'
    },
    {
      id: 'users',
      label: '사용자 관리',
      icon: '👥',
      path: '/admin/users'
    },
    {
      id: 'plans',
      label: '요금제 관리',
      icon: '💳',
      path: '/admin/plans'
    },
    {
      id: 'devices',
      label: '단말기 관리',
      icon: '📱',
      path: '/admin/devices'
    },
    {
      id: 'support',
      label: '고객 지원',
      icon: '🎧',
      path: '/admin/support'
    },
    {
      id: 'settings',
      label: '시스템 설정',
      icon: '⚙️',
      path: '/admin/settings'
    }
  ];

  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  const handleLogout = async () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      await dispatch(adminLogout());
      navigate('/admin/login');
    }
  };

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  const isActiveMenu = (path: string) => {
    return location.pathname === path;
  };

  return (
    <div className={`admin-sidebar ${isCollapsed ? 'admin-sidebar--collapsed' : ''}`}>
      {/* 사이드바 헤더 */}
      <div className="admin-sidebar__header">
        <div className="admin-sidebar__logo">
          <span className="logo-icon">🏢</span>
          {!isCollapsed && <span className="logo-text">MyZone Admin</span>}
        </div>
        <button 
          className="sidebar-toggle"
          onClick={toggleSidebar}
          title={isCollapsed ? '사이드바 확장' : '사이드바 축소'}
        >
          {isCollapsed ? '▶️' : '◀️'}
        </button>
      </div>

      {/* 관리자 프로필 */}
      <div className="admin-sidebar__profile">
        <div className="profile-avatar">
          {admin?.username?.charAt(0).toUpperCase() || 'A'}
        </div>
        {!isCollapsed && (
          <div className="profile-info">
            <div className="profile-name">{admin?.username}</div>
            <div className="profile-role">{admin?.role || '관리자'}</div>
          </div>
        )}
      </div>

      {/* 메뉴 리스트 */}
      <nav className="admin-sidebar__nav">
        <ul className="nav-list">
          {menuItems.map((item) => (
            <li key={item.id} className="nav-item">
              <button
                className={`nav-link ${isActiveMenu(item.path) ? 'nav-link--active' : ''}`}
                onClick={() => handleMenuClick(item.path)}
                title={isCollapsed ? item.label : undefined}
              >
                <span className="nav-icon">{item.icon}</span>
                {!isCollapsed && (
                  <>
                    <span className="nav-label">{item.label}</span>
                    {item.badge && item.badge > 0 && (
                      <span className="nav-badge">{item.badge}</span>
                    )}
                  </>
                )}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* 사이드바 푸터 */}
      <div className="admin-sidebar__footer">
        <button 
          className="logout-btn"
          onClick={handleLogout}
          title={isCollapsed ? '로그아웃' : undefined}
        >
          <span className="logout-icon">🚪</span>
          {!isCollapsed && <span className="logout-text">로그아웃</span>}
        </button>
      </div>
    </div>
  );
};

export default AdminSidebar;