import React, { useState } from 'react';
import { isDemoMode, DEMO_CONFIG } from '../../config/demo';
import PerformanceDashboard from './PerformanceDashboard';
import './DemoBanner.css';

interface DemoBannerProps {
  className?: string;
  showDetails?: boolean;
}

const DemoBanner: React.FC<DemoBannerProps> = ({ 
  className = '', 
  showDetails = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);
  const [showPerformanceDashboard, setShowPerformanceDashboard] = useState(false);

  // 데모 모드가 아니면 렌더링하지 않음
  if (!isDemoMode() || isDismissed) {
    return null;
  }

  const toggleExpanded = () => {
    setIsExpanded(!isExpanded);
  };

  const dismissBanner = () => {
    setIsDismissed(true);
  };

  return (
    <div className={`demo-banner ${className}`}>
      <div className="demo-banner-main">
        <div className="demo-banner-icon">
          🎭
        </div>
        <div className="demo-banner-content">
          <div className="demo-banner-title">
            데모 모드
          </div>
          <div className="demo-banner-message">
            {DEMO_CONFIG.DEMO_MESSAGES.notice}
          </div>
        </div>
        <div className="demo-banner-actions">
          <button 
            className="demo-banner-performance"
            onClick={() => setShowPerformanceDashboard(true)}
            aria-label="성능 대시보드 열기"
            title="성능 모니터링 대시보드"
          >
            📊
          </button>
          {showDetails && (
            <button 
              className="demo-banner-toggle"
              onClick={toggleExpanded}
              aria-label={isExpanded ? "상세 정보 숨기기" : "상세 정보 보기"}
            >
              {isExpanded ? '▲' : '▼'}
            </button>
          )}
          <button 
            className="demo-banner-close"
            onClick={dismissBanner}
            aria-label="배너 닫기"
          >
            ✕
          </button>
        </div>
      </div>
      
      {showDetails && isExpanded && (
        <div className="demo-banner-details">
          <h4>데모 모드 제한사항:</h4>
          <ul>
            {DEMO_CONFIG.DEMO_LIMITATIONS.map((limitation, index) => (
              <li key={index}>{limitation}</li>
            ))}
          </ul>
          <div className="demo-banner-note">
            <strong>참고:</strong> 모든 데이터는 임시로 저장되며, 실제 서비스와는 다를 수 있습니다.
          </div>
        </div>
      )}
      
      {/* 성능 대시보드 */}
      <PerformanceDashboard 
        isVisible={showPerformanceDashboard}
        onClose={() => setShowPerformanceDashboard(false)}
      />
    </div>
  );
};

export default DemoBanner;