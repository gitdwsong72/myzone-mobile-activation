import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { useToast } from '../../components/Common/Toast';
import Button from '../../components/Common/Button';
import Modal from '../../components/Common/Modal';
import ProgressBar from '../../components/Common/ProgressBar';
import './UserInfoPage.css';

interface UserInfo {
  name: string;
  birthDate: string;
  gender: 'male' | 'female' | '';
  phone: string;
  email: string;
  address: {
    zipCode: string;
    address1: string;
    address2: string;
  };
}

interface ValidationErrors {
  [key: string]: string;
}

interface AddressSearchResult {
  zipCode: string;
  address: string;
  roadAddress: string;
}

const UserInfoPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { showError, showSuccess, showInfo } = useToast();

  const [userInfo, setUserInfo] = useState<UserInfo>({
    name: '',
    birthDate: '',
    gender: '',
    phone: '',
    email: '',
    address: {
      zipCode: '',
      address1: '',
      address2: '',
    },
  });

  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isVerified, setIsVerified] = useState(false);
  const [verificationMethod, setVerificationMethod] = useState<'sms' | 'certificate' | 'simple' | ''>('');
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [showAddressModal, setShowAddressModal] = useState(false);
  const [addressSearchResults, setAddressSearchResults] = useState<AddressSearchResult[]>([]);
  const [addressSearchQuery, setAddressSearchQuery] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [verificationTimer, setVerificationTimer] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // 실시간 검증
  useEffect(() => {
    validateField('name', userInfo.name);
  }, [userInfo.name]);

  useEffect(() => {
    validateField('birthDate', userInfo.birthDate);
  }, [userInfo.birthDate]);

  useEffect(() => {
    validateField('phone', userInfo.phone);
  }, [userInfo.phone]);

  useEffect(() => {
    validateField('email', userInfo.email);
  }, [userInfo.email]);

  // 인증 타이머
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (verificationTimer > 0) {
      interval = setInterval(() => {
        setVerificationTimer(prev => prev - 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [verificationTimer]);

  const validateField = (field: string, value: string) => {
    const newErrors = { ...errors };

    switch (field) {
      case 'name':
        if (!value.trim()) {
          newErrors.name = '이름을 입력해주세요.';
        } else if (value.length < 2) {
          newErrors.name = '이름은 2글자 이상 입력해주세요.';
        } else if (!/^[가-힣a-zA-Z\s]+$/.test(value)) {
          newErrors.name = '이름은 한글 또는 영문만 입력 가능합니다.';
        } else {
          delete newErrors.name;
        }
        break;

      case 'birthDate':
        if (!value) {
          newErrors.birthDate = '생년월일을 입력해주세요.';
        } else if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
          newErrors.birthDate = '올바른 날짜 형식으로 입력해주세요. (YYYY-MM-DD)';
        } else {
          const date = new Date(value);
          const today = new Date();
          const age = today.getFullYear() - date.getFullYear();
          if (age < 14 || age > 100) {
            newErrors.birthDate = '만 14세 이상 100세 이하만 가입 가능합니다.';
          } else {
            delete newErrors.birthDate;
          }
        }
        break;

      case 'phone':
        if (!value) {
          newErrors.phone = '휴대폰 번호를 입력해주세요.';
        } else if (!/^010-\d{4}-\d{4}$/.test(value)) {
          newErrors.phone = '올바른 휴대폰 번호 형식으로 입력해주세요. (010-0000-0000)';
        } else {
          delete newErrors.phone;
        }
        break;

      case 'email':
        if (!value) {
          newErrors.email = '이메일을 입력해주세요.';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          newErrors.email = '올바른 이메일 형식으로 입력해주세요.';
        } else {
          delete newErrors.email;
        }
        break;
    }

    setErrors(newErrors);
  };

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('address.')) {
      const addressField = field.split('.')[1];
      setUserInfo(prev => ({
        ...prev,
        address: {
          ...prev.address,
          [addressField]: value,
        },
      }));
    } else {
      setUserInfo(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const formatPhoneNumber = (value: string) => {
    const numbers = value.replace(/[^\d]/g, '');
    if (numbers.length <= 3) return numbers;
    if (numbers.length <= 7) return `${numbers.slice(0, 3)}-${numbers.slice(3)}`;
    return `${numbers.slice(0, 3)}-${numbers.slice(3, 7)}-${numbers.slice(7, 11)}`;
  };

  const handlePhoneChange = (value: string) => {
    const formatted = formatPhoneNumber(value);
    handleInputChange('phone', formatted);
  };

  const searchAddress = async (query: string) => {
    if (!query.trim()) {
      showError('검색어를 입력해주세요.');
      return;
    }

    try {
      // 실제로는 다음 우편번호 API나 다른 주소 검색 API를 사용
      // 여기서는 모의 데이터 사용
      const mockResults: AddressSearchResult[] = [
        {
          zipCode: '06292',
          address: '서울특별시 강남구 역삼동 123-45',
          roadAddress: '서울특별시 강남구 테헤란로 123',
        },
        {
          zipCode: '06293',
          address: '서울특별시 강남구 역삼동 678-90',
          roadAddress: '서울특별시 강남구 테헤란로 456',
        },
      ];

      setAddressSearchResults(mockResults);
    } catch (error) {
      showError('주소 검색 중 오류가 발생했습니다.');
    }
  };

  const selectAddress = (result: AddressSearchResult) => {
    setUserInfo(prev => ({
      ...prev,
      address: {
        ...prev.address,
        zipCode: result.zipCode,
        address1: result.roadAddress,
      },
    }));
    setShowAddressModal(false);
    showSuccess('주소가 선택되었습니다.');
  };

  const startVerification = (method: 'sms' | 'certificate' | 'simple') => {
    if (!userInfo.name || !userInfo.birthDate || !userInfo.phone) {
      showError('기본 정보를 먼저 입력해주세요.');
      return;
    }

    setVerificationMethod(method);
    setShowVerificationModal(true);

    if (method === 'sms') {
      // SMS 인증 코드 발송
      setVerificationTimer(180); // 3분
      showInfo('인증번호가 발송되었습니다. 3분 내에 입력해주세요.');
    }
  };

  const verifyCode = () => {
    if (!verificationCode) {
      showError('인증번호를 입력해주세요.');
      return;
    }

    // 실제로는 서버에서 인증번호 검증
    if (verificationCode === '123456') {
      setIsVerified(true);
      setShowVerificationModal(false);
      showSuccess('본인인증이 완료되었습니다.');
    } else {
      showError('인증번호가 올바르지 않습니다.');
    }
  };

  const handleCertificateVerification = () => {
    // 공인인증서 인증 로직 (실제로는 외부 서비스 연동)
    setTimeout(() => {
      setIsVerified(true);
      setShowVerificationModal(false);
      showSuccess('공인인증서 인증이 완료되었습니다.');
    }, 2000);
  };

  const handleSimpleVerification = () => {
    // 간편인증 로직 (카카오, 네이버 등)
    setTimeout(() => {
      setIsVerified(true);
      setShowVerificationModal(false);
      showSuccess('간편인증이 완료되었습니다.');
    }, 1500);
  };

  const validateForm = () => {
    const requiredFields = ['name', 'birthDate', 'gender', 'phone', 'email'];
    const newErrors: ValidationErrors = {};

    requiredFields.forEach(field => {
      if (!userInfo[field as keyof UserInfo]) {
        newErrors[field] = '필수 입력 항목입니다.';
      }
    });

    if (!userInfo.address.zipCode || !userInfo.address.address1) {
      newErrors.address = '주소를 입력해주세요.';
    }

    if (!isVerified) {
      newErrors.verification = '본인인증을 완료해주세요.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      showError('입력 정보를 확인해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      // 실제로는 서버에 사용자 정보 저장
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      showSuccess('개인정보 입력이 완료되었습니다.');
      navigate('/devices');
    } catch (error) {
      showError('정보 저장 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="user-info-page">
      {/* 진행률 표시 */}
      <div className="progress-section">
        <ProgressBar current={2} total={5} />
        <p className="progress-text">2단계: 개인정보 입력 및 본인인증</p>
      </div>

      {/* 페이지 헤더 */}
      <div className="page-header">
        <h1 className="page-title">개인정보 입력</h1>
        <p className="page-description">
          개통에 필요한 정보를 정확히 입력해주세요
        </p>
      </div>

      <div className="form-container">
        <form className="user-info-form" onSubmit={(e) => e.preventDefault()}>
          {/* 기본 정보 섹션 */}
          <div className="form-section">
            <h3 className="section-title">기본 정보</h3>
            
            <div className="form-group">
              <label htmlFor="name" className="form-label">
                이름 <span className="required">*</span>
              </label>
              <input
                type="text"
                id="name"
                className={`form-input ${errors.name ? 'error' : ''}`}
                value={userInfo.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                placeholder="이름을 입력해주세요"
              />
              {errors.name && <span className="error-message">{errors.name}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="birthDate" className="form-label">
                생년월일 <span className="required">*</span>
              </label>
              <input
                type="date"
                id="birthDate"
                className={`form-input ${errors.birthDate ? 'error' : ''}`}
                value={userInfo.birthDate}
                onChange={(e) => handleInputChange('birthDate', e.target.value)}
              />
              {errors.birthDate && <span className="error-message">{errors.birthDate}</span>}
            </div>

            <div className="form-group">
              <label className="form-label">
                성별 <span className="required">*</span>
              </label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="gender"
                    value="male"
                    checked={userInfo.gender === 'male'}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                  />
                  <span className="radio-text">남성</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="gender"
                    value="female"
                    checked={userInfo.gender === 'female'}
                    onChange={(e) => handleInputChange('gender', e.target.value)}
                  />
                  <span className="radio-text">여성</span>
                </label>
              </div>
              {errors.gender && <span className="error-message">{errors.gender}</span>}
            </div>
          </div>

          {/* 연락처 정보 섹션 */}
          <div className="form-section">
            <h3 className="section-title">연락처 정보</h3>
            
            <div className="form-group">
              <label htmlFor="phone" className="form-label">
                휴대폰 번호 <span className="required">*</span>
              </label>
              <input
                type="tel"
                id="phone"
                className={`form-input ${errors.phone ? 'error' : ''}`}
                value={userInfo.phone}
                onChange={(e) => handlePhoneChange(e.target.value)}
                placeholder="010-0000-0000"
                maxLength={13}
              />
              {errors.phone && <span className="error-message">{errors.phone}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="email" className="form-label">
                이메일 <span className="required">*</span>
              </label>
              <input
                type="email"
                id="email"
                className={`form-input ${errors.email ? 'error' : ''}`}
                value={userInfo.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                placeholder="example@email.com"
              />
              {errors.email && <span className="error-message">{errors.email}</span>}
            </div>
          </div>

          {/* 주소 정보 섹션 */}
          <div className="form-section">
            <h3 className="section-title">주소 정보</h3>
            
            <div className="form-group">
              <label className="form-label">
                주소 <span className="required">*</span>
              </label>
              <div className="address-input-group">
                <input
                  type="text"
                  className="form-input address-input"
                  value={userInfo.address.zipCode}
                  placeholder="우편번호"
                  readOnly
                />
                <Button
                  variant="outline"
                  onClick={() => setShowAddressModal(true)}
                  className="address-search-button"
                >
                  주소 검색
                </Button>
              </div>
              <input
                type="text"
                className="form-input"
                value={userInfo.address.address1}
                placeholder="기본 주소"
                readOnly
              />
              <input
                type="text"
                className="form-input"
                value={userInfo.address.address2}
                onChange={(e) => handleInputChange('address.address2', e.target.value)}
                placeholder="상세 주소를 입력해주세요"
              />
              {errors.address && <span className="error-message">{errors.address}</span>}
            </div>
          </div>

          {/* 본인인증 섹션 */}
          <div className="form-section">
            <h3 className="section-title">본인인증</h3>
            
            <div className="verification-section">
              {!isVerified ? (
                <div className="verification-options">
                  <p className="verification-description">
                    개통을 위해 본인인증이 필요합니다. 원하는 방법을 선택해주세요.
                  </p>
                  <div className="verification-buttons">
                    <Button
                      variant="outline"
                      onClick={() => startVerification('sms')}
                      className="verification-button"
                    >
                      <span className="verification-icon">📱</span>
                      <div className="verification-text">
                        <strong>휴대폰 인증</strong>
                        <small>SMS 인증번호</small>
                      </div>
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => startVerification('certificate')}
                      className="verification-button"
                    >
                      <span className="verification-icon">🔐</span>
                      <div className="verification-text">
                        <strong>공인인증서</strong>
                        <small>공인인증서 인증</small>
                      </div>
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => startVerification('simple')}
                      className="verification-button"
                    >
                      <span className="verification-icon">⚡</span>
                      <div className="verification-text">
                        <strong>간편인증</strong>
                        <small>카카오, 네이버</small>
                      </div>
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="verification-complete">
                  <div className="verification-success">
                    <span className="success-icon">✅</span>
                    <div className="success-text">
                      <strong>본인인증 완료</strong>
                      <small>인증이 성공적으로 완료되었습니다.</small>
                    </div>
                  </div>
                </div>
              )}
              {errors.verification && <span className="error-message">{errors.verification}</span>}
            </div>
          </div>

          {/* 제출 버튼 */}
          <div className="form-actions">
            <Button
              variant="outline"
              size="large"
              onClick={() => navigate('/plans')}
              className="back-button"
            >
              이전 단계
            </Button>
            <Button
              variant="primary"
              size="large"
              onClick={handleSubmit}
              loading={isSubmitting}
              disabled={!isVerified || Object.keys(errors).length > 0}
              className="next-button"
            >
              다음 단계
            </Button>
          </div>
        </form>
      </div>

      {/* 주소 검색 모달 */}
      <Modal
        isOpen={showAddressModal}
        onClose={() => setShowAddressModal(false)}
        title="주소 검색"
        size="medium"
      >
        <div className="address-search-modal">
          <div className="search-input-group">
            <input
              type="text"
              className="form-input"
              value={addressSearchQuery}
              onChange={(e) => setAddressSearchQuery(e.target.value)}
              placeholder="도로명 또는 지번 주소를 입력하세요"
              onKeyPress={(e) => e.key === 'Enter' && searchAddress(addressSearchQuery)}
            />
            <Button
              variant="primary"
              onClick={() => searchAddress(addressSearchQuery)}
            >
              검색
            </Button>
          </div>

          <div className="search-results">
            {addressSearchResults.map((result, index) => (
              <div
                key={index}
                className="address-result"
                onClick={() => selectAddress(result)}
              >
                <div className="result-zipcode">[{result.zipCode}]</div>
                <div className="result-address">
                  <div className="road-address">{result.roadAddress}</div>
                  <div className="jibun-address">{result.address}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Modal>

      {/* 본인인증 모달 */}
      <Modal
        isOpen={showVerificationModal}
        onClose={() => setShowVerificationModal(false)}
        title="본인인증"
        size="medium"
      >
        <div className="verification-modal">
          {verificationMethod === 'sms' && (
            <div className="sms-verification">
              <div className="verification-info">
                <p>휴대폰 번호: <strong>{userInfo.phone}</strong></p>
                <p>위 번호로 인증번호를 발송했습니다.</p>
              </div>
              
              <div className="verification-input-group">
                <input
                  type="text"
                  className="form-input"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="인증번호 6자리 입력"
                  maxLength={6}
                />
                {verificationTimer > 0 && (
                  <span className="timer">{formatTimer(verificationTimer)}</span>
                )}
              </div>

              <div className="verification-actions">
                <Button
                  variant="outline"
                  onClick={() => {
                    setVerificationTimer(180);
                    showInfo('인증번호가 재발송되었습니다.');
                  }}
                  disabled={verificationTimer > 120}
                >
                  재발송
                </Button>
                <Button
                  variant="primary"
                  onClick={verifyCode}
                  disabled={!verificationCode || verificationTimer === 0}
                >
                  인증 확인
                </Button>
              </div>
            </div>
          )}

          {verificationMethod === 'certificate' && (
            <div className="certificate-verification">
              <div className="verification-info">
                <p>공인인증서를 이용한 본인인증을 진행합니다.</p>
                <p>인증서를 선택하고 비밀번호를 입력해주세요.</p>
              </div>
              
              <div className="certificate-actions">
                <Button
                  variant="primary"
                  onClick={handleCertificateVerification}
                  className="certificate-button"
                >
                  공인인증서 선택
                </Button>
              </div>
            </div>
          )}

          {verificationMethod === 'simple' && (
            <div className="simple-verification">
              <div className="verification-info">
                <p>간편인증을 통해 본인인증을 진행합니다.</p>
                <p>원하는 서비스를 선택해주세요.</p>
              </div>
              
              <div className="simple-auth-buttons">
                <Button
                  variant="outline"
                  onClick={handleSimpleVerification}
                  className="kakao-button"
                >
                  카카오 인증
                </Button>
                <Button
                  variant="outline"
                  onClick={handleSimpleVerification}
                  className="naver-button"
                >
                  네이버 인증
                </Button>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default UserInfoPage;