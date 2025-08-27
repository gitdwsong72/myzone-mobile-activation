// 통합 성능 모니터링 시스템

import { performanceMonitor } from './performance';
import BundleAnalyzer from './bundleAnalyzer';
import CodeSplittingAnalyzer from './codeSplittingAnalyzer';

interface PerformanceReport {
  timestamp: string;
  environment: string;
  webVitals: {
    score: number;
    metrics: any;
  };
  bundle: {
    score: number;
    analysis: any;
  };
  codeSplitting: {
    score: number;
    analysis: any;
  };
  overall: {
    score: number;
    grade: string;
    recommendations: string[];
  };
}

class PerformanceMonitoringSystem {
  private static instance: PerformanceMonitoringSystem;
  private reports: PerformanceReport[] = [];
  private isMonitoring = false;

  static getInstance(): PerformanceMonitoringSystem {
    if (!this.instance) {
      this.instance = new PerformanceMonitoringSystem();
    }
    return this.instance;
  }

  // 모니터링 시작
  startMonitoring(): void {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('🔍 성능 모니터링 시작');

    // 페이지 로드 완료 후 초기 분석
    if (document.readyState === 'complete') {
      this.performInitialAnalysis();
    } else {
      window.addEventListener('load', () => {
        setTimeout(() => this.performInitialAnalysis(), 2000);
      });
    }

    // 주기적 모니터링 (5분마다)
    setInterval(() => {
      this.performPeriodicAnalysis();
    }, 5 * 60 * 1000);

    // 라우트 변경 시 분석
    this.setupRouteChangeMonitoring();
  }

  // 초기 분석 수행
  private performInitialAnalysis(): void {
    console.log('📊 초기 성능 분석 수행 중...');
    
    setTimeout(() => {
      const report = this.generateReport();
      this.reports.push(report);
      this.logReport(report);
      
      // 데모 모드에서는 콘솔에 상세 정보 출력
      if (process.env.REACT_APP_DEMO_MODE === 'true') {
        this.displayDetailedAnalysis();
      }
    }, 1000);
  }

  // 주기적 분석 수행
  private performPeriodicAnalysis(): void {
    if (!this.isMonitoring) return;
    
    const report = this.generateReport();
    this.reports.push(report);
    
    // 최근 10개 리포트만 유지
    if (this.reports.length > 10) {
      this.reports = this.reports.slice(-10);
    }
    
    // 성능 저하 감지
    this.detectPerformanceDegradation(report);
  }

  // 라우트 변경 모니터링 설정
  private setupRouteChangeMonitoring(): void {
    let currentPath = window.location.pathname;
    
    // History API 감지
    const originalPushState = history.pushState;
    const originalReplaceState = history.replaceState;
    
    history.pushState = function(...args) {
      originalPushState.apply(history, args);
      PerformanceMonitoringSystem.getInstance().onRouteChange(currentPath, window.location.pathname);
      currentPath = window.location.pathname;
    };
    
    history.replaceState = function(...args) {
      originalReplaceState.apply(history, args);
      PerformanceMonitoringSystem.getInstance().onRouteChange(currentPath, window.location.pathname);
      currentPath = window.location.pathname;
    };
    
    // popstate 이벤트 감지
    window.addEventListener('popstate', () => {
      PerformanceMonitoringSystem.getInstance().onRouteChange(currentPath, window.location.pathname);
      currentPath = window.location.pathname;
    });
  }

  // 라우트 변경 시 처리
  private onRouteChange(from: string, to: string): void {
    console.log(`🔄 라우트 변경: ${from} → ${to}`);
    
    // 새 페이지 로딩 성능 측정
    setTimeout(() => {
      const chunkName = this.getChunkNameFromRoute(to);
      if (chunkName) {
        CodeSplittingAnalyzer.markChunkLoadEnd(chunkName);
      }
    }, 100);
  }

  // 라우트에서 청크명 추출
  private getChunkNameFromRoute(route: string): string | null {
    const routeChunkMap: { [key: string]: string } = {
      '/': 'HomePage',
      '/plans': 'PlanSelection',
      '/user-info': 'UserInfo',
      '/devices': 'DeviceSelection',
      '/numbers': 'NumberSelection',
      '/order-summary': 'OrderSummary',
      '/payment': 'Payment',
      '/payment-complete': 'PaymentComplete',
      '/order-status': 'OrderStatus',
      '/support': 'Support',
      '/admin/login': 'AdminLogin',
      '/admin/dashboard': 'AdminDashboard',
      '/admin/orders': 'AdminOrders',
      '/admin/statistics': 'AdminStatistics'
    };
    
    return routeChunkMap[route] || null;
  }

