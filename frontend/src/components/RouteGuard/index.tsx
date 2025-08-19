import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

interface RouteGuardProps {
  children: React.ReactNode;
  requireAuth?: boolean;
  requireAdmin?: boolean;
}

const RouteGuard: React.FC<RouteGuardProps> = ({
  children,
  requireAuth = false,
  requireAdmin = false,
}) => {
  const location = useLocation();
  
  // TODO: 실제 인증 상태를 Redux store에서 가져와야 함
  const isAuthenticated = false; // 임시로 false 설정
  const isAdmin = false; // 임시로 false 설정

  if (requireAuth && !isAuthenticated) {
    // 로그인이 필요한 페이지인데 인증되지 않은 경우
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requireAdmin && !isAdmin) {
    // 관리자 권한이 필요한 페이지인데 관리자가 아닌 경우
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default RouteGuard;