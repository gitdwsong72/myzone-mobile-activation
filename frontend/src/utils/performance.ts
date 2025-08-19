// 성능 모니터링 및 최적화 유틸리티

interface PerformanceMetrics {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
}

class PerformanceMonitor {
  private metrics: PerformanceMetrics = {};
  private observers: PerformanceObserver[] = [];

  constructor() {
    this.initializeObservers();
  }

  private initializeObservers() {
    // First Contentful Paint & Largest Contentful Paint
    if ('PerformanceObserver' in window) {
      try {
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.name === 'first-contentful-paint') {
              this.metrics.fcp = entry.startTime;
            }
          }
        });
        paintObserver.observe({ entryTypes: ['paint'] });
        this.observers.push(paintObserver);

        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          this.metrics.lcp = lastEntry.startTime;
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        this.observers.push(lcpObserver);

        // First Input Delay
        const fidObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.metrics.fid = (entry as any).processingStart - entry.startTime;
          }
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        this.observers.push(fidObserver);

        // Cumulative Layout Shift
        const clsObserver = new PerformanceObserver((list) => {
          let clsValue = 0;
          for (const entry of list.getEntries()) {
            if (!(entry as any).hadRecentInput) {
              clsValue += (entry as any).value;
            }
          }
          this.metrics.cls = clsValue;
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        this.observers.push(clsObserver);
      } catch (error) {
        console.warn('Performance Observer not supported:', error);
      }
    }

    // Time to First Byte
    if ('performance' in window && 'timing' in performance) {
      window.addEventListener('load', () => {
        const timing = performance.timing;
        this.metrics.ttfb = timing.responseStart - timing.navigationStart;
      });
    }
  }

  getMetrics(): PerformanceMetrics {
    return { ...this.metrics };
  }

  // 성능 점수 계산 (0-100)
  getPerformanceScore(): number {
    const { fcp, lcp, fid, cls } = this.metrics;
    let score = 100;

    // FCP 점수 (2.5초 이하 = 좋음)
    if (fcp) {
      if (fcp > 4000) score -= 25;
      else if (fcp > 2500) score -= 15;
    }

    // LCP 점수 (2.5초 이하 = 좋음)
    if (lcp) {
      if (lcp > 4000) score -= 25;
      else if (lcp > 2500) score -= 15;
    }

    // FID 점수 (100ms 이하 = 좋음)
    if (fid) {
      if (fid > 300) score -= 25;
      else if (fid > 100) score -= 15;
    }

    // CLS 점수 (0.1 이하 = 좋음)
    if (cls) {
      if (cls > 0.25) score -= 25;
      else if (cls > 0.1) score -= 15;
    }

    return Math.max(0, score);
  }

  // 성능 리포트 생성
  generateReport(): string {
    const metrics = this.getMetrics();
    const score = this.getPerformanceScore();
    
    return `
Performance Report:
- Score: ${score}/100
- First Contentful Paint: ${metrics.fcp ? `${metrics.fcp.toFixed(2)}ms` : 'N/A'}
- Largest Contentful Paint: ${metrics.lcp ? `${metrics.lcp.toFixed(2)}ms` : 'N/A'}
- First Input Delay: ${metrics.fid ? `${metrics.fid.toFixed(2)}ms` : 'N/A'}
- Cumulative Layout Shift: ${metrics.cls ? metrics.cls.toFixed(3) : 'N/A'}
- Time to First Byte: ${metrics.ttfb ? `${metrics.ttfb.toFixed(2)}ms` : 'N/A'}
    `.trim();
  }

  // 리소스 로딩 성능 분석
  analyzeResourcePerformance(): any[] {
    if (!('performance' in window)) return [];

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    
    return resources.map(resource => ({
      name: resource.name,
      type: this.getResourceType(resource.name),
      duration: resource.duration,
      size: resource.transferSize || 0,
      cached: resource.transferSize === 0 && resource.decodedBodySize > 0
    })).sort((a, b) => b.duration - a.duration);
  }

  private getResourceType(url: string): string {
    if (url.includes('.js')) return 'script';
    if (url.includes('.css')) return 'stylesheet';
    if (url.match(/\.(png|jpg|jpeg|gif|webp|svg)$/)) return 'image';
    if (url.includes('/api/')) return 'api';
    return 'other';
  }

  // 메모리 사용량 모니터링
  getMemoryUsage(): any {
    if ('memory' in performance) {
      const memory = (performance as any).memory;
      return {
        used: memory.usedJSHeapSize,
        total: memory.totalJSHeapSize,
        limit: memory.jsHeapSizeLimit,
        percentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      };
    }
    return null;
  }

  // 정리
  destroy() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// 전역 성능 모니터 인스턴스
export const performanceMonitor = new PerformanceMonitor();

// 이미지 최적화 유틸리티
export function optimizeImageUrl(url: string, width?: number, quality?: number): string {
  if (!url) return url;

  // WebP 지원 확인
  const supportsWebP = (() => {
    const canvas = document.createElement('canvas');
    return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
  })();

  // URL에 최적화 파라미터 추가
  const urlObj = new URL(url, window.location.origin);
  
  if (width) {
    urlObj.searchParams.set('w', width.toString());
  }
  
  if (quality) {
    urlObj.searchParams.set('q', quality.toString());
  }
  
  if (supportsWebP && !url.includes('.svg')) {
    urlObj.searchParams.set('format', 'webp');
  }

  return urlObj.toString();
}

// 지연 로딩 유틸리티
export function createIntersectionObserver(
  callback: (entries: IntersectionObserverEntry[]) => void,
  options?: IntersectionObserverInit
): IntersectionObserver {
  const defaultOptions: IntersectionObserverInit = {
    threshold: 0.1,
    rootMargin: '50px',
    ...options
  };

  return new IntersectionObserver(callback, defaultOptions);
}

// 번들 크기 분석 (개발 환경용)
export function analyzeBundleSize() {
  if (process.env.NODE_ENV === 'development') {
    const scripts = Array.from(document.querySelectorAll('script[src]'));
    const styles = Array.from(document.querySelectorAll('link[rel="stylesheet"]'));
    
    console.group('Bundle Analysis');
    console.log('Scripts:', scripts.length);
    console.log('Stylesheets:', styles.length);
    
    scripts.forEach((script: any) => {
      console.log(`Script: ${script.src}`);
    });
    
    styles.forEach((style: any) => {
      console.log(`Stylesheet: ${style.href}`);
    });
    
    console.groupEnd();
  }
}

// 렌더링 성능 측정
export function measureRenderTime(componentName: string) {
  return {
    start: () => performance.mark(`${componentName}-start`),
    end: () => {
      performance.mark(`${componentName}-end`);
      performance.measure(
        `${componentName}-render`,
        `${componentName}-start`,
        `${componentName}-end`
      );
      
      const measure = performance.getEntriesByName(`${componentName}-render`)[0];
      console.log(`${componentName} render time: ${measure.duration.toFixed(2)}ms`);
      
      // 정리
      performance.clearMarks(`${componentName}-start`);
      performance.clearMarks(`${componentName}-end`);
      performance.clearMeasures(`${componentName}-render`);
    }
  };
}