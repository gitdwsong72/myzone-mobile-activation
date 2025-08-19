import React from 'react';
import { Link } from 'react-router-dom';
import { ROUTES } from '../../utils/navigation';

const Footer: React.FC = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        {/* 상단 섹션 */}
        <div className="footer-top">
          <div className="footer-section">
            <h3 className="footer-title">서비스</h3>
            <ul className="footer-links">
              <li>
                <Link to={ROUTES.PLANS} className="footer-link">
                  요금제
                </Link>
              </li>
              <li>
                <Link to={ROUTES.ORDER_STATUS} className="footer-link">
                  신청현황
                </Link>
              </li>
              <li>
                <Link to={ROUTES.SUPPORT} className="footer-link">
                  고객지원
                </Link>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">고객지원</h3>
            <ul className="footer-links">
              <li>
                <a href="tel:1588-0000" className="footer-link">
                  고객센터: 1588-0000
                </a>
              </li>
              <li>
                <span className="footer-text">
                  운영시간: 평일 09:00~18:00
                </span>
              </li>
              <li>
                <a href="mailto:support@myzone.co.kr" className="footer-link">
                  이메일 문의
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">회사정보</h3>
            <ul className="footer-links">
              <li>
                <a href="/about" className="footer-link">
                  회사소개
                </a>
              </li>
              <li>
                <a href="/privacy" className="footer-link">
                  개인정보처리방침
                </a>
              </li>
              <li>
                <a href="/terms" className="footer-link">
                  이용약관
                </a>
              </li>
            </ul>
          </div>

          <div className="footer-section">
            <h3 className="footer-title">SNS</h3>
            <div className="social-links">
              <a href="https://facebook.com/myzone" className="social-link" aria-label="페이스북" target="_blank" rel="noopener noreferrer">
                <span>Facebook</span>
              </a>
              <a href="https://instagram.com/myzone" className="social-link" aria-label="인스타그램" target="_blank" rel="noopener noreferrer">
                <span>Instagram</span>
              </a>
              <a href="https://youtube.com/myzone" className="social-link" aria-label="유튜브" target="_blank" rel="noopener noreferrer">
                <span>YouTube</span>
              </a>
            </div>
          </div>
        </div>

        {/* 하단 섹션 */}
        <div className="footer-bottom">
          <div className="company-info">
            <p className="company-text">
              (주)마이존 | 대표이사: 홍길동 | 사업자등록번호: 123-45-67890
            </p>
            <p className="company-text">
              주소: 서울특별시 강남구 테헤란로 123, 456호
            </p>
            <p className="company-text">
              통신판매업신고번호: 제2024-서울강남-1234호
            </p>
          </div>
          <div className="copyright">
            <p>&copy; 2024 MyZone. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;