import { test, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';
import { testAdmin } from '../fixtures/test-data';

test.describe('관리자 대시보드 E2E 테스트', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('관리자 로그인 및 대시보드 접근', async ({ page }) => {
    // 관리자 로그인 페이지로 이동
    await page.goto('/admin/login');
    
    await helpers.expectTitle('MyZone 관리자 로그인');
    await helpers.expectText('h2', '관리자 로그인');
    
    // 로그인 정보 입력
    await helpers.fillForm({
      '[name="username"]': testAdmin.username,
      '[name="password"]': testAdmin.password
    });
    
    // 로그인 API 모킹
    await helpers.mockApiResponse('**/api/v1/auth/login', {
      access_token: 'mock-admin-token',
      refresh_token: 'mock-refresh-token',
      token_type: 'bearer',
      user: {
        id: 1,
        username: testAdmin.username,
        email: testAdmin.email,
        role: 'admin'
      }
    });
    
    await helpers.clickByText('로그인');
    await helpers.waitForPageLoad();
    
    // 대시보드로 리다이렉트 확인
    await helpers.expectUrl('/admin/dashboard');
    await helpers.expectText('h1', '관리자 대시보드');
    
    // 대시보드 위젯 확인
    await helpers.expectElementExists('.dashboard-stats');
    await helpers.expectElementExists('.today-orders-widget');
    await helpers.expectElementExists('.pending-orders-widget');
    await helpers.expectElementExists('.revenue-widget');
    
    // 사이드바 메뉴 확인
    await helpers.expectElementExists('.admin-sidebar');
    await helpers.expectText('.sidebar-menu', '주문 관리');
    await helpers.expectText('.sidebar-menu', '통계');
    await helpers.expectText('.sidebar-menu', '사용자 관리');
  });

  test('주문 관리 페이지 기능', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    // 주문 목록 API 모킹
    const mockOrders = [
      {
        id: 1,
        order_number: 'ORD123456789',
        user: { name: '홍길동', phone: '010-1234-5678' },
        plan: { name: '5G 프리미엄' },
        device: { brand: 'Samsung', model: 'Galaxy S24' },
        status: 'pending',
        total_amount: 1255000,
        created_at: '2023-01-01T10:00:00Z'
      },
      {
        id: 2,
        order_number: 'ORD123456790',
        user: { name: '김철수', phone: '010-9876-5432' },
        plan: { name: 'LTE 스탠다드' },
        device: { brand: 'Apple', model: 'iPhone 15' },
        status: 'processing',
        total_amount: 980000,
        created_at: '2023-01-01T11:00:00Z'
      }
    ];
    
    await helpers.mockApiResponse('**/api/v1/admin/orders*', mockOrders);
    
    await page.goto('/admin/orders');
    await helpers.waitForPageLoad();
    
    // 주문 관리 페이지 확인
    await helpers.expectText('h2', '주문 관리');
    await helpers.expectTableRows(2);
    
    // 필터 기능 테스트
    await helpers.selectOption('[name="statusFilter"]', 'pending');
    await helpers.waitForPageLoad();
    
    // 검색 기능 테스트
    await page.fill('[name="searchQuery"]', '홍길동');
    await helpers.clickByText('검색');
    await helpers.waitForPageLoad();
    
    // 주문 상세 보기
    await page.click('[data-testid="order-row"]:first-child');
    await helpers.waitForModal();
    
    // 주문 상세 정보 확인
    await helpers.expectText('.order-detail-modal', 'ORD123456789');
    await helpers.expectText('.order-detail-modal', '홍길동');
    await helpers.expectText('.order-detail-modal', '5G 프리미엄');
    
    // 상태 변경 기능
    await helpers.selectOption('[name="newStatus"]', 'processing');
    await page.fill('[name="statusNote"]', '심사 시작');
    
    // 상태 변경 API 모킹
    await helpers.mockApiResponse('**/api/v1/orders/1/status', {
      id: 1,
      status: 'processing',
      updated_at: '2023-01-01T12:00:00Z'
    });
    
    await helpers.clickByText('상태 변경');
    await helpers.waitForPageLoad();
    
    // 성공 메시지 확인
    await helpers.expectToast('주문 상태가 변경되었습니다.');
    
    // 모달 닫기
    await helpers.closeModal();
  });

  test('통계 페이지 기능', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    // 통계 데이터 API 모킹
    const mockStats = {
      total_orders: 150,
      pending_orders: 25,
      processing_orders: 30,
      completed_orders: 90,
      cancelled_orders: 5,
      total_revenue: 187500000,
      daily_orders: [
        { date: '2023-01-01', count: 10, revenue: 12550000 },
        { date: '2023-01-02', count: 15, revenue: 18825000 },
        { date: '2023-01-03', count: 12, revenue: 15060000 }
      ],
      plan_statistics: [
        { plan_name: '5G 프리미엄', count: 60, percentage: 40 },
        { plan_name: 'LTE 스탠다드', count: 45, percentage: 30 },
        { plan_name: '5G 스탠다드', count: 30, percentage: 20 },
        { plan_name: 'LTE 베이직', count: 15, percentage: 10 }
      ]
    };
    
    await helpers.mockApiResponse('**/api/v1/admin/statistics*', mockStats);
    
    await page.goto('/admin/statistics');
    await helpers.waitForPageLoad();
    
    // 통계 페이지 확인
    await helpers.expectText('h2', '통계');
    
    // 주요 지표 카드 확인
    await helpers.expectText('.stat-card', '150'); // 총 주문 수
    await helpers.expectText('.stat-card', '25'); // 대기 중 주문
    await helpers.expectText('.stat-card', '187,500,000원'); // 총 매출
    
    // 차트 요소 확인
    await helpers.expectElementExists('.orders-chart');
    await helpers.expectElementExists('.revenue-chart');
    await helpers.expectElementExists('.plan-distribution-chart');
    
    // 날짜 필터 기능
    await page.fill('[name="startDate"]', '2023-01-01');
    await page.fill('[name="endDate"]', '2023-01-31');
    await helpers.clickByText('조회');
    await helpers.waitForPageLoad();
    
    // 차트 데이터 업데이트 확인
    await helpers.expectElementExists('.chart-updated');
    
    // 엑셀 다운로드 기능
    const downloadPromise = page.waitForEvent('download');
    await helpers.clickByText('엑셀 다운로드');
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toContain('statistics');
  });

  test('사용자 관리 페이지 기능', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    // 사용자 목록 API 모킹
    const mockUsers = [
      {
        id: 1,
        name: '홍길동',
        phone: '010-1234-5678',
        email: 'hong@example.com',
        created_at: '2023-01-01T10:00:00Z',
        order_count: 2,
        total_spent: 2510000
      },
      {
        id: 2,
        name: '김철수',
        phone: '010-9876-5432',
        email: 'kim@example.com',
        created_at: '2023-01-02T10:00:00Z',
        order_count: 1,
        total_spent: 980000
      }
    ];
    
    await helpers.mockApiResponse('**/api/v1/admin/users*', mockUsers);
    
    await page.goto('/admin/users');
    await helpers.waitForPageLoad();
    
    // 사용자 관리 페이지 확인
    await helpers.expectText('h2', '사용자 관리');
    await helpers.expectTableRows(2);
    
    // 검색 기능
    await page.fill('[name="userSearch"]', '홍길동');
    await helpers.clickByText('검색');
    await helpers.waitForPageLoad();
    
    // 사용자 상세 보기
    await page.click('[data-testid="user-row"]:first-child');
    await helpers.waitForModal();
    
    // 사용자 상세 정보 확인
    await helpers.expectText('.user-detail-modal', '홍길동');
    await helpers.expectText('.user-detail-modal', '010-1234-5678');
    await helpers.expectText('.user-detail-modal', '주문 횟수: 2회');
    await helpers.expectText('.user-detail-modal', '총 결제 금액: 2,510,000원');
    
    // 사용자 주문 이력 탭
    await helpers.clickByText('주문 이력');
    await helpers.expectElementExists('.user-orders-list');
    
    // 모달 닫기
    await helpers.closeModal();
  });

  test('실시간 알림 기능', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    await page.goto('/admin/dashboard');
    await helpers.waitForPageLoad();
    
    // WebSocket 연결 모킹 (실제 구현에서는 WebSocket 사용)
    await page.evaluate(() => {
      // 새 주문 알림 시뮬레이션
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('newOrder', {
          detail: {
            order_number: 'ORD123456791',
            user_name: '이영희',
            amount: 1255000
          }
        }));
      }, 2000);
    });
    
    // 알림 토스트 확인
    await helpers.expectToast('새로운 주문이 접수되었습니다: ORD123456791');
    
    // 알림 센터 확인
    await helpers.clickByText('알림');
    await helpers.expectElementExists('.notification-list');
    await helpers.expectText('.notification-item', 'ORD123456791');
  });

  test('권한 관리 및 접근 제어', async ({ page }) => {
    // 일반 사용자 토큰으로 설정
    await helpers.setLocalStorage('token', 'mock-user-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 2,
      username: 'user',
      role: 'user'
    }));
    
    // 관리자 페이지 접근 시도
    await page.goto('/admin/dashboard');
    await helpers.waitForPageLoad();
    
    // 접근 거부 페이지로 리다이렉트 확인
    await helpers.expectUrl('/403');
    await helpers.expectText('h2', '접근 권한이 없습니다');
    
    // 로그인 페이지로 이동 링크 확인
    await helpers.expectElementExists('a:has-text("로그인 페이지로 이동")');
  });

  test('관리자 로그아웃 기능', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    await page.goto('/admin/dashboard');
    await helpers.waitForPageLoad();
    
    // 사용자 메뉴 클릭
    await helpers.clickByText('admin');
    await helpers.expectElementExists('.user-dropdown');
    
    // 로그아웃 API 모킹
    await helpers.mockApiResponse('**/api/v1/auth/logout', {
      message: 'Successfully logged out'
    });
    
    // 로그아웃 클릭
    await helpers.clickByText('로그아웃');
    await helpers.waitForPageLoad();
    
    // 로그인 페이지로 리다이렉트 확인
    await helpers.expectUrl('/admin/login');
    
    // 로컬 스토리지에서 토큰 제거 확인
    const token = await helpers.getLocalStorage('token');
    expect(token).toBeNull();
  });

  test('반응형 관리자 대시보드', async ({ page }) => {
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    // 태블릿 뷰포트로 설정
    await helpers.setViewportSize(768, 1024);
    
    await page.goto('/admin/dashboard');
    await helpers.waitForPageLoad();
    
    // 모바일 사이드바 확인
    await helpers.expectElementExists('.mobile-sidebar-toggle');
    
    // 사이드바 토글
    await helpers.clickByText('메뉴');
    await helpers.expectElementExists('.sidebar-overlay');
    
    // 통계 카드가 세로로 배치되는지 확인
    await helpers.expectElementExists('.dashboard-stats.mobile-stack');
    
    // 테이블이 가로 스크롤되는지 확인
    await page.goto('/admin/orders');
    await helpers.waitForPageLoad();
    
    await helpers.expectElementExists('.table-responsive');
  });
});