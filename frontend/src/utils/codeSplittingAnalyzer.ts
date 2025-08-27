// 코드 스플리팅 분석 및 최적화 유틸리티

interface ChunkInfo {
  name: string;
  size: number;
  loadTime: number;
  cached: boolean;
  route?: string;
}

interface CodeSplittingAnalysis {
  totalChunks: number;
  loadedChunks: ChunkInfo[];
  averageLoadTime: number;
  cacheHitRate: number;
  recommendations: string[];
}

class CodeSplittingAnalyzer {
  private static chunkLoadTimes = new Map<string, number>();
  private static chunkSizes = new Map<string, number>();

  // 청크 로딩 시작 시간 기록
  static markChunkLoadStart(chunkName: string): void {
    performance.mark(`chunk-${chunkName}-start`);
  }

  // 청크 로딩 완료 시간 기록
  static markChunkLoadEnd(chunkName: string): void {
    performance.mark(`chunk-${chunkName}-end`);
    
    try {
      performance.measure(
        `chunk-${chunkName}-load`,
        `chunk-${chunkName}-start`,
        `chunk-${chunkName}-end`
      );
      
      const measure = performance.getEntriesByName(`chunk-${chunkName}-load`)[0];
      this.chunkLoadTimes.set(chunkName, measure.duration);
      
      // 정리
      performance.clearMarks(`chunk-${chunkName}-start`);
      performance.clearMarks(`chunk-${chunkName}-end`);
      performance.clearMeasures(`chunk-${chunkName}-load`);
    } catch (error) {
      console.warn(`청크 ${chunkName} 로딩 시간 측정 실패:`, error);
    }
  }

  // 현재 로드된 청크 분석
  static analyzeLoadedChunks(): CodeSplittingAnalysis {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    const loadedChunks: ChunkInfo[] = [];
    let totalLoadTime = 0;
    let cachedCount = 0;

    resources.forEach(resource => {
      if (resource.name.includes('/static/js/') && resource.name.includes('.chunk.js')) {
        const chunkName = this.extractChunkName(resource.name);
        const size = resource.transferSize || resource.decodedBodySize || 0;
        const loadTime = resource.duration;
        const cached = resource.transferSize === 0 && resource.decodedBodySize > 0;
        
        if (cached) cachedCount++;
        totalLoadTime += loadTime;
        
        loadedChunks.push({
          name: chunkName,
          size,
          loadTime,
          cached,
          route: this.guessRouteFromChunkName(chunkName)
        });
        
        this.chunkSizes.set(chunkName, size);
      }
    });

    const averageLoadTime = loadedChunks.length > 0 ? totalLoadTime / loadedChunks.length : 0;
    const cacheHitRate = loadedChunks.length > 0 ? (cachedCount / loadedChunks.length) * 100 : 0;

    return {
      totalChunks: loadedChunks.length,
      loadedChunks: loadedChunks.sort((a, b) => b.loadTime - a.loadTime),
      averageLoadTime,
      cacheHitRate,
      recommendations: this.generateRecommendations(loadedChunks, averageLoadTime, cacheHitRate)
    };
  }

  // 청크명에서 라우트 추측
  private static guessRouteFromChunkName(chunkName: string): string {
    const routeMap: { [key: string]: string } = {
      'HomePage': '/',
      'PlanSelection': '/plans',
      'UserInfo': '/user-info',
      'DeviceSelection': '/devices',
      'NumberSelection': '/numbers',
      'OrderSummary': '/order-summary',
      'Payment': '/payment',
      'PaymentComplete': '/payment-complete',
      'OrderStatus': '/order-status',
      'Support': '/support',
      'AdminLogin': '/admin/login',
      'AdminDashboard': '/admin/dashboard',
      'AdminOrders': '/admin/orders',
      'AdminStatistics': '/admin/statistics'
    };

    for (const [key, route] of Object.entries(routeMap)) {
      if (chunkName.toLowerCase().includes(key.toLowerCase())) {
        return route;
      }
    }

    return 'unknown';
  }

  // 청크명 추출
  private static extractChunkName(url: string): string {
    const fileName = url.split('/').pop() || '';
    return fileName.replace(/\.\w+\.chunk\.js$/, '').replace(/^\d+\./, '');
  }

