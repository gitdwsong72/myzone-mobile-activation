import React, { useState, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState } from '../../store/store';
import { prevStep, nextStep } from '../../store/slices/orderSlice';
import Button from '../../components/Common/Button';
import ProgressBar from '../../components/Common/ProgressBar';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import DemoWarningModal from '../../components/Common/DemoWarningModal';
import { useDemoMode } from '../../hooks/useDemoMode';
import { DEMO_CONFIG } from '../../config/demo';
import './PaymentPage.css';

interface PaymentMethod {
  id: string;
  name: string;
  description: string;
  icon: string;
}

interface InstallmentOption {
  months: number;
  monthlyAmount: number;
  totalAmount: number;
  interestRate: number;
}

interface PaymentForm {
  cardNumber: string;
  expiryDate: string;
  cvv: string;
  cardholderName: string;
  birthDate: string;
  password: string;
}

const PaymentPage: React.FC = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  
  const { selectedPlan, selectedDevice, selectedNumber, userInfo, currentStep } = useSelector(
    (state: RootState) => state.order
  );

  // 데모 모드 훅
  const {
    isDemo,
    isWarningOpen,
    warningOptions,
    handlePaymentAttempt,
    closeDemoWarning,
    confirmDemoWarning
  } = useDemoMode();

  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>('card');
  const [selectedInstallment, setSelectedInstallment] = useState<number>(0);
  const [paymentForm, setPaymentForm] = useState<PaymentForm>({
    cardNumber: '',
    expiryDate: '',
    cvv: '',
    cardholderName: '',
    birthDate: '',
    password: '',
  });
  const [formErrors, setFormErrors] = useState<Partial<PaymentForm>>({});
  const [isProcessing, setIsProcessing] = useState(false);

  const paymentMethods: PaymentMethod[] = [
    {
      id: 'card',
      name: '신용카드/체크카드',
      description: '국내 모든 카드사 이용 가능',
      icon: '💳',
    },
    {
      id: 'account',
      name: '계좌이체',
      description: '실시간 계좌이체로 즉시 결제',
      icon: '🏦',
    },
    {
      id: 'kakaopay',
      name: '카카오페이',
      description: '간편하고 안전한 모바일 결제',
      icon: '💛',
    },
    {
      id: 'naverpay',
      name: '네이버페이',
      description: '네이버 간편결제 서비스',
      icon: '💚',
    },
  ];

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

  // 할부 옵션 계산
  const calculateInstallmentOptions = (): InstallmentOption[] => {
    const devicePrice = selectedDevice?.price || 0;
    const options: InstallmentOption[] = [
      { months: 0, monthlyAmount: devicePrice, totalAmount: devicePrice, interestRate: 0 },
    ];

    // 2개월부터 36개월까지 할부 옵션
    for (let months = 2; months <= 36; months++) {
      const interestRate = months <= 12 ? 0 : 0.05; // 12개월 이하 무이자
      const totalAmount = devicePrice * (1 + interestRate);
      const monthlyAmount = Math.round(totalAmount / months);
      
      options.push({
        months,
        monthlyAmount,
        totalAmount,
        interestRate,
      });
    }

    return options;
  };

  const installmentOptions = calculateInstallmentOptions();

  // 데모 모드에서 폼 자동 채우기
  useEffect(() => {
    if (isDemo && selectedPaymentMethod === 'card') {
      setPaymentForm({
        cardNumber: DEMO_CONFIG.DEMO_PAYMENT.cardNumber,
        expiryDate: DEMO_CONFIG.DEMO_PAYMENT.expiryDate,
        cvv: DEMO_CONFIG.DEMO_PAYMENT.cvv,
        cardholderName: DEMO_CONFIG.DEMO_PAYMENT.cardHolder,
        birthDate: '900101',
        password: '12',
      });
    }
  }, [isDemo, selectedPaymentMethod]);

  // 폼 입력 처리
  const handleFormChange = (field: keyof PaymentForm, value: string) => {
    setPaymentForm(prev => ({ ...prev, [field]: value }));
    
    // 에러 클리어
    if (formErrors[field]) {
      setFormErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  // 카드번호 포맷팅
  const formatCardNumber = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    const formatted = cleaned.replace(/(\d{4})(?=\d)/g, '$1-');
    return formatted.slice(0, 19); // 0000-0000-0000-0000
  };

  // 유효기간 포맷팅
  const formatExpiryDate = (value: string) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length >= 2) {
      return cleaned.slice(0, 2) + '/' + cleaned.slice(2, 4);
    }
    return cleaned;
  };

  // 폼 검증
  const validateForm = (): boolean => {
    const errors: Partial<PaymentForm> = {};

    if (selectedPaymentMethod === 'card') {
      if (!paymentForm.cardNumber || paymentForm.cardNumber.replace(/\D/g, '').length !== 16) {
        errors.cardNumber = '올바른 카드번호를 입력해주세요';
      }
      if (!paymentForm.expiryDate || !/^\d{2}\/\d{2}$/.test(paymentForm.expiryDate)) {
        errors.expiryDate = '올바른 유효기간을 입력해주세요 (MM/YY)';
      }
      if (!paymentForm.cvv || paymentForm.cvv.length !== 3) {
        errors.cvv = '올바른 CVV를 입력해주세요';
      }
      if (!paymentForm.cardholderName.trim()) {
        errors.cardholderName = '카드소유자명을 입력해주세요';
      }
      if (!paymentForm.birthDate || paymentForm.birthDate.length !== 6) {
        errors.birthDate = '생년월일 6자리를 입력해주세요';
      }
      if (!paymentForm.password || paymentForm.password.length !== 2) {
        errors.password = '카드 비밀번호 앞 2자리를 입력해주세요';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // 실제 결제 처리 로직
  const processPayment = async () => {
    setIsProcessing(true);

    try {
      // 실제 PG사 연동 로직이 들어갈 부분
      // 여기서는 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 3000));

      // 결제 성공 시 다음 단계로
      dispatch(nextStep());
      navigate('/payment-complete');
    } catch (error) {
      alert('결제 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setIsProcessing(false);
    }
  };

  // 결제 처리 (데모 경고 포함)
  const handlePayment = () => {
    if (!validateForm()) {
      return;
    }

    // 데모 모드에서는 경고 표시 후 진행
    handlePaymentAttempt(processPayment);
  };

  // 이전 단계로 이동
  const handlePrevStep = () => {
    dispatch(prevStep());
    navigate('/order-summary');
  };

  // 데이터 검증
  if (!selectedPlan || !selectedDevice || !selectedNumber || !userInfo) {
    return (
      <div className="payment-page">
        <div className="payment-container">
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
    <div className="payment-page">
      <div className="payment-container">
        {/* 헤더 */}
        <div className="payment-header">
          <h1 className="payment-title">결제</h1>
          <p className="payment-subtitle">
            결제 방법을 선택하고 결제 정보를 입력해주세요
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

        {/* 결제 내용 */}
        <div className="payment-content">
          {/* 결제 방법 및 정보 입력 */}
          <div className="payment-methods-section">
            <div className="payment-methods-header">
              <span className="payment-methods-icon">💳</span>
              <h2 className="payment-methods-title">결제 방법</h2>
            </div>

            {/* 결제 방법 선택 */}
            <div className="payment-methods-list">
              {paymentMethods.map((method) => (
                <div
                  key={method.id}
                  className={`payment-method-item ${
                    selectedPaymentMethod === method.id ? 'selected' : ''
                  }`}
                  onClick={() => setSelectedPaymentMethod(method.id)}
                >
                  <input
                    type="radio"
                    id={`payment-${method.id}`}
                    name="paymentMethod"
                    value={method.id}
                    checked={selectedPaymentMethod === method.id}
                    onChange={() => setSelectedPaymentMethod(method.id)}
                    className="payment-method-radio"
                  />
                  <div className="payment-method-info">
                    <div className="payment-method-name">{method.name}</div>
                    <div className="payment-method-description">{method.description}</div>
                  </div>
                  <span className="payment-method-icon">{method.icon}</span>
                </div>
              ))}
            </div>

            {/* 할부 옵션 (카드 결제 시에만) */}
            {selectedPaymentMethod === 'card' && (
              <div className="installment-section">
                <h3 className="installment-header">할부 선택</h3>
                <div className="installment-options">
                  {installmentOptions.slice(0, 13).map((option) => (
                    <div
                      key={option.months}
                      className={`installment-option ${
                        selectedInstallment === option.months ? 'selected' : ''
                      }`}
                      onClick={() => setSelectedInstallment(option.months)}
                    >
                      <div className="installment-months">
                        {option.months === 0 ? '일시불' : `${option.months}개월`}
                      </div>
                      <div className="installment-amount">
                        {option.months === 0 
                          ? '무이자' 
                          : `월 ${option.monthlyAmount.toLocaleString()}원`
                        }
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 결제 정보 입력 (카드 결제 시에만) */}
            {selectedPaymentMethod === 'card' && (
              <div className="payment-form-section">
                <h3 className="payment-form-header">카드 정보 입력</h3>
                <form className="payment-form">
                  {isDemo && (
                    <div className="demo-form-notice">
                      🎭 <strong>데모 모드:</strong> 결제 정보가 자동으로 입력되었습니다. 실제 결제는 이루어지지 않습니다.
                    </div>
                  )}
                  
                  <div className="form-group">
                    <label htmlFor="cardNumber" className="form-label">
                      카드번호 *
                    </label>
                    <input
                      type="text"
                      id="cardNumber"
                      className={`form-input ${formErrors.cardNumber ? 'error' : ''}`}
                      placeholder="0000-0000-0000-0000"
                      value={paymentForm.cardNumber}
                      onChange={(e) => handleFormChange('cardNumber', formatCardNumber(e.target.value))}
                      maxLength={19}
                    />
                    {formErrors.cardNumber && (
                      <div className="form-error">{formErrors.cardNumber}</div>
                    )}
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="expiryDate" className="form-label">
                        유효기간 *
                      </label>
                      <input
                        type="text"
                        id="expiryDate"
                        className={`form-input ${formErrors.expiryDate ? 'error' : ''}`}
                        placeholder="MM/YY"
                        value={paymentForm.expiryDate}
                        onChange={(e) => handleFormChange('expiryDate', formatExpiryDate(e.target.value))}
                        maxLength={5}
                      />
                      {formErrors.expiryDate && (
                        <div className="form-error">{formErrors.expiryDate}</div>
                      )}
                    </div>

                    <div className="form-group">
                      <label htmlFor="cvv" className="form-label">
                        CVV *
                      </label>
                      <input
                        type="password"
                        id="cvv"
                        className={`form-input ${formErrors.cvv ? 'error' : ''}`}
                        placeholder="000"
                        value={paymentForm.cvv}
                        onChange={(e) => handleFormChange('cvv', e.target.value.replace(/\D/g, '').slice(0, 3))}
                        maxLength={3}
                      />
                      {formErrors.cvv && (
                        <div className="form-error">{formErrors.cvv}</div>
                      )}
                    </div>
                  </div>

                  <div className="form-group">
                    <label htmlFor="cardholderName" className="form-label">
                      카드소유자명 *
                    </label>
                    <input
                      type="text"
                      id="cardholderName"
                      className={`form-input ${formErrors.cardholderName ? 'error' : ''}`}
                      placeholder="카드에 표시된 이름을 입력하세요"
                      value={paymentForm.cardholderName}
                      onChange={(e) => handleFormChange('cardholderName', e.target.value)}
                    />
                    {formErrors.cardholderName && (
                      <div className="form-error">{formErrors.cardholderName}</div>
                    )}
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label htmlFor="birthDate" className="form-label">
                        생년월일 *
                      </label>
                      <input
                        type="text"
                        id="birthDate"
                        className={`form-input ${formErrors.birthDate ? 'error' : ''}`}
                        placeholder="YYMMDD"
                        value={paymentForm.birthDate}
                        onChange={(e) => handleFormChange('birthDate', e.target.value.replace(/\D/g, '').slice(0, 6))}
                        maxLength={6}
                      />
                      {formErrors.birthDate && (
                        <div className="form-error">{formErrors.birthDate}</div>
                      )}
                    </div>

                    <div className="form-group">
                      <label htmlFor="password" className="form-label">
                        비밀번호 앞 2자리 *
                      </label>
                      <input
                        type="password"
                        id="password"
                        className={`form-input ${formErrors.password ? 'error' : ''}`}
                        placeholder="**"
                        value={paymentForm.password}
                        onChange={(e) => handleFormChange('password', e.target.value.replace(/\D/g, '').slice(0, 2))}
                        maxLength={2}
                      />
                      {formErrors.password && (
                        <div className="form-error">{formErrors.password}</div>
                      )}
                    </div>
                  </div>
                </form>
              </div>
            )}
          </div>

          {/* 결제 요약 사이드바 */}
          <div className="payment-summary">
            <div className="payment-summary-header">
              <span className="payment-summary-icon">📋</span>
              <h2 className="payment-summary-title">결제 요약</h2>
            </div>

            {/* 선택 항목 요약 */}
            <div className="selected-items">
              <div className="selected-item">
                <div className="selected-item-info">
                  <div className="selected-item-name">{selectedPlan.name}</div>
                  <div className="selected-item-details">월 요금</div>
                </div>
                <div className="selected-item-price">
                  {selectedPlan.monthlyFee.toLocaleString()}원
                </div>
              </div>

              <div className="selected-item">
                <div className="selected-item-info">
                  <div className="selected-item-name">
                    {selectedDevice.brand} {selectedDevice.model}
                  </div>
                  <div className="selected-item-details">
                    {selectedDevice.color} • 단말기
                  </div>
                </div>
                <div className="selected-item-price">
                  {selectedDevice.price.toLocaleString()}원
                </div>
              </div>

              <div className="selected-item">
                <div className="selected-item-info">
                  <div className="selected-item-name">{selectedNumber.number}</div>
                  <div className="selected-item-details">번호 수수료</div>
                </div>
                <div className="selected-item-price">
                  {selectedNumber.additionalFee > 0 
                    ? `${selectedNumber.additionalFee.toLocaleString()}원`
                    : '무료'
                  }
                </div>
              </div>
            </div>

            {/* 금액 상세 */}
            <div className="amount-details">
              <div className="amount-row">
                <span className="amount-label">월 요금</span>
                <span className="amount-value">{amounts.planFee.toLocaleString()}원</span>
              </div>
              <div className="amount-row">
                <span className="amount-label">단말기 가격</span>
                <span className="amount-value">{amounts.devicePrice.toLocaleString()}원</span>
              </div>
              <div className="amount-row">
                <span className="amount-label">번호 수수료</span>
                <span className="amount-value">{amounts.numberFee.toLocaleString()}원</span>
              </div>
              <div className="amount-row">
                <span className="amount-label">개통비</span>
                <span className="amount-value">{amounts.activationFee.toLocaleString()}원</span>
              </div>
              <div className="amount-row total">
                <span className="amount-label">총 결제 금액</span>
                <span className="amount-value">{amounts.total.toLocaleString()}원</span>
              </div>
            </div>

            {/* 할부 정보 */}
            {selectedPaymentMethod === 'card' && selectedInstallment > 0 && (
              <div className="installment-info">
                <div className="installment-info-title">
                  {selectedInstallment}개월 할부 선택
                </div>
                <div className="installment-info-details">
                  월 {installmentOptions.find(opt => opt.months === selectedInstallment)?.monthlyAmount.toLocaleString()}원씩 {selectedInstallment}개월간 결제
                  {selectedInstallment <= 12 && <br />}
                  {selectedInstallment <= 12 && '무이자 할부'}
                </div>
              </div>
            )}

            {/* 액션 버튼 */}
            <div className="payment-actions">
              <Button
                variant="primary"
                size="large"
                onClick={handlePayment}
                disabled={isProcessing}
                loading={isProcessing}
                className="payment-button"
              >
                {isProcessing ? '결제 처리 중...' : `${amounts.total.toLocaleString()}원 결제하기`}
              </Button>
              
              <Button
                variant="secondary"
                size="medium"
                onClick={handlePrevStep}
                disabled={isProcessing}
                className="back-button"
              >
                이전 단계
              </Button>
            </div>

            {/* 보안 정보 */}
            <div className="security-info">
              <span className="security-icon">🔒</span>
              <span className="security-text">
                SSL 보안 연결로 안전하게 보호됩니다
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 결제 처리 중 로딩 */}
      {isProcessing && (
        <div className="payment-loading">
          <div className="payment-loading-content">
            <div className="payment-loading-spinner">
              <LoadingSpinner />
            </div>
            <div className="payment-loading-text">
              {isDemo ? '데모 결제를 처리하고 있습니다...' : '결제를 처리하고 있습니다...'}
            </div>
          </div>
        </div>
      )}

      {/* 데모 경고 모달 */}
      <DemoWarningModal
        isOpen={isWarningOpen}
        onClose={closeDemoWarning}
        onConfirm={confirmDemoWarning}
        type={warningOptions.type}
        title={warningOptions.title}
        message={warningOptions.message}
      />
    </div>
  );
};

export default PaymentPage;