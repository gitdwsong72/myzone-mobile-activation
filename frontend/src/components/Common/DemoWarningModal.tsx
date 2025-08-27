import React from 'react';
import { isDemoMode, DEMO_CONFIG } from '../../config/demo';
import Modal from './Modal';
import Button from './Button';
import './DemoWarningModal.css';

interface DemoWarningModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  type: 'payment' | 'order' | 'verification' | 'general';
  title?: string;
  message?: string;
}

const DemoWarningModal: React.FC<DemoWarningModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  type,
  title,
  message
}) => {
  // 데모 모드가 아니면 렌더링하지 않음
  if (!isDemoMode()) {
    return null;
  }

  const getWarningContent = () => {
    switch (type) {
      case 'payment':
        return {
          title: title || '⚠️ 데모 결제 안내',
          message: message || '이것은 데모 환경입니다. 실제 결제가 이루어지지 않으며, 카드 정보도 저장되지 않습니다.',
          details: [
            '실제 금액이 청구되지 않습니다',
            '카드 정보는 저장되지 않습니다',
            '결제 과정은 시뮬레이션됩니다',
            '데모용 결제 정보를 사용해주세요'
          ],
          confirmText: '데모 결제 진행',
          icon: '💳'
        };
      
      case 'order':
        return {
          title: title || '⚠️ 데모 주문 안내',
          message: message || '이것은 데모 환경입니다. 실제 주문이 처리되지 않으며, 개통도 이루어지지 않습니다.',
          details: [
            '실제 개통이 이루어지지 않습니다',
            'SMS 인증이 발송되지 않습니다',
            '주문 정보는 임시로 저장됩니다',
            '실제 서비스 이용은 불가능합니다'
          ],
          confirmText: '데모 주문 진행',
          icon: '📱'
        };
      
      case 'verification':
        return {
          title: title || '⚠️ 데모 인증 안내',
          message: message || '이것은 데모 환경입니다. 실제 SMS나 이메일 인증이 발송되지 않습니다.',
          details: [
            'SMS 인증번호가 발송되지 않습니다',
            '이메일 인증이 발송되지 않습니다',
            '인증 과정은 시뮬레이션됩니다',
            '데모용 인증번호를 사용해주세요'
          ],
          confirmText: '데모 인증 진행',
          icon: '📧'
        };
      
      default:
        return {
          title: title || '⚠️ 데모 모드 안내',
          message: message || DEMO_CONFIG.DEMO_MESSAGES.notice,
          details: DEMO_CONFIG.DEMO_LIMITATIONS,
          confirmText: '계속 진행',
          icon: '🎭'
        };
    }
  };

  const content = getWarningContent();

  return (
    <Modal isOpen={isOpen} onClose={onClose} className="demo-warning-modal">
      <div className="demo-warning-content">
        <div className="demo-warning-header">
          <div className="demo-warning-icon">
            {content.icon}
          </div>
          <h2 className="demo-warning-title">
            {content.title}
          </h2>
        </div>
        
        <div className="demo-warning-body">
          <p className="demo-warning-message">
            {content.message}
          </p>
          
          <div className="demo-warning-details">
            <h4>주의사항:</h4>
            <ul>
              {content.details.map((detail, index) => (
                <li key={index}>{detail}</li>
              ))}
            </ul>
          </div>
          
          <div className="demo-warning-note">
            <strong>참고:</strong> 실제 서비스를 이용하시려면 정식 서비스에서 진행해주세요.
          </div>
        </div>
        
        <div className="demo-warning-actions">
          <Button
            variant="secondary"
            onClick={onClose}
            className="demo-warning-cancel"
          >
            취소
          </Button>
          <Button
            variant="primary"
            onClick={() => {
              onConfirm();
              onClose();
            }}
            className="demo-warning-confirm"
          >
            {content.confirmText}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DemoWarningModal;