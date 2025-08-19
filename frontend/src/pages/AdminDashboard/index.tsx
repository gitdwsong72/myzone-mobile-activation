import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../../store/store';
import { fetchDashboardStats } from '../../store/slices/adminSlice';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import './AdminDashboard.css';

const AdminDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { admin, dashboardStats, statsLoading } = useSelector((state: RootState) => state.admin);

  useEffect(() => {
    dispatch(fetchDashboardStats());
  }, [dispatch]);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW'
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  const getCurrentTime = () => {
    return new Date().toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="admin-dashboard">
      <div className="admin-dashboard__header">
        <div className="admin-dashboard__welcome">
          <h1>관리자 대시보드</h1>
          <p>안녕하세요, <strong>{admin?.username}</strong>님! 오늘도 좋은 하루 되세요.</p>
          <span className="current-time">{getCurrentTime()}</span>
        </div>
        <div className="admin-dashboard__actions">
          <button className="refresh-btn" onClick={() => dispatch(fetchDashboardStats())}>
            🔄 새로고침
          </button>
        </div>
      </div>

      {statsLoading ? (
        <div className="admin-dashboard__loading">
          <LoadingSpinner size="large" />
          <p>통계 데이터를 불러오는 중...</p>
        </div>
      ) : (
        <div className="admin-dashboard__content">
          {/* 주요 통계 카드 */}
          <div className="stats-grid">
            <div className="stat-card stat-card--primary">
              <div className="stat-card__icon">📋</div>
              <div className="stat-card__content">
                <h3>오늘 신청</h3>
                <div className="stat-card__value">
                  {formatNumber(dashboardStats?.todayOrders || 0)}
                  <span className="stat-card__unit">건</span>
                </div>
                <p className="stat-card__description">오늘 접수된 개통 신청</p>
              </div>
            </div>

            <div className="stat-card stat-card--warning">
              <div className="stat-card__icon">⏳</div>
              <div className="stat-card__content">
                <h3>처리 대기</h3>
                <div className="stat-card__value">
                  {formatNumber(dashboardStats?.pendingOrders || 0)}
                  <span className="stat-card__unit">건</span>
                </div>
                <p className="stat-card__description">처리가 필요한 신청</p>
              </div>
            </div>

            <div className="stat-card stat-card--success">
              <div className="stat-card__icon">✅</div>
              <div className="stat-card__content">
                <h3>처리 완료</h3>
                <div className="stat-card__value">
                  {formatNumber(dashboardStats?.completedOrders || 0)}
                  <span className="stat-card__unit">건</span>
                </div>
                <p className="stat-card__description">오늘 완료된 신청</p>
              </div>
            </div>

            <div className="stat-card stat-card--info">
              <div className="stat-card__icon">💰</div>
              <div className="stat-card__content">
                <h3>총 매출</h3>
                <div className="stat-card__value">
                  {formatCurrency(dashboardStats?.totalRevenue || 0)}
                </div>
                <p className="stat-card__description">오늘 발생한 매출</p>
              </div>
            </div>
          </div>

          {/* 빠른 액션 */}
          <div className="quick-actions">
            <h2>빠른 작업</h2>
            <div className="quick-actions__grid">
              <button className="quick-action-btn">
                <span className="quick-action-btn__icon">📝</span>
                <span className="quick-action-btn__text">신규 주문 처리</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-btn__icon">📊</span>
                <span className="quick-action-btn__text">통계 보고서</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-btn__icon">👥</span>
                <span className="quick-action-btn__text">고객 관리</span>
              </button>
              <button className="quick-action-btn">
                <span className="quick-action-btn__icon">⚙️</span>
                <span className="quick-action-btn__text">시스템 설정</span>
              </button>
            </div>
          </div>

          {/* 최근 활동 */}
          <div className="recent-activity">
            <h2>최근 활동</h2>
            <div className="activity-list">
              <div className="activity-item">
                <div className="activity-item__icon">🔔</div>
                <div className="activity-item__content">
                  <p><strong>새로운 주문</strong>이 접수되었습니다.</p>
                  <span className="activity-item__time">5분 전</span>
                </div>
              </div>
              <div className="activity-item">
                <div className="activity-item__icon">✅</div>
                <div className="activity-item__content">
                  <p><strong>주문 #12345</strong>가 처리 완료되었습니다.</p>
                  <span className="activity-item__time">15분 전</span>
                </div>
              </div>
              <div className="activity-item">
                <div className="activity-item__icon">💳</div>
                <div className="activity-item__content">
                  <p><strong>결제 승인</strong>이 완료되었습니다.</p>
                  <span className="activity-item__time">30분 전</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;