  // 권장사항 생성
  private static generateRecommendations(
    chunks: ChunkInfo[], 
    averageLoadTime: number, 
    cacheHitRate: number
  ): string[] {
    const recommendations: string[] = [];

    // 로딩 시간 분석
    if (averageLoadTime > 1000) {
      recommendations.push(
        `평균 청크 로딩 시간이 ${averageLoadTime.toFixed(0)}ms로 깁니다. 청크 크기를 줄이거나 프리로딩을 고려하세요.`
      );
    }

    // 캐시 히트율 분석
    if (cacheHitRate < 50) {
      recommendations.push(
        `캐시 히트율이 ${cacheHitRate.toFixed(1)}%로 낮습니다. 캐시 전략을 개선하세요.`
      );
    }

    // 큰 청크 식별
    chunks.forEach(chunk => {
      if (chunk.size > 500 * 1024) { // 500KB 이상
        recommendations.push(
          `${chunk.name} 청크가 ${this.formatSize(chunk.size)}로 큽니다. 더 세분화된 분할을 고려하세요.`
        );
      }
      
      if (chunk.loadTime > 2000) { // 2초 이상
        recommendations.push(
          `${chunk.name} 청크 로딩이 ${chunk.loadTime.toFixed(0)}ms로 깁니다. 최적화가 필요합니다.`
        );
      }
    });

    // 일반적인 권장사항
    if (recommendations.length === 0) {
      recommendations.push('코드 스플리팅이 효율적으로 작동하고 있습니다.');
    }

    return recommendations;
  }

  // 크기 포맷팅
  private static formatSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // 분석 리포트 생성
  static generateReport(): string {
    const analysis = this.analyzeLoadedChunks();
    
    let report = `
🧩 코드 스플리팅 분석 리포트
========================

📊 총 청크 수: ${analysis.totalChunks}
⏱️ 평균 로딩 시간: ${analysis.averageLoadTime.toFixed(0)}ms
💾 캐시 히트율: ${analysis.cacheHitRate.toFixed(1)}%

📋 로드된 청크:
${analysis.loadedChunks.map(chunk => 
  `  ${chunk.name} (${chunk.route}): ${this.formatSize(chunk.size)} - ${chunk.loadTime.toFixed(0)}ms ${chunk.cached ? '(캐시됨)' : ''}`
).join('\n')}

💡 권장사항:
${analysis.recommendations.map(rec => `  • ${rec}`).join('\n')}
    `.trim();

    return report;
  }

  // 성능 점수 계산
  static calculatePerformanceScore(): number {
    const analysis = this.analyzeLoadedChunks();
    let score = 100;

    // 평균 로딩 시간 점수
    if (analysis.averageLoadTime > 2000) {
      score -= 30;
    } else if (analysis.averageLoadTime > 1000) {
      score -= 15;
    }

    // 캐시 히트율 점수
    if (analysis.cacheHitRate < 30) {
      score -= 20;
    } else if (analysis.cacheHitRate < 60) {
      score -= 10;
    }

    // 큰 청크 페널티
    analysis.loadedChunks.forEach(chunk => {
      if (chunk.size > 1024 * 1024) { // 1MB 이상
        score -= 15;
      } else if (chunk.size > 500 * 1024) { // 500KB 이상
        score -= 5;
      }
    });

    return Math.max(0, score);
  }

  // 프리로딩 권장사항
  static getPreloadRecommendations(): string[] {
    const analysis = this.analyzeLoadedChunks();
    const recommendations: string[] = [];

    // 자주 사용되는 라우트 식별
    const criticalRoutes = ['/', '/plans', '/user-info'];
    
    analysis.loadedChunks.forEach(chunk => {
      if (chunk.route && criticalRoutes.includes(chunk.route) && chunk.loadTime > 1000) {
        recommendations.push(
          `${chunk.route} 라우트의 청크를 프리로드하는 것을 고려하세요.`
        );
      }
    });

    return recommendations;
  }
}

export default CodeSplittingAnalyzer;
export type { ChunkInfo, CodeSplittingAnalysis };