  // 성능 리포트 생성
  generateReport(): PerformanceReport {
    const timestamp = new Date().toISOString();
    const environment = process.env.REACT_APP_ENVIRONMENT || 'unknown';
    
    // Web Vitals 분석
    const webVitalsScore = performanceMonitor.getPerformanceScore();
    const webVitalsMetrics = performanceMonitor.getMetrics();
    
    // 번들 분석
    const bundleScore = BundleAnalyzer.calculatePerformanceScore();
    const bundleAnalysis = BundleAnalyzer.analyzeResourceSizes();
    
    // 코드 스플리팅 분석
    const codeSplittingScore = CodeSplittingAnalyzer.calculatePerformanceScore();
    const codeSplittingAnalysis = CodeSplittingAnalyzer.analyzeLoadedChunks();
    
    // 전체 점수 계산 (가중 평균)
    const overallScore = Math.round(
      (webVitalsScore * 0.4) + 
      (bundleScore * 0.3) + 
      (codeSplittingScore * 0.3)
    );
    
    const grade = this.getGrade(overallScore);
    const recommendations = this.generateOverallRecommendations(
      webVitalsScore, bundleScore, codeSplittingScore,
      bundleAnalysis, codeSplittingAnalysis
    );
    
    return {
      timestamp,
      environment,
      webVitals: {
        score: webVitalsScore,
        metrics: webVitalsMetrics
      },
      bundle: {
        score: bundleScore,
        analysis: bundleAnalysis
      },
      codeSplitting: {
        score: codeSplittingScore,
        analysis: codeSplittingAnalysis
      },
      overall: {
        score: overallScore,
        grade,
        recommendations
      }
    };
  }

  // 성능 등급 계산
  private getGrade(score: number): string {
    if (score >= 90) return 'A';
    if (score >= 80) return 'B';
    if (score >= 70) return 'C';
    if (score >= 60) return 'D';
    return 'F';
  }

  // 종합 권장사항 생성
  private generateOverallRecommendations(
    webVitalsScore: number,
    bundleScore: number,
    codeSplittingScore: number,
    bundleAnalysis: any,
    codeSplittingAnalysis: any
  ): string[] {
    const recommendations: string[] = [];
    
    // 가장 낮은 점수 영역 우선 개선
    const scores = [
      { name: 'Web Vitals', score: webVitalsScore },
      { name: '번들 최적화', score: bundleScore },
      { name: '코드 스플리팅', score: codeSplittingScore }
    ];
    
    scores.sort((a, b) => a.score - b.score);
    
    if (scores[0].score < 70) {
      recommendations.push(`${scores[0].name} 영역의 개선이 가장 시급합니다 (점수: ${scores[0].score})`);
    }
    
    // 구체적인 권장사항 추가
    if (bundleAnalysis.recommendations.length > 0) {
      recommendations.push(...bundleAnalysis.recommendations.slice(0, 2));
    }
    
    if (codeSplittingAnalysis.recommendations.length > 0) {
      recommendations.push(...codeSplittingAnalysis.recommendations.slice(0, 2));
    }
    
    return recommendations;
  }

  // 성능 저하 감지
  private detectPerformanceDegradation(currentReport: PerformanceReport): void {
    if (this.reports.length < 2) return;
    
    const previousReport = this.reports[this.reports.length - 2];
    const scoreDiff = currentReport.overall.score - previousReport.overall.score;
    
    if (scoreDiff < -10) {
      console.warn(`⚠️ 성능 저하 감지: ${scoreDiff}점 하락`);
      console.warn('이전 점수:', previousReport.overall.score);
      console.warn('현재 점수:', currentReport.overall.score);
    }
  }

  // 리포트 로깅
  private logReport(report: PerformanceReport): void {
    console.group(`📊 성능 리포트 (${report.timestamp})`);
    console.log(`🏆 전체 점수: ${report.overall.score}/100 (${report.overall.grade}등급)`);
    console.log(`📈 Web Vitals: ${report.webVitals.score}/100`);
    console.log(`📦 번들 최적화: ${report.bundle.score}/100`);
    console.log(`🧩 코드 스플리팅: ${report.codeSplitting.score}/100`);
    
    if (report.overall.recommendations.length > 0) {
      console.log('💡 권장사항:');
      report.overall.recommendations.forEach(rec => console.log(`  • ${rec}`));
    }
    
    console.groupEnd();
  }

  // 상세 분석 표시 (데모 모드용)
  private displayDetailedAnalysis(): void {
    console.group('🔍 상세 성능 분석');
    
    console.log('📦 번들 분석:');
    console.log(BundleAnalyzer.generateReport());
    
    console.log('\n🧩 코드 스플리팅 분석:');
    console.log(CodeSplittingAnalyzer.generateReport());
    
    console.log('\n📈 Web Vitals:');
    console.log(performanceMonitor.generateReport());
    
    console.groupEnd();
  }

  // 최신 리포트 가져오기
  getLatestReport(): PerformanceReport | null {
    return this.reports.length > 0 ? this.reports[this.reports.length - 1] : null;
  }

  // 모든 리포트 가져오기
  getAllReports(): PerformanceReport[] {
    return [...this.reports];
  }

  // 모니터링 중지
  stopMonitoring(): void {
    this.isMonitoring = false;
    console.log('⏹️ 성능 모니터링 중지');
  }

  // 성능 데이터 내보내기 (JSON)
  exportData(): string {
    return JSON.stringify({
      reports: this.reports,
      summary: {
        totalReports: this.reports.length,
        averageScore: this.reports.reduce((sum, r) => sum + r.overall.score, 0) / this.reports.length,
        environment: process.env.REACT_APP_ENVIRONMENT
      }
    }, null, 2);
  }
}

// 전역 인스턴스
export const performanceMonitoring = PerformanceMonitoringSystem.getInstance();

// 자동 시작 (프로덕션 환경에서)
if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
  // 페이지 로드 후 모니터링 시작
  if (document.readyState === 'complete') {
    performanceMonitoring.startMonitoring();
  } else {
    window.addEventListener('load', () => {
      performanceMonitoring.startMonitoring();
    });
  }
}

export default PerformanceMonitoringSystem;
export type { PerformanceReport };