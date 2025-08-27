import React, { useState, useEffect } from 'react';
import { performanceMonitoring, PerformanceReport } from '../../utils/performanceMonitoring';
import './PerformanceDashboard.css';

interface PerformanceDashboardProps {
  isVisible: boolean;
  onClose: () => void;
}

const PerformanceDashboard: React.FC<PerformanceDashboardProps> = ({ isVisible, onClose }) => {
  const [report, setReport] = useState<PerformanceReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isVisible) {
      // 최신 리포트 가져오기
      const latestReport = performanceMonitoring.getLatestReport();
      if (latestReport) {
        setReport(latestReport);
        setIsLoading(false);
      } else {
        // 리포트가 없으면 새로 생성
        setTimeout(() => {
          const newReport = performanceMonitoring.generateReport();
          setReport(newReport);
          setIsLoading(false);
        }, 1000);
      }
    }
  }, [isVisible]);

  const handleExportData = () => {
    const data = performanceMonitoring.exportData();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `performance-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getScoreColor = (score: number): string => {
    if (score >= 90) return '#28a745';
    if (score >= 80) return '#ffc107';
    if (score >= 70) return '#fd7e14';
    return '#dc3545';
  };

  const formatSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!isVisible) return null;

  return (
    <div className="performance-dashboard-overlay">
      <div className="performance-dashboard">
        <div className="dashboard-header">
          <h2>📊 성능 대시보드</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        {isLoading ? (
          <div className="loading">
            <div className="spinner"></div>
            <p>성능 데이터를 분석하는 중...</p>
          </div>
        ) : report ? (
          <div className="dashboard-content">
            {/* 전체 점수 */}
            <div className="score-section">
              <div className="overall-score">
                <div 
                  className="score-circle"
                  style={{ borderColor: getScoreColor(report.overall.score) }}
                >
                  <span className="score-number">{report.overall.score}</span>
                  <span className="score-grade">{report.overall.grade}</span>
                </div>
                <div className="score-info">
                  <h3>전체 성능 점수</h3>
                  <p>환경: {report.environment}</p>
                  <p>측정 시간: {new Date(report.timestamp).toLocaleString('ko-KR')}</p>
                </div>
              </div>
            </div>

            {/* 세부 점수 */}
            <div className="metrics-grid">
              <div className="metric-card">
                <h4>📈 Web Vitals</h4>
                <div className="metric-score" style={{ color: getScoreColor(report.webVitals.score) }}>
                  {report.webVitals.score}/100
                </div>
                <div className="metric-details">
                  {report.webVitals.metrics.fcp && (
                    <p>FCP: {report.webVitals.metrics.fcp.toFixed(0)}ms</p>
                  )}
                  {report.webVitals.metrics.lcp && (
                    <p>LCP: {report.webVitals.metrics.lcp.toFixed(0)}ms</p>
                  )}
                  {report.webVitals.metrics.fid && (
                    <p>FID: {report.webVitals.metrics.fid.toFixed(0)}ms</p>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <h4>📦 번들 최적화</h4>
                <div className="metric-score" style={{ color: getScoreColor(report.bundle.score) }}>
                  {report.bundle.score}/100
                </div>
                <div className="metric-details">
                  <p>총 크기: {formatSize(report.bundle.analysis.totalSize)}</p>
                  <p>JS: {formatSize(report.bundle.analysis.jsSize)}</p>
                  <p>CSS: {formatSize(report.bundle.analysis.cssSize)}</p>
                </div>
              </div>

              <div className="metric-card">
                <h4>🧩 코드 스플리팅</h4>
                <div className="metric-score" style={{ color: getScoreColor(report.codeSplitting.score) }}>
                  {report.codeSplitting.score}/100
                </div>
                <div className="metric-details">
                  <p>청크 수: {report.codeSplitting.analysis.totalChunks}</p>
                  <p>평균 로딩: {report.codeSplitting.analysis.averageLoadTime.toFixed(0)}ms</p>
                  <p>캐시율: {report.codeSplitting.analysis.cacheHitRate.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            {/* 권장사항 */}
            {report.overall.recommendations.length > 0 && (
              <div className="recommendations">
                <h4>💡 개선 권장사항</h4>
                <ul>
                  {report.overall.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* 액션 버튼 */}
            <div className="dashboard-actions">
              <button className="export-button" onClick={handleExportData}>
                📄 데이터 내보내기
              </button>
              <button 
                className="refresh-button" 
                onClick={() => {
                  setIsLoading(true);
                  setTimeout(() => {
                    const newReport = performanceMonitoring.generateReport();
                    setReport(newReport);
                    setIsLoading(false);
                  }, 1000);
                }}
              >
                🔄 새로고침
              </button>
            </div>
          </div>
        ) : (
          <div className="no-data">
            <p>성능 데이터를 사용할 수 없습니다.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceDashboard;