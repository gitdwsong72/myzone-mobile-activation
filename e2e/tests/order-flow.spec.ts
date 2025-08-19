import { test, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';
import { testUser, testPlan, testDevice, testNumber, testPayment, testDelivery } from '../fixtures/test-data';

test.describe('주문 플로우 E2E 테스트', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
    await page.goto('/');
  });

  test('전체 주문 플로우가 정상적으로 작동한다', async ({ page }) => {
    // 1. 메인 페이지에서 개통 신청 시작
    await helpers.expectTitle('MyZone - 간편한 휴대폰 개통 서비스');
    await helpers.expectText('h1', 'MyZone');
    await helpers.expectText('.hero-description', '간편하고 빠른 휴대폰 개통 서비스');
    
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    // 2. 요금제 선택 페이지
    await helpers.expectUrl('/plans');
    await helpers.expectProgressStep(1);
    await helpers.expectText('h2', '요금제 선택');
    
    // 요금제 목록이 로드될 때까지 대기
    await helpers.waitForLoadingToFinish();
    
    // 5G 카테고리 필터 적용
    await helpers.clickByText('5G');
    await helpers.waitForPageLoad();
    
    // 5G 프리미엄 요금제 선택
    await page.click('[data-testid="plan-card"]:has-text("5G 프리미엄")');
    await helpers.expectText('.selected-plan', '5G 프리미엄');
    
    // 다음 단계로 이동
    await helpers.clickByText('다음 단계');
    await helpers.waitForPageLoad();
    
    // 3. 개인정보 입력 페이지
    await helpers.expectUrl('/user-info');
    await helpers.expectProgressStep(2);
    await helpers.expectText('h2', '개인정보 입력');
    
    // 개인정보 입력
    await helpers.fillForm({
      '[name="name"]': testUser.name,
      '[name="phone"]': testUser.phone,
      '[name="email"]': testUser.email,
      '[name="birthDate"]': testUser.birthDate,
      '[name="address"]': testUser.address,
      '[name="detailAddress"]': testUser.detailAddress,
      '[name="zipCode"]': testUser.zipCode
    });
    
    // 성별 선택
    await helpers.selectRadio('[name="gender"][value="M"]');
    
    // 본인인증 (모킹된 응답)
    await helpers.mockApiResponse('**/api/v1/auth/send-verification', { success: true });
    await helpers.clickByText('인증번호 발송');
    await helpers.waitForElement('[name="verificationCode"]');
    
    await page.fill('[name="verificationCode"]', '123456');
    await helpers.mockApiResponse('**/api/v1/auth/verify-phone', { verified: true });
    await helpers.clickByText('인증 확인');
    
    // 인증 완료 확인
    await helpers.expectText('.verification-status', '인증 완료');
    
    // 다음 단계로 이동
    await helpers.clickByText('다음 단계');
    await helpers.waitForPageLoad();
    
    // 4. 단말기 선택 페이지
    await helpers.expectUrl('/devices');
    await helpers.expectProgressStep(3);
    await helpers.expectText('h2', '단말기 선택');
    
    // 단말기 목록 로드 대기
    await helpers.waitForLoadingToFinish();
    
    // 삼성 브랜드 필터 적용
    await helpers.clickByText('Samsung');
    await helpers.waitForPageLoad();
    
    // Galaxy S24 선택
    await page.click('[data-testid="device-card"]:has-text("Galaxy S24")');
    
    // 색상 선택
    await page.click('[data-testid="color-option"]:has-text("Black")');
    
    // 배송 정보 입력
    await helpers.fillForm({
      '[name="recipientName"]': testDelivery.recipientName,
      '[name="recipientPhone"]': testDelivery.recipientPhone,
      '[name="deliveryAddress"]': testDelivery.address,
      '[name="deliveryDetailAddress"]': testDelivery.detailAddress,
      '[name="deliveryRequest"]': testDelivery.deliveryRequest
    });
    
    // 다음 단계로 이동
    await helpers.clickByText('다음 단계');
    await helpers.waitForPageLoad();
    
    // 5. 번호 선택 페이지
    await helpers.expectUrl('/numbers');
    await helpers.expectProgressStep(4);
    await helpers.expectText('h2', '번호 선택');
    
    // 번호 목록 로드 대기
    await helpers.waitForLoadingToFinish();
    
    // 일반 번호 카테고리 선택
    await helpers.clickByText('일반');
    await helpers.waitForPageLoad();
    
    // 번호 검색
    await page.fill('[name="numberSearch"]', '1111');
    await helpers.clickByText('검색');
    await helpers.waitForPageLoad();
    
    // 번호 선택
    await page.click('[data-testid="number-card"]:first-child');
    
    // 번호 예약 확인
    await helpers.expectText('.reservation-timer', '29:');
    
    // 다음 단계로 이동
    await helpers.clickByText('다음 단계');
    await helpers.waitForPageLoad();
    
    // 6. 신청 내역 확인 페이지
    await helpers.expectUrl('/order-summary');
    await helpers.expectProgressStep(5);
    await helpers.expectText('h2', '신청 내역 확인');
    
    // 선택 내역 확인
    await helpers.expectText('.selected-plan-summary', '5G 프리미엄');
    await helpers.expectText('.selected-device-summary', 'Galaxy S24');
    await helpers.expectText('.selected-number-summary', '010-');
    await helpers.expectText('.user-info-summary', testUser.name);
    
    // 약관 동의
    await helpers.checkBox('[name="termsOfService"]');
    await helpers.checkBox('[name="privacyPolicy"]');
    await helpers.checkBox('[name="marketingConsent"]');
    
    // 결제 페이지로 이동
    await helpers.clickByText('결제하기');
    await helpers.waitForPageLoad();
    
    // 7. 결제 페이지
    await helpers.expectUrl('/payment');
    await helpers.expectProgressStep(6);
    await helpers.expectText('h2', '결제');
    
    // 결제 금액 확인
    await helpers.expectElementExists('.payment-amount');
    
    // 결제 방법 선택
    await helpers.selectRadio('[name="paymentMethod"][value="credit_card"]');
    
    // 카드 정보 입력
    await helpers.fillForm({
      '[name="cardNumber"]': testPayment.cardNumber,
      '[name="expiryMonth"]': testPayment.expiryMonth,
      '[name="expiryYear"]': testPayment.expiryYear,
      '[name="cvc"]': testPayment.cvc
    });
    
    // 할부 선택
    await helpers.selectOption('[name="installment"]', testPayment.installment.toString());
    
    // 결제 처리 (모킹된 응답)
    await helpers.mockApiResponse('**/api/v1/payments/', {
      id: 1,
      status: 'completed',
      transaction_id: 'TXN123456789',
      amount: 1255000
    });
    
    await helpers.clickByText('결제하기');
    await helpers.waitForPageLoad();
    
    // 8. 결제 완료 페이지
    await helpers.expectUrl('/payment-complete');
    await helpers.expectText('h2', '결제 완료');
    await helpers.expectText('.success-message', '신청이 완료되었습니다');
    
    // 신청번호 확인
    await helpers.expectElementExists('.order-number');
    const orderNumber = await page.textContent('.order-number');
    expect(orderNumber).toMatch(/ORD\d{9}/);
    
    // 예상 개통일 확인
    await helpers.expectElementExists('.expected-activation-date');
    
    // 신청 현황 조회 페이지로 이동
    await helpers.clickByText('신청 현황 조회');
    await helpers.waitForPageLoad();
    
    // 9. 신청 현황 조회 페이지
    await helpers.expectUrl('/order-status');
    await helpers.expectText('h2', '신청 현황 조회');
    
    // 신청번호로 조회 (자동으로 입력되어 있어야 함)
    await helpers.expectInputValue('[name="orderNumber"]', orderNumber!);
    
    // 조회 결과 확인
    await helpers.expectElementExists('.order-status-card');
    await helpers.expectText('.current-status', '접수완료');
    await helpers.expectElementExists('.progress-steps');
  });

  test('모바일 환경에서 주문 플로우가 정상적으로 작동한다', async ({ page }) => {
    // 모바일 뷰포트 설정
    await helpers.setMobileViewport();
    
    // 메인 페이지 모바일 레이아웃 확인
    await helpers.expectElementExists('.mobile-layout');
    
    // 햄버거 메뉴 확인
    await helpers.expectElementExists('.mobile-menu-button');
    
    // 개통 신청 버튼이 전체 너비를 차지하는지 확인
    const startButton = page.locator('button:has-text("개통 신청")');
    await expect(startButton).toHaveClass(/btn-full-width/);
    
    // 개통 신청 시작
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    // 모바일에서 요금제 카드가 세로로 배치되는지 확인
    await helpers.expectElementExists('.plan-cards.mobile-stack');
    
    // 터치 친화적인 UI 요소 확인
    const planCards = page.locator('[data-testid="plan-card"]');
    const firstCard = planCards.first();
    
    // 카드 크기가 터치하기 적절한지 확인 (최소 44px)
    const cardHeight = await firstCard.evaluate(el => el.getBoundingClientRect().height);
    expect(cardHeight).toBeGreaterThanOrEqual(44);
  });

  test('접근성 기능이 올바르게 작동한다', async ({ page }) => {
    // 키보드 네비게이션 테스트
    await page.keyboard.press('Tab');
    
    // 첫 번째 포커스 가능한 요소가 포커스되었는지 확인
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
    
    // 개통 신청 버튼으로 Tab 이동
    await page.keyboard.press('Tab');
    const startButton = page.locator('button:has-text("개통 신청")');
    await expect(startButton).toBeFocused();
    
    // Enter 키로 버튼 클릭
    await page.keyboard.press('Enter');
    await helpers.waitForPageLoad();
    
    // ARIA 속성 확인
    await helpers.expectUrl('/plans');
    
    const progressBar = page.locator('[role="progressbar"]');
    await expect(progressBar).toHaveAttribute('aria-valuenow', '1');
    await expect(progressBar).toHaveAttribute('aria-valuemax', '6');
    
    // 스크린 리더용 텍스트 확인
    await helpers.expectElementExists('[aria-label]');
    await helpers.expectElementExists('[aria-describedby]');
  });

  test('에러 상황이 올바르게 처리된다', async ({ page }) => {
    // API 에러 모킹
    await helpers.mockApiError('**/api/v1/plans/', 500, {
      error_code: 'INTERNAL_SERVER_ERROR',
      message: '서버 오류가 발생했습니다.'
    });
    
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    // 에러 메시지 확인
    await helpers.expectText('.error-message', '서버 오류가 발생했습니다.');
    
    // 재시도 버튼 확인
    await helpers.expectElementExists('button:has-text("다시 시도")');
    
    // 네트워크 에러 시나리오
    await page.route('**/api/v1/plans/', route => route.abort());
    
    await helpers.clickByText('다시 시도');
    await helpers.waitForPageLoad();
    
    // 네트워크 에러 메시지 확인
    await helpers.expectText('.error-message', '네트워크 연결을 확인해주세요.');
  });

  test('브라우저 뒤로가기/앞으로가기가 올바르게 작동한다', async ({ page }) => {
    // 개통 신청 시작
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    await helpers.expectUrl('/plans');
    
    // 뒤로가기
    await page.goBack();
    await helpers.waitForPageLoad();
    await helpers.expectUrl('/');
    
    // 앞으로가기
    await page.goForward();
    await helpers.waitForPageLoad();
    await helpers.expectUrl('/plans');
    
    // 상태가 유지되는지 확인
    await helpers.expectProgressStep(1);
  });

  test('세션 만료 시 적절히 처리된다', async ({ page }) => {
    // 만료된 토큰 설정
    await helpers.setLocalStorage('token', 'expired-token');
    
    // 인증이 필요한 API 호출 시 401 에러 모킹
    await helpers.mockApiError('**/api/v1/users/me', 401, {
      error_code: 'TOKEN_EXPIRED',
      message: '토큰이 만료되었습니다.'
    });
    
    await page.goto('/user-info');
    await helpers.waitForPageLoad();
    
    // 로그인 페이지로 리다이렉트되는지 확인
    await helpers.expectUrl('/login');
    await helpers.expectText('.login-message', '세션이 만료되었습니다. 다시 로그인해주세요.');
  });

  test('페이지 새로고침 시 상태가 유지된다', async ({ page }) => {
    // 개통 신청 진행
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    // 요금제 선택
    await page.click('[data-testid="plan-card"]:first-child');
    
    // 페이지 새로고침
    await page.reload();
    await helpers.waitForPageLoad();
    
    // 선택된 요금제가 유지되는지 확인
    await helpers.expectElementExists('.selected-plan');
    await helpers.expectProgressStep(1);
  });
});