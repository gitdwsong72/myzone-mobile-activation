import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { removeToast } from '../../store/slices/uiSlice';

interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

const Toast: React.FC<ToastProps> = ({
  id,
  type,
  message,
  duration = 5000,
  onClose,
}) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose(id);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const typeIcons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️',
  };

  const typeClasses = {
    success: 'toast-success',
    error: 'toast-error',
    warning: 'toast-warning',
    info: 'toast-info',
  };

  return (
    <div className={`toast ${typeClasses[type]}`}>
      <div className="toast-content">
        <span className="toast-icon">{typeIcons[type]}</span>
        <span className="toast-message">{message}</span>
      </div>
      <button
        className="toast-close"
        onClick={() => onClose(id)}
        aria-label="알림 닫기"
      >
        ✕
      </button>
    </div>
  );
};

// 토스트 컨테이너 컴포넌트
const ToastContainer: React.FC = () => {
  const dispatch = useAppDispatch();
  const { toasts } = useAppSelector((state) => state.ui);

  const handleCloseToast = (id: string) => {
    dispatch(removeToast(id));
  };

  if (toasts.length === 0) return null;

  const toastContainer = (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast
          key={toast.id}
          id={toast.id}
          type={toast.type}
          message={toast.message}
          duration={toast.duration}
          onClose={handleCloseToast}
        />
      ))}
    </div>
  );

  return createPortal(toastContainer, document.body);
};

// 토스트 사용을 위한 커스텀 훅
export const useToast = () => {
  const dispatch = useAppDispatch();

  const showToast = (
    type: 'success' | 'error' | 'warning' | 'info',
    message: string,
    duration?: number
  ) => {
    dispatch({
      type: 'ui/addToast',
      payload: { type, message, duration },
    });
  };

  const showSuccess = (message: string, duration?: number) => {
    showToast('success', message, duration);
  };

  const showError = (message: string, duration?: number) => {
    showToast('error', message, duration);
  };

  const showWarning = (message: string, duration?: number) => {
    showToast('warning', message, duration);
  };

  const showInfo = (message: string, duration?: number) => {
    showToast('info', message, duration);
  };

  return {
    showToast,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  };
};

export default ToastContainer;