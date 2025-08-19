import React from 'react';
import { screen, fireEvent } from '@testing-library/react';
import { renderWithProviders } from '../../../test-utils';
import HomePage from '../index';

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('HomePage Component', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('메인 페이지가 올바르게 렌더링된다', () => {
    renderWithProviders(<HomePage />);
    
    expect(screen.getByText('MyZone')).toBeInTheDocument();
    expect(screen.getByText(/간편하고 빠른 휴대폰 개통 서비스/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /개통 신청/i })).toBeInTheDocument();
  });

  test('개통 신청 버튼 클릭 시 요금제 선택 페이지로 이동한다', () => {
    renderWithProviders(<HomePage />);
    
    const startButton = screen.getByRole('button', { name: /개통 신청/i });
    fireEvent.click(startButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/plans');
  });

  test('서비스 특징이 올바르게 표시된다', () => {
    renderWithProviders(<HomePage />);
    
    expect(screen.getByText(/빠른 개통/i)).toBeInTheDocument();
    expect(screen.getByText(/다양한 요금제/i)).toBeInTheDocument();
    expect(screen.getByText(/안전한 결제/i)).toBeInTheDocument();
    expect(screen.getByText(/실시간 현황 확인/i)).toBeInTheDocument();
  });

  test('프로모션 배너가 표시된다', () => {
    const mockPromotion = {
      title: '신규 가입 혜택',
      description: '첫 달 요금 50% 할인',
      image: '/images/promotion-banner.jpg'
    };

    renderWithProviders(<HomePage />, {
      preloadedState: {
        ui: {
          promotions: [mockPromotion],
          loading: false,
          error: null
        }
      }
    });
    
    expect(screen.getByText('신규 가입 혜택')).toBeInTheDocument();
    expect(screen.getByText('첫 달 요금 50% 할인')).toBeInTheDocument();
  });

  test('신청 현황 조회 링크가 올바르게 작동한다', () => {
    renderWithProviders(<HomePage />);
    
    const statusLink = screen.getByText(/신청 현황 조회/i);
    fireEvent.click(statusLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/order-status');
  });

  test('고객 지원 링크가 올바르게 작동한다', () => {
    renderWithProviders(<HomePage />);
    
    const supportLink = screen.getByText(/고객 지원/i);
    fireEvent.click(supportLink);
    
    expect(mockNavigate).toHaveBeenCalledWith('/support');
  });

  test('로딩 상태가 올바르게 표시된다', () => {
    renderWithProviders(<HomePage />, {
      preloadedState: {
        ui: {
          loading: true,
          error: null,
          promotions: []
        }
      }
    });
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('에러 상태가 올바르게 표시된다', () => {
    renderWithProviders(<HomePage />, {
      preloadedState: {
        ui: {
          loading: false,
          error: '데이터를 불러오는 중 오류가 발생했습니다.',
          promotions: []
        }
      }
    });
    
    expect(screen.getByText('데이터를 불러오는 중 오류가 발생했습니다.')).toBeInTheDocument();
  });

  test('반응형 디자인이 적용된다', () => {
    // 모바일 뷰포트 시뮬레이션
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    
    renderWithProviders(<HomePage />);
    
    const container = screen.getByTestId('homepage-container');
    expect(container).toHaveClass('mobile-layout');
  });

  test('접근성 속성이 올바르게 설정된다', () => {
    renderWithProviders(<HomePage />);
    
    const mainContent = screen.getByRole('main');
    expect(mainContent).toBeInTheDocument();
    
    const startButton = screen.getByRole('button', { name: /개통 신청/i });
    expect(startButton).toHaveAttribute('aria-label', '휴대폰 개통 신청 시작');
  });

  test('키보드 네비게이션이 올바르게 작동한다', () => {
    renderWithProviders(<HomePage />);
    
    const startButton = screen.getByRole('button', { name: /개통 신청/i });
    
    // Tab 키로 포커스 이동
    startButton.focus();
    expect(startButton).toHaveFocus();
    
    // Enter 키로 버튼 클릭
    fireEvent.keyDown(startButton, { key: 'Enter', code: 'Enter' });
    expect(mockNavigate).toHaveBeenCalledWith('/plans');
  });

  test('스크롤 애니메이션이 트리거된다', () => {
    const mockIntersectionObserver = jest.fn();
    mockIntersectionObserver.mockReturnValue({
      observe: () => null,
      unobserve: () => null,
      disconnect: () => null
    });
    
    window.IntersectionObserver = mockIntersectionObserver;
    
    renderWithProviders(<HomePage />);
    
    expect(mockIntersectionObserver).toHaveBeenCalled();
  });

  test('메타 태그가 올바르게 설정된다', () => {
    renderWithProviders(<HomePage />);
    
    expect(document.title).toBe('MyZone - 간편한 휴대폰 개통 서비스');
    
    const metaDescription = document.querySelector('meta[name="description"]');
    expect(metaDescription?.getAttribute('content')).toContain('MyZone');
  });
});