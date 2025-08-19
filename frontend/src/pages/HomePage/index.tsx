import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/Common/Button';
import './HomePage.css';

const HomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleStartApplication = () => {
    navigate('/plans');
  };

  const features = [
    {
      icon: '📱',
      title: '간편한 온라인 개통',
      description: '집에서 편리하게 휴대폰 개통 신청'
    },
    {
      icon: '⚡',
      title: '빠른 처리',
      description: '24시간 이내 개통 완료'
    },
    {
      icon: '💰',
      title: '최저가 보장',
      description: '다양한 할인 혜택과 프로모션'
    },
    {
      icon: '🔒',
      title: '안전한 보안',
      description: '개인정보 보호 및 안전한 결제'
    }
  ];

  return (
    <div className="home-page">
      {/* 히어로 섹션 */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="brand-logo">
            <h1 className="brand-title">MyZone</h1>
            <p className="brand-subtitle">핸드폰 개통 서비스</p>
          </div>
          
          <div className="hero-text">
            <h2 className="hero-title">
              간편하고 빠른<br />
              온라인 개통 서비스
            </h2>
            <p className="hero-description">
              집에서 편리하게 휴대폰 개통 신청부터 배송까지<br />
              MyZone과 함께 스마트하게 시작하세요
            </p>
          </div>

          <div className="hero-actions">
            <Button
              variant="primary"
              size="large"
              onClick={handleStartApplication}
              className="start-button"
            >
              개통 신청 시작하기
            </Button>
            <Button
              variant="outline"
              size="large"
              onClick={() => navigate('/support')}
              className="support-button"
            >
              서비스 문의
            </Button>
          </div>
        </div>

        <div className="hero-image">
          <div className="phone-mockup">
            <div className="phone-screen">
              <div className="screen-content">
                <div className="app-preview">
                  <div className="preview-header">MyZone</div>
                  <div className="preview-content">
                    <div className="preview-item"></div>
                    <div className="preview-item"></div>
                    <div className="preview-item"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 프로모션 배너 */}
      <section className="promotion-banner">
        <div className="banner-content">
          <div className="banner-icon">🎉</div>
          <div className="banner-text">
            <h3>신규 가입 특별 혜택</h3>
            <p>첫 달 요금 50% 할인 + 무료 배송</p>
          </div>
          <div className="banner-action">
            <Button
              variant="success"
              size="medium"
              onClick={handleStartApplication}
            >
              지금 신청
            </Button>
          </div>
        </div>
      </section>

      {/* 서비스 특징 */}
      <section className="features-section">
        <div className="section-header">
          <h2 className="section-title">MyZone만의 특별한 서비스</h2>
          <p className="section-description">
            고객 만족을 위한 차별화된 서비스를 제공합니다
          </p>
        </div>

        <div className="features-grid">
          {features.map((feature, index) => (
            <div key={index} className="feature-card">
              <div className="feature-icon">{feature.icon}</div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 개통 절차 안내 */}
      <section className="process-section">
        <div className="section-header">
          <h2 className="section-title">간단한 4단계 개통 절차</h2>
          <p className="section-description">
            복잡한 절차 없이 쉽고 빠르게 개통하세요
          </p>
        </div>

        <div className="process-steps">
          <div className="step">
            <div className="step-number">1</div>
            <div className="step-content">
              <h3>요금제 선택</h3>
              <p>나에게 맞는 요금제를 선택하세요</p>
            </div>
          </div>
          <div className="step-arrow">→</div>
          
          <div className="step">
            <div className="step-number">2</div>
            <div className="step-content">
              <h3>개인정보 입력</h3>
              <p>본인인증 및 정보를 입력하세요</p>
            </div>
          </div>
          <div className="step-arrow">→</div>
          
          <div className="step">
            <div className="step-number">3</div>
            <div className="step-content">
              <h3>단말기 선택</h3>
              <p>원하는 스마트폰을 선택하세요</p>
            </div>
          </div>
          <div className="step-arrow">→</div>
          
          <div className="step">
            <div className="step-number">4</div>
            <div className="step-content">
              <h3>결제 완료</h3>
              <p>안전한 결제로 개통을 완료하세요</p>
            </div>
          </div>
        </div>

        <div className="process-action">
          <Button
            variant="primary"
            size="large"
            onClick={handleStartApplication}
            className="process-start-button"
          >
            지금 시작하기
          </Button>
        </div>
      </section>

      {/* CTA 섹션 */}
      <section className="cta-section">
        <div className="cta-content">
          <h2 className="cta-title">지금 바로 MyZone과 함께하세요!</h2>
          <p className="cta-description">
            더 나은 모바일 라이프의 시작, MyZone에서 경험하세요
          </p>
          <div className="cta-actions">
            <Button
              variant="primary"
              size="large"
              onClick={handleStartApplication}
              className="cta-primary-button"
            >
              개통 신청하기
            </Button>
            <Button
              variant="outline"
              size="large"
              onClick={() => navigate('/status')}
              className="cta-secondary-button"
            >
              신청 현황 조회
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;