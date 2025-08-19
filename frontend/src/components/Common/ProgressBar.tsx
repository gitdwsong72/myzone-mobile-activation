import React from 'react';

interface ProgressBarProps {
  current: number;
  total: number;
  steps?: Array<{
    step: number;
    title: string;
    completed?: boolean;
  }>;
  showPercentage?: boolean;
  showStepLabels?: boolean;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'small' | 'medium' | 'large';
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  current,
  total,
  steps,
  showPercentage = true,
  showStepLabels = true,
  variant = 'default',
  size = 'medium',
}) => {
  const percentage = Math.round((current / total) * 100);

  const variantClasses = {
    default: 'progress-default',
    success: 'progress-success',
    warning: 'progress-warning',
    danger: 'progress-danger',
  };

  const sizeClasses = {
    small: 'progress-small',
    medium: 'progress-medium',
    large: 'progress-large',
  };

  return (
    <div className={`progress-container ${sizeClasses[size]}`}>
      {/* 단계별 표시 */}
      {steps && showStepLabels && (
        <div className="progress-steps">
          {steps.map((step, index) => (
            <div
              key={step.step}
              className={`progress-step ${
                step.step <= current ? 'completed' : ''
              } ${step.step === current ? 'current' : ''}`}
            >
              <div className="step-indicator">
                <span className="step-number">
                  {step.completed || step.step < current ? '✓' : step.step}
                </span>
              </div>
              <span className="step-title">{step.title}</span>
            </div>
          ))}
        </div>
      )}

      {/* 진행률 바 */}
      <div className={`progress-bar ${variantClasses[variant]}`}>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${percentage}%` }}
          />
        </div>
        
        {showPercentage && (
          <span className="progress-percentage">{percentage}%</span>
        )}
      </div>

      {/* 진행 상태 텍스트 */}
      <div className="progress-info">
        <span className="progress-text">
          {current} / {total} 단계 완료
        </span>
      </div>
    </div>
  );
};

// 간단한 진행률 바 컴포넌트
interface SimpleProgressBarProps {
  percentage: number;
  variant?: 'default' | 'success' | 'warning' | 'danger';
  size?: 'small' | 'medium' | 'large';
  showPercentage?: boolean;
  animated?: boolean;
}

export const SimpleProgressBar: React.FC<SimpleProgressBarProps> = ({
  percentage,
  variant = 'default',
  size = 'medium',
  showPercentage = false,
  animated = false,
}) => {
  const variantClasses = {
    default: 'progress-default',
    success: 'progress-success',
    warning: 'progress-warning',
    danger: 'progress-danger',
  };

  const sizeClasses = {
    small: 'progress-small',
    medium: 'progress-medium',
    large: 'progress-large',
  };

  return (
    <div className={`simple-progress ${sizeClasses[size]}`}>
      <div className={`progress-bar ${variantClasses[variant]}`}>
        <div className="progress-track">
          <div
            className={`progress-fill ${animated ? 'animated' : ''}`}
            style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
          />
        </div>
        
        {showPercentage && (
          <span className="progress-percentage">
            {Math.round(percentage)}%
          </span>
        )}
      </div>
    </div>
  );
};

export default ProgressBar;