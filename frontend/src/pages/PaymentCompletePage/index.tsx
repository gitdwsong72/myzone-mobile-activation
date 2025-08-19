import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';
import Button from '../../components/Common/Button';
import './PaymentCompletePage.css';

const PaymentCompletePage: React.FC = () => {
  const navigate = useNavigate();
  
  const { selectedPlan, selectedDevice, selectedNumber, userInfo } = useSelector(
    (state: RootState) => state.order
  );

  const [applicationNumber, setApplicationNumber] = useState<string>('');
  const [estimatedActivationDate, setEstimatedActivationDate] = useState<string>('');
  const [showCopyToast, setShowCopyToast] = useState(false);
  const [copyButtonText, setCopyButtonText] = useState('복사');

  // 신청번호 생성 (실제로는 서버에서 받아올 값)
  useEffect(() => {
    const generateApplicationNumber = () => {
      const prefix = 'MZ';
      const timestamp = Date.now().toString().slice(-8);
      const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
      return `${prefix}${timestamp}${random}`;
    };

    // 예상 개통일 계산 (영업일 기준 2-3일)
    const calculateActivationDate = () => {
      const today = new Date();
      const activationDate = new Date(today);
      activationDate.setDate(today.getDate() + 3); // 3일 후
      
      // 주말이면 월요일로 조정
      if (activationDate.getDay() === 0) { // 일요일
        activationDate.setDate(activationDate.getDate() + 1);
      } else if (activationDate.getDay() === 6) { // 토요일
        activationDate.setDate(activationDate.getDate() + 2);
      }
      
      return activationDate.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      });
    };

    setApplicationNumber(generateApplicationNumber());
    setEstimatedActivationDate(calculateActivationDate());
  }, []);

  // 신청번호 복사
  const handleCopyApplicationNumber = async () => {
    try {
      await navigator.clipboard.writeText(applicationNumber);
      setCopyButtonText('복사됨');
      setShowCopyToast(true);
      
      setTimeout(() => {
        setCopyButtonText('복사');
        setShowCopyToast(false);
      }, 2000);
    } catch (error) {
      // 클립보드 API가 지원되지 않는 경우 fallback
      const textArea = document.createElement('textarea');
      textArea.value = applicationNumber;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      setCopyButtonText('복사됨');
      setShowCopyToast(true);
      
      setTimeout(() => {
        setCopyButtonText('복사');
        setShowCopyToast(false);
      }, 2000);
    }
  };

  // 총 금액 계산
  const calculateTotalAmount = () => {
    const planFee = selectedPlan?.monthlyFee || 0;
    const devicePrice = selectedDevice?.price || 0;
    const numberFee = selectedNumber?.additionalFee || 0;
    const activationFee = 10000;
    
    return {
      planFee,
      devicePrice,
      numberFee,
      activationFee,
      total: planFee + devicePrice + numberFee + activationFee,
    };
  };

  const amounts = calculateTotalAmount();

  // 신청 현황 조회 페이지로 이동
  const handleCheckStatus = () => {
    navigate('/order-status');
  };

  // 메인 페이지로 이동
  const handleGoHome = () => {
    navigate('/');
  };

  // 데이터 검증
  if (!selectedPlan || !selectedDevice || !selectedNumber || !userInfo) {
    return (
      <div className="payment-complete-page">
        <div className="payment-complete-container">
          <div className="payment-complete-card">
            <h2>오류가 발생했습니다</h2>
            <p>결제 정보를 찾을 수 없습니다.</p>
            <Button onClick={() => navigate('/')}>처음으로</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-complete-page">
      <div className="payment-complete-container">
        <div className="payment-complete-card">
          {/* 성공 아이콘 */}
          <div className="success-icon-container">
            <div className="success-icon"></div>
          </div>

          {/* 헤더 */}
          <div className="payment-complete-header">
            <h1 className="payment-complete-title">결제가 완료되었습니다!</h1>
            <p className="payment-complete-subtitle">
              MyZone 서비스 신청이 성공적으로 접수되었습니다.<br />
              개통 처리 후 SMS와 이메일로 안내드리겠습니다.
            </p>
          </div>

          {/* 신청번호 섹션 */}
          <div className="application-number-section">
            <div className="application-number-label">신청번호</div>
            <div className="application-number">{applicationNumber}</div>
            <button 
              className={`copy-button ${copyButtonText === '복사됨' ? 'copied' : ''}`}
              onClick={handleCopyApplicationNumber}
            >
              <span className="copy-icon">📋</span>
              {copyButtonText}
            </button>
          </div>

          {/* 예상 개통일 */}
          <div className="activation-date-section">
            <div className="activation-date-header">
              <span className="activation-date-icon">📅</span>
              <h3 className="activation-date-title">예상 개통일</h3>
            </div>
            <div className="activation-date">{estimatedActivationDate}</div>
            <p className="activation-note">
              영업일 기준으로 처리되며, 서류 검토나 재고 상황에 따라 
              1-2일 정도 지연될 수 있습니다.
            </p>
          </div>

          {/* 주문 요약 */}
          <div className="order-summary-section">
            <h3 className="order-summary-header">결제 내역</h3>
            <div className="order-summary-items">
              <div className="order-summary-item">
                <span className="order-item-label">요금제 ({selectedPlan.name})</span>
                <span className="order-item-value">{amounts.planFee.toLocaleString()}원</span>
              </div>
              <div className="order-summary-item">
                <span className="order-item-label">
                  단말기 ({selectedDevice.brand} {selectedDevice.model})
                </span>
                <span className="order-item-value">{amounts.devicePrice.toLocaleString()}원</span>
              </div>
              <div className="order-summary-item">
                <span className="order-item-label">번호 수수료 ({selectedNumber.number})</span>
                <span className="order-item-value">
                  {amounts.numberFee > 0 ? `${amounts.numberFee.toLocaleString()}원` : '무료'}
                </span>
              </div>
              <div className="order-summary-item">
                <span className="order-item-label">개통비</span>
                <span className="order-item-value">{amounts.activationFee.toLocaleString()}원</span>
              </div>
              <div className="order-summary-item">
                <span className="order-item-label">총 결제 금액</span>
                <span className="order-item-value">{amounts.total.toLocaleString()}원</span>
              </div>
            </div>
          </div>

          {/* 다음 단계 안내 */}
          <div className="next-steps-section">
            <h3 className="next-steps-header">다음 단계</h3>
            <ul className="next-steps-list">
              <li className="next-step-item">
                <span className="step-number">1</span>
                <div className="step-content">
                  <div className="step-title">신청 접수 확인</div>
                  <div className="step-description">
                    신청 내용을 검토하고 서류를 확인합니다. (약 1시간 소요)
                  </div>
                </div>
              </li>
              <li className="next-step-item">
                <span className="step-number">2</span>
                <div className="step-content">
                  <div className="step-title">개통 처리</div>
                  <div className="step-description">
                    통신사 시스템에서 번호 개통 및 요금제 설정을 진행합니다.
                  </div>
                </div>
              </li>
              <li className="next-step-item">
                <span className="step-number">3</span>
                <div className="step-content">
                  <div className="step-title">단말기 배송</div>
                  <div className="step-description">
                    선택하신 주소로 단말기를 배송해드립니다. (1-2일 소요)
                  </div>
                </div>
              </li>
              <li className="next-step-item">
                <span className="step-number">4</span>
                <div className="step-content">
                  <div className="step-title">서비스 시작</div>
                  <div className="step-description">
                    단말기 수령 후 즉시 MyZone 서비스를 이용하실 수 있습니다.
                  </div>
                </div>
              </li>
            </ul>
          </div>

          {/* 액션 버튼 */}
          <div className="action-buttons">
            <Button
              variant="primary"
              size="large"
              onClick={handleCheckStatus}
              className="action-button"
            >
              신청 현황 조회
            </Button>
            <Button
              variant="outline"
              size="large"
              onClick={handleGoHome}
              className="action-button"
            >
              메인으로 돌아가기
            </Button>
          </div>

          {/* 고객 지원 정보 */}
          <div className="support-info">
            <div className="support-info-header">
              <span className="support-info-icon">💬</span>
              <h4 className="support-info-title">문의사항이 있으신가요?</h4>
            </div>
            <div className="support-info-content">
              개통 과정에서 궁금한 점이나 문제가 발생하면 언제든지 연락주세요.
              <div className="support-contact">
                <span>고객센터:</span>
                <a href="tel:1588-0000" className="support-phone">1588-0000</a>
                <span>(평일 09:00-18:00)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 복사 완료 토스트 */}
      {showCopyToast && (
        <div className="copy-toast">
          신청번호가 클립보드에 복사되었습니다!
        </div>
      )}
    </div>
  );
};

export default PaymentCompletePage;