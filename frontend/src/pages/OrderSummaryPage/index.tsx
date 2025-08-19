import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';
import { nextStep, prevStep } from '../../store/slices/orderSlice';
import Button from '../../components/Common/Button';
import Modal from '../../components/Common/Modal';
import ProgressBar from '../../components/Common/ProgressBar';
import './OrderSummaryPage.css';

interface TermsItem {
  id: string;
  title: string;
  description: string;
  content: string;
  required: boolean;
  agreed: boolean;
}

const OrderSummaryPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const { selectedPlan, selectedDevice, selectedNumber, userInfo, currentStep } = useSelector(
    (state: RootState) => state.order
  );

  const [terms, setTerms] = useState<TermsItem[]>([
    {
      id: 'service',
      title: '통신서비스 이용약관',
      description: 'MyZone 통신서비스 이용에 관한 기본 약관입니다.',
      content: '통신서비스 이용약관 전문...',
      required: true,
      agreed: false,
    },
    {
      id: 'privacy',
      title: '개인정보 수집·이용 동의',
      description: '서비스 제공을 위한 개인정보 수집 및 이용에 대한 동의입니다.',
      content: '개인정보 수집·이용 동의서 전문...',
      required: true,
      agreed: false,
    },
    {
      id: 'location',
      title: '위치정보 이용약관',
      description: '위치기반 서비스 제공을 위한 위치정보 이용 약관입니다.',
      content: '위치정보 이용약관 전문...',
      required: true,
      agreed: false,
    },
    {
      id: 'marketing',
      title: '마케팅 정보 수신 동의',
      description: '이벤트, 혜택 정보 등 마케팅 목적의 정보 수신 동의입니다.',
      content: '마케팅 정보 수신 동의서 전문...',
      required: false,
      agreed: false,
    },
    {
      id: 'thirdparty',
      title: '제3자 정보 제공 동의',
      description: '서비스 제공을 위한 제3자 정보 제공에 대한 동의입니다.',
      content: '제3자 정보 제공 동의서 전문...',
      required: false,
      agreed: false,
    },
  ]);

  const [allAgreed, setAllAgreed] = useState(false);
  const [selectedTerms, setSelectedTerms] = useState<TermsItem | null>(null);
  const [showTermsModal, setShowTermsModal] = useState(false);

  // 전체 동의 상태 업데이트
  useEffect(() => {
    const requiredTerms = terms.filter(term => term.required);
    const allRequiredAgreed = requiredTerms.every(term => term.agreed);
    setAllAgreed(allRequiredAgreed);
  }, [terms]);

  // 개별 약관 동의 처리
  const handleTermsChange = (termId: string, agreed: boolean) => {
    setTerms(prev => prev.map(term => 
      term.id === termId ? { ...term, agreed } : term
    ));
  };

  // 전체 동의 처리
  const handleAllAgreeChange = (agreed: boolean) => {
    setTerms(prev => prev.map(term => ({ ...term, agreed })));
  };

  // 약관 내용 보기
  const handleViewTerms = (term: TermsItem) => {
    setSelectedTerms(term);
    setShowTermsModal(true);
  };

  // 정보 수정 페이지로 이동
  const handleEditInfo = (section: string) => {
    switch (section) {
      case 'plan':
        navigate('/plans');
        break;
      case 'device':
        navigate('/devices');
        break;
      case 'number':
        navigate('/numbers');
        break;
      case 'user':
        navigate('/user-info');
        break;
      default:
        break;
    }
  };

  // 이전 단계로 이동
  const handlePrevStep = () => {
    dispatch(prevStep());
    navigate('/numbers');
  };

  // 다음 단계로 이동 (결제)
  const handleNextStep = () => {
    if (!allAgreed) {
      alert('필수 약관에 동의해주세요.');
      return;
    }
    
    dispatch(nextStep());
    navigate('/payment');
  };

  // 총 금액 계산
  const calculateTotalAmount = () => {
    const planFee = selectedPlan?.monthlyFee || 0;
    const devicePrice = selectedDevice?.price || 0;
    const numberFee = selectedNumber?.additionalFee || 0;
    const activationFee = 10000; // 개통비
    
    return {
      planFee,
      devicePrice,
      numberFee,
      activationFee,
      total: planFee + devicePrice + numberFee + activationFee,
    };
  };

  const amounts = calculateTotalAmount();

  // 데이터 검증
  if (!selectedPlan || !selectedDevice || !selectedNumber || !userInfo) {
    return (
      <div className="order-summary-page">
        <div className="order-summary-container">
          <div className="text-center">
            <h2>선택된 정보가 없습니다</h2>
            <p>처음부터 다시 시작해주세요.</p>
            <Button onClick={() => navigate('/')}>처음으로</Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="order-summary-page">
      <div className="order-summary-container">
        {/* 헤더 */}
        <div className="order-summary-header">
          <h1 className="order-summary-title">신청 내역 확인</h1>
          <p className="order-summary-subtitle">
            선택하신 내용을 확인하고 약관에 동의해주세요
          </p>
        </div>

        {/* 진행률 바 */}
        <div className="progress-section">
          <ProgressBar 
            current={currentStep} 
            total={6} 
            steps={['요금제', '개인정보', '단말기', '번호', '확인', '결제']}
          />
        </div>

        {/* 선택 항목 요약 카드들 */}
        <div className="summary-cards">
          {/* 요금제 카드 */}
          <div className="summary-card">
            <div className="summary-card-header">
              <h2 className="summary-card-title">
                <span className="summary-card-icon">📱</span>
                요금제
              </h2>
              <button 
                className="edit-link"
                onClick={() => handleEditInfo('plan')}
              >
                수정
              </button>
            </div>
            <div className="summary-card-content">
              <div className="plan-summary">
                <div className="plan-info">
                  <h3>{selectedPlan.name}</h3>
                  <div className="plan-features">
                    <div className="plan-feature">
                      <div className="plan-feature-label">데이터</div>
                      <div className="plan-feature-value">{selectedPlan.dataLimit}</div>
                    </div>
                    <div className="plan-feature">
                      <div className="plan-feature-label">통화</div>
                      <div className="plan-feature-value">{selectedPlan.callMinutes}분</div>
                    </div>
                    <div className="plan-feature">
                      <div className="plan-feature-label">문자</div>
                      <div className="plan-feature-value">{selectedPlan.smsCount}건</div>
                    </div>
                  </div>
                </div>
                <div className="plan-price">
                  <div className="plan-monthly-fee">
                    {selectedPlan.monthlyFee.toLocaleString()}원
                  </div>
                  <div className="plan-price-label">월 요금</div>
                </div>
              </div>
            </div>
          </div>

          {/* 단말기 카드 */}
          <div className="summary-card">
            <div className="summary-card-header">
              <h2 className="summary-card-title">
                <span className="summary-card-icon">📱</span>
                단말기
              </h2>
              <button 
                className="edit-link"
                onClick={() => handleEditInfo('device')}
              >
                수정
              </button>
            </div>
            <div className="summary-card-content">
              <div className="device-summary">
                <img 
                  src={selectedDevice.imageUrl || '/images/device-placeholder.png'} 
                  alt={selectedDevice.model}
                  className="device-image"
                />
                <div className="device-info">
                  <h3>{selectedDevice.brand} {selectedDevice.model}</h3>
                  <div className="device-specs">
                    <span className="device-spec">{selectedDevice.color}</span>
                    <span className="device-spec">128GB</span>
                  </div>
                </div>
                <div className="device-price">
                  <div className="device-total-price">
                    {selectedDevice.price.toLocaleString()}원
                  </div>
                  <div className="device-installment">
                    24개월 할부 시 월 {Math.round(selectedDevice.price / 24).toLocaleString()}원
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 번호 카드 */}
          <div className="summary-card">
            <div className="summary-card-header">
              <h2 className="summary-card-title">
                <span className="summary-card-icon">📞</span>
                전화번호
              </h2>
              <button 
                className="edit-link"
                onClick={() => handleEditInfo('number')}
              >
                수정
              </button>
            </div>
            <div className="summary-card-content">
              <div className="number-summary">
                <div className="number-info">
                  <h3>{selectedNumber.number}</h3>
                  <span className="number-category">{selectedNumber.category}</span>
                </div>
                <div className="number-fee">
                  <div className="number-additional-fee">
                    {selectedNumber.additionalFee > 0 
                      ? `+${selectedNumber.additionalFee.toLocaleString()}원`
                      : '무료'
                    }
                  </div>
                  <div className="number-fee-label">번호 수수료</div>
                </div>
              </div>
            </div>
          </div>

          {/* 사용자 정보 카드 */}
          <div className="summary-card">
            <div className="summary-card-header">
              <h2 className="summary-card-title">
                <span className="summary-card-icon">👤</span>
                개인정보
              </h2>
              <button 
                className="edit-link"
                onClick={() => handleEditInfo('user')}
              >
                수정
              </button>
            </div>
            <div className="summary-card-content">
              <div className="user-info-grid">
                <div className="user-info-item">
                  <div className="user-info-label">이름</div>
                  <div className="user-info-value">{userInfo.name}</div>
                </div>
                <div className="user-info-item">
                  <div className="user-info-label">연락처</div>
                  <div className="user-info-value">{userInfo.phone}</div>
                </div>
                <div className="user-info-item">
                  <div className="user-info-label">이메일</div>
                  <div className="user-info-value">{userInfo.email}</div>
                </div>
                <div className="user-info-item">
                  <div className="user-info-label">생년월일</div>
                  <div className="user-info-value">{userInfo.birthDate}</div>
                </div>
                <div className="user-info-item">
                  <div className="user-info-label">성별</div>
                  <div className="user-info-value">{userInfo.gender}</div>
                </div>
                <div className="user-info-item">
                  <div className="user-info-label">주소</div>
                  <div className="user-info-value">{userInfo.address}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 총 금액 섹션 */}
        <div className="total-amount-section">
          <div className="total-amount-header">
            <span className="total-amount-icon">💰</span>
            <h2 className="total-amount-title">결제 금액</h2>
          </div>
          <div className="amount-breakdown">
            <div className="amount-item">
              <span className="amount-label">월 요금</span>
              <span className="amount-value">{amounts.planFee.toLocaleString()}원</span>
            </div>
            <div className="amount-item">
              <span className="amount-label">단말기 가격</span>
              <span className="amount-value">{amounts.devicePrice.toLocaleString()}원</span>
            </div>
            <div className="amount-item">
              <span className="amount-label">번호 수수료</span>
              <span className="amount-value">{amounts.numberFee.toLocaleString()}원</span>
            </div>
            <div className="amount-item">
              <span className="amount-label">개통비</span>
              <span className="amount-value">{amounts.activationFee.toLocaleString()}원</span>
            </div>
            <div className="amount-item total">
              <span className="amount-label">총 결제 금액</span>
              <span className="amount-value">{amounts.total.toLocaleString()}원</span>
            </div>
          </div>
        </div>

        {/* 약관 동의 섹션 */}
        <div className="terms-section">
          <div className="terms-header">
            <h2 className="terms-title">
              <span className="terms-icon">📋</span>
              약관 동의
            </h2>
          </div>

          {/* 전체 동의 */}
          <div className="terms-all-agree">
            <div className="terms-all-agree-content">
              <input
                type="checkbox"
                id="all-agree"
                className="terms-all-checkbox"
                checked={terms.every(term => term.agreed)}
                onChange={(e) => handleAllAgreeChange(e.target.checked)}
              />
              <label htmlFor="all-agree" className="terms-all-label">
                전체 약관에 동의합니다
              </label>
            </div>
          </div>

          {/* 개별 약관 목록 */}
          <div className="terms-list">
            {terms.map((term) => (
              <div 
                key={term.id} 
                className={`terms-item ${term.required ? 'required' : 'optional'}`}
              >
                <input
                  type="checkbox"
                  id={`terms-${term.id}`}
                  className="terms-checkbox"
                  checked={term.agreed}
                  onChange={(e) => handleTermsChange(term.id, e.target.checked)}
                />
                <div className="terms-content">
                  <label htmlFor={`terms-${term.id}`} className="terms-label">
                    {term.title}
                    {term.required ? (
                      <span className="terms-required-badge">필수</span>
                    ) : (
                      <span className="terms-optional-badge">선택</span>
                    )}
                  </label>
                  <p className="terms-description">{term.description}</p>
                  <div className="terms-actions">
                    <button
                      className="terms-view-btn"
                      onClick={() => handleViewTerms(term)}
                    >
                      전문보기
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="action-buttons">
          <Button
            variant="secondary"
            size="large"
            onClick={handlePrevStep}
            className="action-button"
          >
            이전 단계
          </Button>
          <Button
            variant="primary"
            size="large"
            onClick={handleNextStep}
            disabled={!allAgreed}
            className="action-button"
          >
            결제하기
          </Button>
        </div>
      </div>

      {/* 약관 내용 모달 */}
      <Modal
        isOpen={showTermsModal}
        onClose={() => setShowTermsModal(false)}
        title={selectedTerms?.title}
        size="large"
      >
        <div style={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
          {selectedTerms?.content}
        </div>
      </Modal>
    </div>
  );
};

export default OrderSummaryPage;