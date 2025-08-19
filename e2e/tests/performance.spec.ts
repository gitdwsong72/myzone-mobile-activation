import { test, expect } from '@playwright/test';
import { TestHelpers } from '../utils/test-helpers';

test.describe('성능 테스트', () => {
  let helpers: TestHelpers;

  test.beforeEach(async ({ page }) => {
    helpers = new TestHelpers(page);
  });

  test('페이지 로딩 성능 측정', async ({ page }) => {
    // 성능 메트릭 수집 시작
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // Web Vitals 측정
    const webVitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals: any = {};
        
        // LCP (Largest Contentful Paint)
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          vitals.lcp = lastEntry.startTime;
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        // FID (First Input Delay) - 실제 사용자 상호작용 필요
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            vitals.fid = entry.processingStart - entry.startTime;
          });
        }).observe({ entryTypes: ['first-input'] });
        
        // CLS (Cumulative Layout Shift)
        let clsValue = 0;
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          vitals.cls = clsValue;
        }).observe({ entryTypes: ['layout-shift'] });
        
        // 3초 후 결과 반환
        setTimeout(() => resolve(vitals), 3000);
      });
    });
    
    // 성능 기준 검증
    expect(webVitals.lcp).toBeLessThan(2500); // LCP < 2.5초
    expect(webVitals.cls).toBeLessThan(0.1); // CLS < 0.1
    
    console.log('Web Vitals:', webVitals);
  });

  test('이미지 최적화 확인', async ({ page }) => {
    await page.goto('/');
    
    // 이미지 요소들 확인
    const images = await page.locator('img').all();
    
    for (const img of images) {
      // lazy loading 속성 확인
      const loading = await img.getAttribute('loading');
      if (loading) {
        expect(loading).toBe('lazy');
      }
      
      // alt 속성 확인 (접근성)
      const alt = await img.getAttribute('alt');
      expect(alt).toBeTruthy();
      
      // 이미지 크기 확인
      const src = await img.getAttribute('src');
      if (src && !src.startsWith('data:')) {
        const response = await page.request.get(src);
        const contentLength = response.headers()['content-length'];
        if (contentLength) {
          const size = parseInt(contentLength);
          expect(size).toBeLessThan(500000); // 500KB 미만
        }
      }
    }
  });

  test('JavaScript 번들 크기 확인', async ({ page }) => {
    // 네트워크 요청 모니터링
    const jsRequests: any[] = [];
    
    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('.js') && response.status() === 200) {
        jsRequests.push({
          url,
          size: response.headers()['content-length']
        });
      }
    });
    
    await page.goto('/');
    await helpers.waitForPageLoad();
    
    // 메인 번들 크기 확인
    const mainBundle = jsRequests.find(req => req.url.includes('main'));
    if (mainBundle && mainBundle.size) {
      const size = parseInt(mainBundle.size);
      expect(size).toBeLessThan(1000000); // 1MB 미만
    }
    
    // 총 JavaScript 크기 확인
    const totalJSSize = jsRequests.reduce((total, req) => {
      return total + (req.size ? parseInt(req.size) : 0);
    }, 0);
    
    expect(totalJSSize).toBeLessThan(2000000); // 2MB 미만
    
    console.log('JavaScript bundle sizes:', jsRequests);
  });

  test('API 응답 시간 측정', async ({ page }) => {
    const apiRequests: any[] = [];
    
    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('/api/')) {
        apiRequests.push({
          url,
          status: response.status(),
          timing: response.timing()
        });
      }
    });
    
    // 개통 신청 플로우 진행
    await page.goto('/');
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    // API 응답 시간 확인
    for (const request of apiRequests) {
      const responseTime = request.timing.responseEnd - request.timing.requestStart;
      expect(responseTime).toBeLessThan(3000); // 3초 미만
      
      console.log(`API ${request.url}: ${responseTime}ms`);
    }
  });

  test('메모리 사용량 모니터링', async ({ page }) => {
    await page.goto('/');
    
    // 초기 메모리 사용량 측정
    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
        jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
      } : null;
    });
    
    if (initialMemory) {
      console.log('Initial memory usage:', initialMemory);
    }
    
    // 여러 페이지 네비게이션 수행
    await helpers.clickByText('개통 신청');
    await helpers.waitForPageLoad();
    
    await page.goBack();
    await helpers.waitForPageLoad();
    
    await helpers.clickByText('신청 현황 조회');
    await helpers.waitForPageLoad();
    
    // 최종 메모리 사용량 측정
    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory ? {
        usedJSHeapSize: (performance as any).memory.usedJSHeapSize,
        totalJSHeapSize: (performance as any).memory.totalJSHeapSize,
        jsHeapSizeLimit: (performance as any).memory.jsHeapSizeLimit
      } : null;
    });
    
    if (initialMemory && finalMemory) {
      const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
      console.log('Memory increase:', memoryIncrease);
      
      // 메모리 증가량이 과도하지 않은지 확인 (10MB 미만)
      expect(memoryIncrease).toBeLessThan(10 * 1024 * 1024);
    }
  });

  test('캐싱 효율성 확인', async ({ page }) => {
    const cacheHits: string[] = [];
    const cacheMisses: string[] = [];
    
    page.on('response', (response) => {
      const cacheControl = response.headers()['cache-control'];
      const url = response.url();
      
      if (cacheControl && (url.includes('.js') || url.includes('.css') || url.includes('.png') || url.includes('.jpg'))) {
        if (response.fromServiceWorker() || response.status() === 304) {
          cacheHits.push(url);
        } else {
          cacheMisses.push(url);
        }
      }
    });
    
    // 첫 번째 방문
    await page.goto('/');
    await helpers.waitForPageLoad();
    
    // 페이지 새로고침
    await page.reload();
    await helpers.waitForPageLoad();
    
    console.log('Cache hits:', cacheHits.length);
    console.log('Cache misses:', cacheMisses.length);
    
    // 캐시 히트율이 50% 이상인지 확인
    const totalRequests = cacheHits.length + cacheMisses.length;
    if (totalRequests > 0) {
      const hitRate = cacheHits.length / totalRequests;
      expect(hitRate).toBeGreaterThan(0.5);
    }
  });

  test('모바일 성능 측정', async ({ page }) => {
    // 모바일 환경 시뮬레이션
    await helpers.setMobileViewport();
    
    // 네트워크 속도 제한 (3G)
    await page.route('**/*', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 100)); // 100ms 지연
      await route.continue();
    });
    
    const startTime = Date.now();
    await page.goto('/');
    await helpers.waitForPageLoad();
    const loadTime = Date.now() - startTime;
    
    // 모바일에서 5초 이내 로딩 확인
    expect(loadTime).toBeLessThan(5000);
    
    console.log('Mobile load time:', loadTime, 'ms');
  });

  test('대용량 데이터 처리 성능', async ({ page }) => {
    // 대용량 주문 목록 API 모킹
    const largeOrderList = Array.from({ length: 1000 }, (_, i) => ({
      id: i + 1,
      order_number: `ORD${String(i + 1).padStart(9, '0')}`,
      user: { name: `사용자${i + 1}`, phone: `010-${String(i).padStart(4, '0')}-${String(i).padStart(4, '0')}` },
      plan: { name: '5G 프리미엄' },
      status: 'pending',
      total_amount: 1255000,
      created_at: new Date().toISOString()
    }));
    
    await helpers.mockApiResponse('**/api/v1/admin/orders*', largeOrderList);
    
    // 관리자로 로그인
    await helpers.setLocalStorage('token', 'mock-admin-token');
    await helpers.setLocalStorage('user', JSON.stringify({
      id: 1,
      username: 'admin',
      role: 'admin'
    }));
    
    const startTime = Date.now();
    await page.goto('/admin/orders');
    await helpers.waitForPageLoad();
    const renderTime = Date.now() - startTime;
    
    // 대용량 데이터 렌더링이 10초 이내에 완료되는지 확인
    expect(renderTime).toBeLessThan(10000);
    
    // 가상화된 테이블이 사용되는지 확인
    await helpers.expectElementExists('.virtual-table');
    
    console.log('Large data render time:', renderTime, 'ms');
  });

  test('동시 사용자 시뮬레이션', async ({ browser }) => {
    // 여러 브라우저 컨텍스트로 동시 접속 시뮬레이션
    const contexts = await Promise.all([
      browser.newContext(),
      browser.newContext(),
      browser.newContext()
    ]);
    
    const pages = await Promise.all(
      contexts.map(context => context.newPage())
    );
    
    // 동시에 페이지 로드
    const startTime = Date.now();
    await Promise.all(
      pages.map(page => page.goto('/'))
    );
    const concurrentLoadTime = Date.now() - startTime;
    
    // 동시 접속 시에도 합리적인 시간 내에 로드되는지 확인
    expect(concurrentLoadTime).toBeLessThan(8000);
    
    console.log('Concurrent load time:', concurrentLoadTime, 'ms');
    
    // 컨텍스트 정리
    await Promise.all(contexts.map(context => context.close()));
  });
});