// 라우트 상수 정의
export const ROUTES = {
  HOME: '/',
  PLANS: '/plans',
  USER_INFO: '/user-info',
  DEVICES: '/devices',
  NUMBERS: '/numbers',
  SUMMARY: '/summary',
  PAYMENT: '/payment',
  ORDER_STATUS: '/status',
  SUPPORT: '/support',
  ADMIN: '/admin',
  ADMIN_ORDERS: '/admin/orders',
  ADMIN_STATISTICS: '/admin/statistics',
} as const;

// 개통 신청 단계별 라우트
export const ORDER_STEPS = [
  { step: 1, path: ROUTES.PLANS, title: '요금제 선택' },
  { step: 2, path: ROUTES.USER_INFO, title: '개인정보 입력' },
  { step: 3, path: ROUTES.DEVICES, title: '단말기 선택' },
  { step: 4, path: ROUTES.NUMBERS, title: '번호 선택' },
  { step: 5, path: ROUTES.SUMMARY, title: '신청 내역 확인' },
  { step: 6, path: ROUTES.PAYMENT, title: '결제' },
] as const;

// 현재 단계 확인
export const getCurrentStep = (pathname: string): number => {
  const currentRoute = ORDER_STEPS.find(step => step.path === pathname);
  return currentRoute?.step || 0;
};

// 다음 단계 경로 가져오기
export const getNextStepPath = (currentStep: number): string | null => {
  const nextStep = ORDER_STEPS.find(step => step.step === currentStep + 1);
  return nextStep?.path || null;
};

// 이전 단계 경로 가져오기
export const getPrevStepPath = (currentStep: number): string | null => {
  const prevStep = ORDER_STEPS.find(step => step.step === currentStep - 1);
  return prevStep?.path || null;
};

// 단계 제목 가져오기
export const getStepTitle = (step: number): string => {
  const stepInfo = ORDER_STEPS.find(s => s.step === step);
  return stepInfo?.title || '';
};

// 진행률 계산
export const getProgressPercentage = (currentStep: number): number => {
  return Math.round((currentStep / ORDER_STEPS.length) * 100);
};