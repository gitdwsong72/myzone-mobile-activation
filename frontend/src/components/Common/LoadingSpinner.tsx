import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'primary' | 'secondary' | 'white';
  text?: string;
  fullScreen?: boolean;
  overlay?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  variant = 'primary',
  text,
  fullScreen = false,
  overlay = false,
}) => {
  const sizeClasses = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large',
  };

  const variantClasses = {
    primary: 'spinner-primary',
    secondary: 'spinner-secondary',
    white: 'spinner-white',
  };

  const spinnerElement = (
    <div className={`loading-spinner ${sizeClasses[size]} ${variantClasses[variant]}`}>
      <div className="spinner-circle">
        <svg className="spinner-svg" viewBox="0 0 24 24">
          <circle
            className="spinner-path"
            cx="12"
            cy="12"
            r="10"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
        </svg>
      </div>
      {text && <span className="spinner-text">{text}</span>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="loading-fullscreen">
        <div className="loading-content">
          {spinnerElement}
        </div>
      </div>
    );
  }

  if (overlay) {
    return (
      <div className="loading-overlay">
        <div className="loading-content">
          {spinnerElement}
        </div>
      </div>
    );
  }

  return spinnerElement;
};

// 점 형태의 로딩 애니메이션
interface DotsLoadingProps {
  size?: 'small' | 'medium' | 'large';
  variant?: 'primary' | 'secondary' | 'white';
}

export const DotsLoading: React.FC<DotsLoadingProps> = ({
  size = 'medium',
  variant = 'primary',
}) => {
  const sizeClasses = {
    small: 'dots-small',
    medium: 'dots-medium',
    large: 'dots-large',
  };

  const variantClasses = {
    primary: 'dots-primary',
    secondary: 'dots-secondary',
    white: 'dots-white',
  };

  return (
    <div className={`dots-loading ${sizeClasses[size]} ${variantClasses[variant]}`}>
      <div className="dot dot-1"></div>
      <div className="dot dot-2"></div>
      <div className="dot dot-3"></div>
    </div>
  );
};

// 스켈레톤 로딩 컴포넌트
interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  variant?: 'text' | 'rectangular' | 'circular';
  animation?: 'pulse' | 'wave' | 'none';
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '1rem',
  variant = 'text',
  animation = 'pulse',
  className = '',
}) => {
  const variantClasses = {
    text: 'skeleton-text',
    rectangular: 'skeleton-rectangular',
    circular: 'skeleton-circular',
  };

  const animationClasses = {
    pulse: 'skeleton-pulse',
    wave: 'skeleton-wave',
    none: '',
  };

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      className={`skeleton ${variantClasses[variant]} ${animationClasses[animation]} ${className}`}
      style={style}
    />
  );
};

export default LoadingSpinner;