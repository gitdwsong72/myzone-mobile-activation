import { Page, expect } from '@playwright/test';

/**
 * E2E 테스트 헬퍼 함수들
 */

export class TestHelpers {
  constructor(private page: Page) {}

  /**
   * 페이지 로딩 대기
   */
  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 요소가 보일 때까지 대기
   */
  async waitForElement(selector: string, timeout = 10000) {
    await this.page.waitForSelector(selector, { timeout });
  }

  /**
   * 텍스트가 포함된 요소 클릭
   */
  async clickByText(text: string) {
    await this.page.click(`text=${text}`);
  }

  /**
   * 폼 필드 입력
   */
  async fillForm(fields: Record<string, string>) {
    for (const [selector, value] of Object.entries(fields)) {
      await this.page.fill(selector, value);
    }
  }

  /**
   * 드롭다운 선택
   */
  async selectOption(selector: string, value: string) {
    await this.page.selectOption(selector, value);
  }

  /**
   * 체크박스 체크
   */
  async checkBox(selector: string) {
    await this.page.check(selector);
  }

  /**
   * 라디오 버튼 선택
   */
  async selectRadio(selector: string) {
    await this.page.click(selector);
  }

  /**
   * 파일 업로드
   */
  async uploadFile(selector: string, filePath: string) {
    await this.page.setInputFiles(selector, filePath);
  }

  /**
   * 스크린샷 촬영
   */
  async takeScreenshot(name: string) {
    await this.page.screenshot({ path: `test-results/screenshots/${name}.png` });
  }

  /**
   * 로딩 스피너 대기
   */
  async waitForLoadingToFinish() {
    await this.page.waitForSelector('[data-testid="loading-spinner"]', { state: 'hidden' });
  }

  /**
   * 토스트 메시지 확인
   */
  async expectToast(message: string) {
    await expect(this.page.locator('[data-testid="toast"]')).toContainText(message);
  }

  /**
   * 모달 대기
   */
  async waitForModal() {
    await this.page.waitForSelector('[role="dialog"]');
  }

  /**
   * 모달 닫기
   */
  async closeModal() {
    await this.page.click('[data-testid="modal-close"]');
  }

  /**
   * 진행률 바 확인
   */
  async expectProgressStep(step: number) {
    const progressBar = this.page.locator('[role="progressbar"]');
    await expect(progressBar).toHaveAttribute('aria-valuenow', step.toString());
  }

  /**
   * 테이블 행 수 확인
   */
  async expectTableRows(count: number) {
    const rows = this.page.locator('tbody tr');
    await expect(rows).toHaveCount(count);
  }

  /**
   * URL 확인
   */
  async expectUrl(path: string) {
    await expect(this.page).toHaveURL(new RegExp(path));
  }

  /**
   * 페이지 제목 확인
   */
  async expectTitle(title: string) {
    await expect(this.page).toHaveTitle(title);
  }

  /**
   * 요소 텍스트 확인
   */
  async expectText(selector: string, text: string) {
    await expect(this.page.locator(selector)).toContainText(text);
  }

  /**
   * 요소 존재 확인
   */
  async expectElementExists(selector: string) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  /**
   * 요소 비존재 확인
   */
  async expectElementNotExists(selector: string) {
    await expect(this.page.locator(selector)).not.toBeVisible();
  }

  /**
   * 버튼 활성화 상태 확인
   */
  async expectButtonEnabled(selector: string) {
    await expect(this.page.locator(selector)).toBeEnabled();
  }

  /**
   * 버튼 비활성화 상태 확인
   */
  async expectButtonDisabled(selector: string) {
    await expect(this.page.locator(selector)).toBeDisabled();
  }

  /**
   * 입력 필드 값 확인
   */
  async expectInputValue(selector: string, value: string) {
    await expect(this.page.locator(selector)).toHaveValue(value);
  }

  /**
   * 로컬 스토리지 값 설정
   */
  async setLocalStorage(key: string, value: string) {
    await this.page.evaluate(
      ({ key, value }) => localStorage.setItem(key, value),
      { key, value }
    );
  }

  /**
   * 로컬 스토리지 값 가져오기
   */
  async getLocalStorage(key: string): Promise<string | null> {
    return await this.page.evaluate(
      (key) => localStorage.getItem(key),
      key
    );
  }

  /**
   * 쿠키 설정
   */
  async setCookie(name: string, value: string) {
    await this.page.context().addCookies([{
      name,
      value,
      domain: 'localhost',
      path: '/'
    }]);
  }

  /**
   * 네트워크 요청 모킹
   */
  async mockApiResponse(url: string, response: any) {
    await this.page.route(url, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  /**
   * 네트워크 요청 실패 모킹
   */
  async mockApiError(url: string, status: number, error: any) {
    await this.page.route(url, route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify(error)
      });
    });
  }

  /**
   * 뷰포트 크기 설정
   */
  async setViewportSize(width: number, height: number) {
    await this.page.setViewportSize({ width, height });
  }

  /**
   * 모바일 뷰포트로 설정
   */
  async setMobileViewport() {
    await this.setViewportSize(375, 667);
  }

  /**
   * 데스크톱 뷰포트로 설정
   */
  async setDesktopViewport() {
    await this.setViewportSize(1920, 1080);
  }

  /**
   * 스크롤
   */
  async scrollTo(selector: string) {
    await this.page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * 페이지 맨 위로 스크롤
   */
  async scrollToTop() {
    await this.page.evaluate(() => window.scrollTo(0, 0));
  }

  /**
   * 페이지 맨 아래로 스크롤
   */
  async scrollToBottom() {
    await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  }

  /**
   * 키보드 입력
   */
  async pressKey(key: string) {
    await this.page.keyboard.press(key);
  }

  /**
   * 마우스 호버
   */
  async hover(selector: string) {
    await this.page.hover(selector);
  }

  /**
   * 더블 클릭
   */
  async doubleClick(selector: string) {
    await this.page.dblclick(selector);
  }

  /**
   * 우클릭
   */
  async rightClick(selector: string) {
    await this.page.click(selector, { button: 'right' });
  }

  /**
   * 드래그 앤 드롭
   */
  async dragAndDrop(sourceSelector: string, targetSelector: string) {
    await this.page.dragAndDrop(sourceSelector, targetSelector);
  }
}