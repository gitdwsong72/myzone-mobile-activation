// 데모 모드 설정
export const DEMO_CONFIG = {
  // API 설정
  API_URL: process.env.REACT_APP_API_URL || 'https://myzone-backend-production.up.railway.app/api/v1',
  
  // 데모 모드 여부
  IS_DEMO: process.env.REACT_APP_DEMO_MODE === 'true',
  
  // 데모 사용자 정보
  DEMO_USER: {
    name: '홍길동',
    phone: '010-1234-5678',
    email: 'demo@myzone.com',
    birthDate: '1990-01-01',
    gender: 'M',
    address: '서울특별시 강남구 테헤란로 123'
  },
  
  // 데모 결제 정보
  DEMO_PAYMENT: {
    cardNumber: '1234-5678-9012-3456',
    expiryDate: '12/25',
    cvv: '123',
    cardHolder: '홍길동'
  },
  
  // 데모 메시지
  DEMO_MESSAGES: {
    welcome: '🎉 MyZone 데모 서비스에 오신 것을 환영합니다!',
    notice: '이것은 데모 환경입니다. 실제 결제나 개통은 이루어지지 않습니다.',
    success: '데모 신청이 완료되었습니다! 실제 서비스에서는 진짜 개통이 진행됩니다.'
  },
  
  // 데모 제한사항
  DEMO_LIMITATIONS: [
    '실제 SMS 발송이 되지 않습니다',
    '실제 결제가 처리되지 않습니다',
    '실제 개통이 이루어지지 않습니다',
    '데이터는 임시로 저장됩니다'
  ]
};

// 데모 모드 체크 함수
export const isDemoMode = (): boolean => {
  return DEMO_CONFIG.IS_DEMO || process.env.NODE_ENV === 'development';
};

// 데모 알림 표시 함수
export const showDemoNotice = (): void => {
  if (isDemoMode()) {
    console.log('🎭 Demo Mode Active');
    console.log('📋 Demo Limitations:', DEMO_CONFIG.DEMO_LIMITATIONS);
  }
};