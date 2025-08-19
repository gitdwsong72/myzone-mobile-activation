import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { logout } from '../../store/slices/authSlice';
import { toggleMobileMenu } from '../../store/slices/uiSlice';
import { ROUTES } from '../../utils/navigation';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const { mobileMenuOpen } = useAppSelector((state) => state.ui);

  const handleLogout = () => {
    dispatch(logout());
    navigate(ROUTES.HOME);
  };

  const handleMobileMenuToggle = () => {
    dispatch(toggleMobileMenu());
  };

  return (
    <header className="header">
      <div className="header-container">
        {/* 로고 */}
        <div className="header-logo">
          <Link to={ROUTES.HOME} className="logo-link">
            <img src="/logo.png" alt="MyZone" className="logo-image" />
            <span className="logo-text">MyZone</span>
          </Link>
        </div>

        {/* 데스크톱 네비게이션 */}
        <nav className="header-nav desktop-nav">
          <ul className="nav-list">
            <li className="nav-item">
              <Link to={ROUTES.PLANS} className="nav-link">
                요금제
              </Link>
            </li>
            <li className="nav-item">
              <Link to={ROUTES.ORDER_STATUS} className="nav-link">
                신청현황
              </Link>
            </li>
            <li className="nav-item">
              <Link to={ROUTES.SUPPORT} className="nav-link">
                고객지원
              </Link>
            </li>
          </ul>
        </nav>

        {/* 사용자 메뉴 */}
        <div className="header-user">
          {isAuthenticated ? (
            <div className="user-menu">
              <span className="user-name">안녕하세요, {user?.name}님</span>
              {user?.role === 'admin' && (
                <Link to={ROUTES.ADMIN} className="admin-link">
                  관리자
                </Link>
              )}
              <button onClick={handleLogout} className="logout-btn">
                로그아웃
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button className="login-btn">로그인</button>
              <button className="signup-btn">회원가입</button>
            </div>
          )}
        </div>

        {/* 모바일 메뉴 버튼 */}
        <button
          className="mobile-menu-btn"
          onClick={handleMobileMenuToggle}
          aria-label="메뉴 열기"
        >
          <span className={`hamburger ${mobileMenuOpen ? 'active' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
      </div>

      {/* 모바일 메뉴 */}
      {mobileMenuOpen && (
        <div className="mobile-menu">
          <nav className="mobile-nav">
            <ul className="mobile-nav-list">
              <li className="mobile-nav-item">
                <Link to={ROUTES.PLANS} className="mobile-nav-link">
                  요금제
                </Link>
              </li>
              <li className="mobile-nav-item">
                <Link to={ROUTES.ORDER_STATUS} className="mobile-nav-link">
                  신청현황
                </Link>
              </li>
              <li className="mobile-nav-item">
                <Link to={ROUTES.SUPPORT} className="mobile-nav-link">
                  고객지원
                </Link>
              </li>
              {user?.role === 'admin' && (
                <li className="mobile-nav-item">
                  <Link to={ROUTES.ADMIN} className="mobile-nav-link">
                    관리자
                  </Link>
                </li>
              )}
            </ul>
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;