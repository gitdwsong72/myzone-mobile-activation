// 번들 크기 분석 및 최적화 유틸리티

interface BundleInfo {
  name: string;
  size: number;
  gzipSize?: number;
  type: 'js' | 'css' | 'asset';
}

interface BundleAnalysis {
  totalSize: number;
  jsSize: number;
  cssSize: number;
  assetSize: number;
  bundles: BundleInfo[];
  recommendations: string[];
}

class BundleAnalyzer {
  private static readonly SIZE_THRESHOLDS = {
    JS_WARNING: 500 * 1024, // 500KB
    JS_ERROR: 1024 * 1024, // 1MB
    CSS_WARNING: 100 * 1024, // 100KB
    TOTAL_WARNING: 2 * 1024 * 1024, // 2MB
  };

  // 번들 정보 수집
  static collectBundleInfo(): BundleInfo[] {
    const bundles: BundleInfo[] = [];

    // JavaScript 파일 분석
    const scripts = document.querySelectorAll('script[src]');
    scripts.forEach((script: any) => {
      if (script.src && script.src.includes('/static/js/')) {
        bundles.push({
          name: this.extractFileName(script.src),
          size: 0, // 실제 크기는 네트워크 탭에서 확인 필요
          type: 'js'
        });
      }
    });

    // CSS 파일 분석
    const styles = document.querySelectorAll('link[rel="stylesheet"]');
    styles.forEach((style: any) => {
      if (style.href && style.href.includes('/static/css/')) {
        bundles.push({
          name: this.extractFileName(style.href),
          size: 0,
          type: 'css'
        });
      }
    });

    return bundles;
  }

  // 성능 리소스 API를 통한 실제 크기 분석
  static analyzeResourceSizes(): BundleAnalysis {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
    const bundles: BundleInfo[] = [];
    let totalSize = 0;
    let jsSize = 0;
    let cssSize = 0;
    let assetSize = 0;

    resources.forEach(resource => {
      if (resource.name.includes('/static/')) {
        const size = resource.transferSize || resource.decodedBodySize || 0;
        const name = this.extractFileName(resource.name);
        
        let type: 'js' | 'css' | 'asset' = 'asset';
        if (resource.name.includes('.js')) {
          type = 'js';
          jsSize += size;
        } else if (resource.name.includes('.css')) {
          type = 'css';
          cssSize += size;
        } else {
          assetSize += size;
        }

        bundles.push({ name, size, type });
        totalSize += size;
      }
    });

    const recommendations = this.generateRecommendations({
      totalSize,
      jsSize,
      cssSize,
      assetSize,
      bundles,
      recommendations: []
    });

    return {
      totalSize,
      jsSize,
      cssSize,
      assetSize,
      bundles: bundles.sort((a, b) => b.size - a.size),
      recommendations
    };
  }

  // 최적화 권장사항 생성
  private static generateRecommendations(analysis: BundleAnalysis): string[] {
    const recommendations: string[] = [];

    // 전체 번들 크기 검사
    if (analysis.totalSize > this.SIZE_THRESHOLDS.TOTAL_WARNING) {
      recommendations.push(
        `전체 번들 크기가 ${this.formatSize(analysis.totalSize)}로 큽니다. 코드 스플리팅을 고려하세요.`
      );
    }

    // JavaScript 번들 크기 검사
    if (analysis.jsSize > this.SIZE_THRESHOLDS.JS_ERROR) {
      recommendations.push(
        `JavaScript 번들이 ${this.formatSize(analysis.jsSize)}로 매우 큽니다. 동적 임포트를 사용하세요.`
      );
    } else if (analysis.jsSize > this.SIZE_THRESHOLDS.JS_WARNING) {
      recommendations.push(
        `JavaScript 번들이 ${this.formatSize(analysis.jsSize)}입니다. 최적화를 고려하세요.`
      );
    }

    // CSS 번들 크기 검사
    if (analysis.cssSize > this.SIZE_THRESHOLDS.CSS_WARNING) {
      recommendations.push(
        `CSS 번들이 ${this.formatSize(analysis.cssSize)}입니다. 사용하지 않는 스타일을 제거하세요.`
      );
    }

    // 큰 개별 파일 검사
    analysis.bundles.forEach(bundle => {
      if (bundle.type === 'js' && bundle.size > this.SIZE_THRESHOLDS.JS_WARNING) {
        recommendations.push(
          `${bundle.name} 파일이 ${this.formatSize(bundle.size)}로 큽니다. 분할을 고려하세요.`
        );
      }
    });

    // 일반적인 최적화 권장사항
    if (recommendations.length === 0) {
      recommendations.push('번들 크기가 적절합니다. 계속 모니터링하세요.');
    }

    return recommendations;
  }

  // 파일명 추출
  private static extractFileName(url: string): string {
    return url.split('/').pop() || url;
  }

  // 크기 포맷팅
  private static formatSize(bytes: number): string {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // 번들 분석 리포트 생성
  static generateReport(): string {
    const analysis = this.analyzeResourceSizes();
    
    let report = `
📦 번들 분석 리포트
==================

📊 전체 크기: ${this.formatSize(analysis.totalSize)}
🟨 JavaScript: ${this.formatSize(analysis.jsSize)}
🟦 CSS: ${this.formatSize(analysis.cssSize)}
🟩 기타 자산: ${this.formatSize(analysis.assetSize)}

📋 개별 파일:
${analysis.bundles.map(bundle => 
  `  ${bundle.type.toUpperCase()}: ${bundle.name} (${this.formatSize(bundle.size)})`
).join('\n')}

💡 권장사항:
${analysis.recommendations.map(rec => `  • ${rec}`).join('\n')}
    `.trim();

    return report;
  }

  // 성능 점수 계산 (0-100)
  static calculatePerformanceScore(): number {
    const analysis = this.analyzeResourceSizes();
    let score = 100;

    // 전체 크기 점수
    if (analysis.totalSize > this.SIZE_THRESHOLDS.TOTAL_WARNING) {
      score -= 30;
    } else if (analysis.totalSize > this.SIZE_THRESHOLDS.TOTAL_WARNING * 0.7) {
      score -= 15;
    }

    // JavaScript 크기 점수
    if (analysis.jsSize > this.SIZE_THRESHOLDS.JS_ERROR) {
      score -= 25;
    } else if (analysis.jsSize > this.SIZE_THRESHOLDS.JS_WARNING) {
      score -= 10;
    }

    // CSS 크기 점수
    if (analysis.cssSize > this.SIZE_THRESHOLDS.CSS_WARNING) {
      score -= 15;
    }

    return Math.max(0, score);
  }
}

export default BundleAnalyzer;
export type { BundleInfo, BundleAnalysis };