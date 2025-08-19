import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { setSidebar } from '../../store/slices/uiSlice';
import { ROUTES } from '../../utils/navigation';

interface SidebarProps {
  isAdmin?: boolean;
}

const Sidebar: React.FC<SidebarProps> = ({ isAdmin = false }) => {
  const location = useLocation();
  const dispatch = useAppDispatch();
  const { sidebarOpen } = useAppSelector((state) => state.ui);

  const handleCloseSidebar = () => {
    dispatch(setSidebar(false));
  };

  // 관리자 메뉴 항목
  const adminMenuItems = [
    {
      path: '/admin',
      label: '대시보드',
      icon: '📊',
    },
    {
      path: '/admin/orders',
      label: '주문 관리',
      icon: '📋',
    },
    {
      path: '/admin/statistics',
      label: '통계',
      icon: '📈',
    },
    {
      path: '/admin/users',
      label: '사용자 관리',
      icon: '👥',
    },
    {
      path: '/admin/settings',
      label: '설정',
      icon: '⚙️',
    },
  ];

  // 일반 사용자 메뉴 항목
  const userMenuItems = [
    {
      path: ROUTES.HOME,
      label: '홈',
      icon: '🏠',
    },
    {
      path: ROUTES.PLANS,
      label: '요금제',
      icon: '📱',
    },
    {
      path: ROUTES.ORDER_STATUS,
      label: '신청현황',
      icon: '📋',
    },
    {
      path: ROUTES.SUPPORT,
      label: '고객지원',
      icon: '💬',
    },
  ];

  const menuItems = isAdmin ? adminMenuItems : userMenuItems;

  const isActiveRoute = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <>
      {/* 사이드바 오버레이 */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={handleCloseSidebar} />
      )}

      {/* 사이드바 */}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2 className="sidebar-title">
            {isAdmin ? '관리자 메뉴' : 'MyZone'}
          </h2>
          <button
            className="sidebar-close-btn"
            onClick={handleCloseSidebar}
            aria-label="사이드바 닫기"
          >
            ✕
          </button>
        </div>

        <nav className="sidebar-nav">
          <ul className="sidebar-menu">
            {menuItems.map((item) => (
              <li key={item.path} className="sidebar-menu-item">
                <Link
                  to={item.path}
                  className={`sidebar-menu-link ${
                    isActiveRoute(item.path) ? 'active' : ''
                  }`}
                  onClick={handleCloseSidebar}
                >
                  <span className="sidebar-menu-icon">{item.icon}</span>
                  <span className="sidebar-menu-label">{item.label}</span>
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {isAdmin && (
          <div className="sidebar-footer">
            <Link
              to={ROUTES.HOME}
              className="sidebar-footer-link"
              onClick={handleCloseSidebar}
            >
              고객 페이지로 이동
            </Link>
          </div>
        )}
      </aside>
    </>
  );
};

export default Sidebar;