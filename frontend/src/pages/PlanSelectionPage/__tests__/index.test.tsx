import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders, mockPlan } from '../../../test-utils';
import PlanSelectionPage from '../index';

// Mock API calls
jest.mock('../../../services/api', () => ({
  getPlans: jest.fn(),
  getPlansByCategory: jest.fn(),
}));

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('PlanSelectionPage Component', () => {
  const mockPlans = [
    { ...mockPlan, id: 1, name: '5G 프리미엄', category: '5G', monthly_fee: 55000 },
    { ...mockPlan, id: 2, name: '5G 스탠다드', category: '5G', monthly_fee: 45000 },
    { ...mockPlan, id: 3, name: 'LTE 프리미엄', category: 'LTE', monthly_fee: 35000 },
  ];

  beforeEach(() => {
    mockNavigate.mockClear();
  });

  test('요금제 선택 페이지가 올바르게 렌더링된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    expect(screen.getByText('요금제 선택')).toBeInTheDocument();
    expect(screen.getByText('원하시는 요금제를 선택해주세요')).toBeInTheDocument();
  });

  test('요금제 목록이 올바르게 표시된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    expect(screen.getByText('5G 프리미엄')).toBeInTheDocument();
    expect(screen.getByText('5G 스탠다드')).toBeInTheDocument();
    expect(screen.getByText('LTE 프리미엄')).toBeInTheDocument();
    
    expect(screen.getByText('55,000원')).toBeInTheDocument();
    expect(screen.getByText('45,000원')).toBeInTheDocument();
    expect(screen.getByText('35,000원')).toBeInTheDocument();
  });

  test('카테고리 필터가 올바르게 작동한다', async () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    // 5G 카테고리 선택
    const fiveGFilter = screen.getByText('5G');
    fireEvent.click(fiveGFilter);
    
    await waitFor(() => {
      expect(screen.getByText('5G 프리미엄')).toBeInTheDocument();
      expect(screen.getByText('5G 스탠다드')).toBeInTheDocument();
      expect(screen.queryByText('LTE 프리미엄')).not.toBeInTheDocument();
    });
  });

  test('요금제 선택이 올바르게 작동한다', () => {
    const { store } = renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const planCard = screen.getByTestId('plan-card-1');
    fireEvent.click(planCard);
    
    const state = store.getState();
    expect(state.plans.selectedPlan?.id).toBe(1);
  });

  test('요금제 상세 정보 모달이 올바르게 작동한다', async () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const detailButton = screen.getAllByText('상세보기')[0];
    fireEvent.click(detailButton);
    
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText('요금제 상세 정보')).toBeInTheDocument();
    });
  });

  test('다음 단계 버튼이 요금제 선택 후 활성화된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: mockPlans[0],
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const nextButton = screen.getByRole('button', { name: /다음 단계/i });
    expect(nextButton).not.toBeDisabled();
  });

  test('다음 단계 버튼 클릭 시 사용자 정보 입력 페이지로 이동한다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: mockPlans[0],
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const nextButton = screen.getByRole('button', { name: /다음 단계/i });
    fireEvent.click(nextButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/user-info');
  });

  test('이전 단계 버튼 클릭 시 메인 페이지로 이동한다', () => {
    renderWithProviders(<PlanSelectionPage />);
    
    const backButton = screen.getByRole('button', { name: /이전 단계/i });
    fireEvent.click(backButton);
    
    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  test('로딩 상태가 올바르게 표시된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: [],
          selectedPlan: null,
          loading: true,
          error: null,
          categories: []
        }
      }
    });
    
    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  test('에러 상태가 올바르게 표시된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: [],
          selectedPlan: null,
          loading: false,
          error: '요금제를 불러오는 중 오류가 발생했습니다.',
          categories: []
        }
      }
    });
    
    expect(screen.getByText('요금제를 불러오는 중 오류가 발생했습니다.')).toBeInTheDocument();
  });

  test('요금제 비교 기능이 올바르게 작동한다', async () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    // 비교할 요금제 선택
    const compareCheckbox1 = screen.getAllByRole('checkbox', { name: /비교하기/i })[0];
    const compareCheckbox2 = screen.getAllByRole('checkbox', { name: /비교하기/i })[1];
    
    fireEvent.click(compareCheckbox1);
    fireEvent.click(compareCheckbox2);
    
    const compareButton = screen.getByRole('button', { name: /선택한 요금제 비교/i });
    fireEvent.click(compareButton);
    
    await waitFor(() => {
      expect(screen.getByText('요금제 비교')).toBeInTheDocument();
    });
  });

  test('정렬 기능이 올바르게 작동한다', async () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const sortSelect = screen.getByRole('combobox', { name: /정렬/i });
    fireEvent.change(sortSelect, { target: { value: 'price_asc' } });
    
    await waitFor(() => {
      const planCards = screen.getAllByTestId(/plan-card-/);
      expect(planCards[0]).toHaveTextContent('35,000원'); // LTE 프리미엄이 첫 번째
    });
  });

  test('검색 기능이 올바르게 작동한다', async () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const searchInput = screen.getByPlaceholderText(/요금제 검색/i);
    fireEvent.change(searchInput, { target: { value: '프리미엄' } });
    
    await waitFor(() => {
      expect(screen.getByText('5G 프리미엄')).toBeInTheDocument();
      expect(screen.getByText('LTE 프리미엄')).toBeInTheDocument();
      expect(screen.queryByText('5G 스탠다드')).not.toBeInTheDocument();
    });
  });

  test('진행률 바가 올바르게 표시된다', () => {
    renderWithProviders(<PlanSelectionPage />);
    
    const progressBar = screen.getByRole('progressbar');
    expect(progressBar).toHaveAttribute('aria-valuenow', '1'); // 첫 번째 단계
  });

  test('접근성 속성이 올바르게 설정된다', () => {
    renderWithProviders(<PlanSelectionPage />, {
      preloadedState: {
        plans: {
          plans: mockPlans,
          selectedPlan: null,
          loading: false,
          error: null,
          categories: ['5G', 'LTE']
        }
      }
    });
    
    const planCards = screen.getAllByRole('button', { name: /요금제 선택/i });
    planCards.forEach(card => {
      expect(card).toHaveAttribute('aria-label');
    });
  });
});