import React, { useState } from 'react';
import './OrderStatusPage.css';
import LoadingSpinner from '../../components/Common/LoadingSpinner';

interface OrderStatus {
  id: number;
  order_number: string;
  status: string;
  total_amount: number;
  user_name: string;
  plan_name: string;
  device_name?: string;
  number?: string;
  created_at: string;
}

const OrderStatusPage: React.FC = () => {
  const [orderNumber, setOrderNumber] = useState('');
  const [orderStatus, setOrderStatus] = useState<OrderStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const statusSteps = [
    { key: 'pending', label: '접수완료', icon: '1' },
    { key: 'confirmed', label: '심사중', icon: '2' },
    { key: 'processing', label: '개통처리중', icon: '3' },
    { key: 'completed', label: '개통완료', icon: '4' }
  ];

  const statusLabels: { [key: string]: string } = {
    pending: '접수완료',
    confirmed: '심사중',
    processing: '개통처리중',
    completed: '개통완료',
    cancelled: '취소됨'
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!orderNumber.trim()) {
      setError('신청번호를 입력해주세요.');
      return;
    }

    setLoading(true);
    setError(null);
    setOrderStatus(null);

    try {
      const response = await fetch(`/api/v1/orders/public/${orderNumber.trim()}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('해당 신청번호를 찾을 수 없습니다.');
        }
        throw new Error('조회 중 오류가 발생했습니다.');
      }

      const data = await response.json();
      setOrderStatus(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusIndex = (status: string): number => {
    const statusOrder = ['pending', 'confirmed', 'processing', 'completed'];
    return statusOrder.indexOf(status);
  };

  const getProgressPercentage = (status: string): number => {
    const index = getStatusIndex(status);
    if (index === -1) return 0;
    return ((index + 1) / statusSteps.length) * 100;
  };

  const formatAmount = (amount: number): string => {
    return new Intl.NumberFormat('ko-KR').format(amount);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="order-status-page">
      <div className="order-status-container">
        <div className="page-header">
          <h1 className="page-title">신청 현황 조회</h1>
          <p className="page-subtitle">신청번호를 입력하여 개통 진행 상황을 확인하세요</p>
        </div>

        <div className="search-section">
          <form onSubmit={handleSearch} className="search-form">
            <div className="form-group">
              <label htmlFor="orderNumber" className="form-label">
                신청번호
              </label>
              <input
                type="text"
                id="orderNumber"
                className="form-input"
                placeholder="예: MZ20240101001"
                value={orderNumber}
                onChange={(e) => setOrderNumber(e.target.value)}
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              className="search-button"
              disabled={loading}
            >
              {loading ? '조회중...' : '조회하기'}
            </button>
          </form>
        </div>

        {loading && (
          <div className="loading-container">
            <LoadingSpinner />
            <p className="loading-text">신청 현황을 조회하고 있습니다...</p>
          </div>
        )}

        {error && (
          <div className="error-message">
            <div className="error-icon">⚠️</div>
            <h3 className="error-title">조회 실패</h3>
            <p className="error-text">{error}</p>
            <button
              onClick={() => setError(null)}
              className="retry-button"
            >
              다시 시도
            </button>
          </div>
        )}

        {orderStatus && (
          <div className="order-result">
            <div className="order-header">
              <div>
                <h2 className="order-number">신청번호: {orderStatus.order_number}</h2>
                <p className="order-date">신청일시: {formatDate(orderStatus.created_at)}</p>
              </div>
              <span className={`status-badge status-${orderStatus.status}`}>
                {statusLabels[orderStatus.status] || orderStatus.status}
              </span>
            </div>

            <div className="progress-section">
              <h3 className="progress-title">진행 상황</h3>
              <div className="progress-steps">
                <div className="progress-line">
                  <div 
                    className="progress-line-active"
                    style={{ width: `${getProgressPercentage(orderStatus.status)}%` }}
                  />
                </div>
                {statusSteps.map((step, index) => {
                  const currentIndex = getStatusIndex(orderStatus.status);
                  const isCompleted = index < currentIndex;
                  const isActive = index === currentIndex;
                  
                  return (
                    <div key={step.key} className="progress-step">
                      <div className={`step-circle ${isCompleted ? 'completed' : isActive ? 'active' : ''}`}>
                        {isCompleted ? '✓' : step.icon}
                      </div>
                      <span className={`step-label ${isCompleted ? 'completed' : isActive ? 'active' : ''}`}>
                        {step.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="order-details">
              <div className="detail-card">
                <h4 className="detail-title">
                  👤 신청자 정보
                </h4>
                <div className="detail-item">
                  <span className="detail-label">이름</span>
                  <span className="detail-value">{orderStatus.user_name}</span>
                </div>
              </div>

              <div className="detail-card">
                <h4 className="detail-title">
                  📱 선택 상품
                </h4>
                <div className="detail-item">
                  <span className="detail-label">요금제</span>
                  <span className="detail-value">{orderStatus.plan_name}</span>
                </div>
                {orderStatus.device_name && (
                  <div className="detail-item">
                    <span className="detail-label">단말기</span>
                    <span className="detail-value">{orderStatus.device_name}</span>
                  </div>
                )}
                {orderStatus.number && (
                  <div className="detail-item">
                    <span className="detail-label">전화번호</span>
                    <span className="detail-value">{orderStatus.number}</span>
                  </div>
                )}
              </div>

              <div className="detail-card">
                <h4 className="detail-title">
                  💰 결제 정보
                </h4>
                <div className="detail-item">
                  <span className="detail-label">총 결제금액</span>
                  <span className="detail-value amount-highlight">
                    {formatAmount(orderStatus.total_amount)}원
                  </span>
                </div>
              </div>

              <div className="detail-card">
                <h4 className="detail-title">
                  📋 처리 상태
                </h4>
                <div className="detail-item">
                  <span className="detail-label">현재 상태</span>
                  <span className="detail-value">
                    {statusLabels[orderStatus.status] || orderStatus.status}
                  </span>
                </div>
                {orderStatus.status === 'completed' && (
                  <div className="detail-item">
                    <span className="detail-label">개통 완료</span>
                    <span className="detail-value" style={{ color: '#28a745' }}>
                      서비스 이용 가능
                    </span>
                  </div>
                )}
                {orderStatus.status === 'processing' && (
                  <div className="detail-item">
                    <span className="detail-label">예상 완료</span>
                    <span className="detail-value">1-2 영업일</span>
                  </div>
                )}
              </div>
            </div>

            {orderStatus.status === 'completed' && (
              <div style={{ 
                marginTop: '2rem', 
                padding: '1rem', 
                background: '#d4edda', 
                borderRadius: '8px',
                textAlign: 'center'
              }}>
                <p style={{ color: '#155724', fontWeight: '600', margin: 0 }}>
                  🎉 개통이 완료되었습니다! 서비스를 이용해보세요.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderStatusPage;