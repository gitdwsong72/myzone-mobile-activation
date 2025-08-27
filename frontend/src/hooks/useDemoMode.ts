import { useState, useCallback } from 'react';
import { isDemoMode, DEMO_CONFIG } from '../config/demo';

interface DemoWarningOptions {
  type: 'payment' | 'order' | 'verification' | 'general';
  title?: string;
  message?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

export const useDemoMode = () => {
  const [isWarningOpen, setIsWarningOpen] = useState(false);
  const [warningOptions, setWarningOptions] = useState<DemoWarningOptions>({
    type: 'general'
  });

  // 데모 모드 여부 확인
  const isDemo = isDemoMode();

  // 데모 경고 표시
  const showDemoWarning = useCallback((options: DemoWarningOptions) => {
    if (!isDemo) {
      // 데모 모드가 아니면 바로 확인 콜백 실행
      options.onConfirm?.();
      return;
    }

    setWarningOptions(options);
    setIsWarningOpen(true);
  }, [isDemo]);

  // 데모 경고 닫기
  const closeDemoWarning = useCallback(() => {
    setIsWarningOpen(false);
    warningOptions.onCancel?.();
  }, [warningOptions]);

  // 데모 경고 확인
  const confirmDemoWarning = useCallback(() => {
    setIsWarningOpen(false);
    warningOptions.onConfirm?.();
  }, [warningOptions]);

  // 결제 시도 시 데모 경고
  const handlePaymentAttempt = useCallback((onConfirm: () => void) => {
    showDemoWarning({
      type: 'payment',
      onConfirm
    });
  }, [showDemoWarning]);

  // 주문 시도 시 데모 경고
  const handleOrderAttempt = useCallback((onConfirm: () => void) => {
    showDemoWarning({
      type: 'order',
      onConfirm
    });
  }, [showDemoWarning]);

  // 인증 시도 시 데모 경고
  const handleVerificationAttempt = useCallback((onConfirm: () => void) => {
    showDemoWarning({
      type: 'verification',
      onConfirm
    });
  }, [showDemoWarning]);

  // 데모 데이터 가져오기
  const getDemoData = useCallback((key: keyof typeof DEMO_CONFIG) => {
    return DEMO_CONFIG[key];
  }, []);

  // 데모 메시지 표시
  const showDemoMessage = useCallback((message: string) => {
    if (isDemo) {
      console.log(`🎭 Demo: ${message}`);
    }
  }, [isDemo]);

  return {
    // 상태
    isDemo,
    isWarningOpen,
    warningOptions,
    
    // 경고 관련 함수
    showDemoWarning,
    closeDemoWarning,
    confirmDemoWarning,
    
    // 특정 액션 핸들러
    handlePaymentAttempt,
    handleOrderAttempt,
    handleVerificationAttempt,
    
    // 유틸리티 함수
    getDemoData,
    showDemoMessage
  };
};