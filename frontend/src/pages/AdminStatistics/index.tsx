import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { AppDispatch } from '../../store/store';
import SimpleChart from '../../components/Charts/SimpleChart';
import Button from '../../components/Common/Button';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import { useToast } from '../../components/Common/Toast';
import './AdminStatistics.css';

interface StatisticsData {
  dailyOrders: Array<{ label: string; value: number }>;
  monthlyOrders: Array<{ label: string; value: number }>;
  planStats: Array<{ label: string; value: number; color?: string }>;
  deviceStats: Array<{ label: string; value: number; color?: string }>;
  revenueStats: Array<{ label: string; value: number }>;
  statusStats: Array<{ label: string; value: number; color?: string }>;
}

const AdminStatistics: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { showError } = useToast();
  
  const [loading, setLoading] = useState(true);
  const [statisticsData, setStatisticsData] = useState<StatisticsData | null>(null);
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0]
  });
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'monthly'>('daily');

  useEffect(() => {
    fetchStatistics();
  }, [dateRange, selectedPeriod]);

  const fetchStatistics = async () => {
    setLoading(true);
    try {
      // API 호출 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockData: StatisticsData = {
        dailyOrders: [
          { label: '1/10', value: 15 },
          { label: '1/11', value: 23 },
          { label: '1/12', value: 18 },
          { label: '1/13', value: 31 },
          { label: '1/14', value: 27 },
          { label: '1/15', value: 42 },
          { label: '1/16', value: 38 }
        ],
        monthlyOrders: [
          { label: '10월', value: 450 },
          { label: '11월', value: 520 },
          { label: '12월', value: 680 },
          { label: '1월', value: 750 }
        ],
        planStats: [
          { label: '5G 프리미엄', value: 320, color: '#667eea' },
          { label: '5G 스탠다드', value: 280, color: '#764ba2' },
          { label: 'LTE 베이직', value: 150, color: '#f093fb' },
          { label: 'LTE 플러스', value: 200, color: '#f5576c' }
        ],
        deviceStats: [
          { label: 'iPhone 15 Pro', value: 180, color: '#4facfe' },
          { label: 'iPhone 15', value: 150, color: '#00f2fe' },
          { label: 'Galaxy S24', value: 140, color: '#43e97b' },
          { label: 'Galaxy S24+', value: 120, color: '#38f9d7' },
          { label: '기타', value: 110, color: '#ffecd2' }
        ],
        revenueStats: [
          { label: '1/10', value: 18500000 },
          { label: '1/11', value: 25600000 },
          { label: '1/12', value: 21200000 },
          { label: '1/13', value: 34800000 },
          { label: '1/14', value: 29700000 },
          { label: '1/15', value: 45200000 },
          { label: '1/16', value: 41300000 }
        ],
        statusStats: [
          { label: '접수대기', value: 45, color: '#ffc107' },
          { label: '처리중', value: 32, color: '#17a2b8' },
          { label: '완료', value: 180, color: '#28a745' },
          { label: '취소', value: 8, color: '#dc3545' }
        ]
      };
      
      setStatisticsData(mockData);
    } catch (error) {
      showError('통계 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDateRangeChange = (field: 'startDate' | 'endDate', value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  const handlePeriodChange = (period: 'daily' | 'monthly') => {
    setSelectedPeriod(period);
  };

  const exportReport = () => {
    // 리포트 내보내기 기능 시뮬레이션
    const reportData = {
      period: `${dateRange.startDate} ~ ${dateRange.endDate}`,
      statistics: statisticsData,
      generatedAt: new Date().toISOString()
    };
    
    const dataStr = JSON.stringify(reportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `statistics-report-${dateRange.startDate}-${dateRange.endDate}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      notation: 'compact'
    }).format(amount);
  };

  const calculateTotalRevenue = () => {
    if (!statisticsData) return 0;
    return statisticsData.revenueStats.reduce((sum, item) => sum + item.value, 0);
  };

  const calculateTotalOrders = () => {
    if (!statisticsData) return 0;
    const data = selectedPeriod === 'daily' ? statisticsData.dailyOrders : statisticsData.monthlyOrders;
    return data.reduce((sum, item) => sum + item.value, 0);
  };

  const calculateAverageOrderValue = () => {
    const totalRevenue = calculateTotalRevenue();
    const totalOrders = calculateTotalOrders();
    return totalOrders > 0 ? totalRevenue / totalOrders : 0;
  };

  if (loading) {
    return (
      <div className="admin-statistics__loading">
        <LoadingSpinner size="large" />
        <p>통계 데이터를 불러오는 중...</p>
      </div>
    );
  }

  return (
    <div className="admin-statistics">
      <div className="admin-statistics__header">
        <div className="header-content">
          <h1>통계 및 리포트</h1>
          <p>비즈니스 성과와 트렌드를 분석하세요</p>
        </div>
        <div className="header-actions">
          <Button variant="outline" onClick={exportReport}>
            📊 리포트 내보내기
          </Button>
        </div>
      </div>

      {/* 필터 및 설정 */}
      <div className="statistics-filters">
        <div className="filter-section">
          <div className="date-filters">
            <div className="filter-group">
              <label>시작일</label>
              <input
                type="date"
                value={dateRange.startDate}
                onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
              />
            </div>
            <div className="filter-group">
              <label>종료일</label>
              <input
                type="date"
                value={dateRange.endDate}
                onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
              />
            </div>
          </div>
          
          <div className="period-selector">
            <button
              className={`period-btn ${selectedPeriod === 'daily' ? 'active' : ''}`}
              onClick={() => handlePeriodChange('daily')}
            >
              일별
            </button>
            <button
              className={`period-btn ${selectedPeriod === 'monthly' ? 'active' : ''}`}
              onClick={() => handlePeriodChange('monthly')}
            >
              월별
            </button>
          </div>
        </div>
      </div>

      {/* 주요 지표 */}
      <div className="key-metrics">
        <div className="metric-card">
          <div className="metric-icon">📈</div>
          <div className="metric-content">
            <h3>총 주문 수</h3>
            <div className="metric-value">{calculateTotalOrders().toLocaleString()}건</div>
            <div className="metric-change positive">+12.5%</div>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">💰</div>
          <div className="metric-content">
            <h3>총 매출</h3>
            <div className="metric-value">{formatCurrency(calculateTotalRevenue())}</div>
            <div className="metric-change positive">+18.3%</div>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">🛒</div>
          <div className="metric-content">
            <h3>평균 주문 금액</h3>
            <div className="metric-value">{formatCurrency(calculateAverageOrderValue())}</div>
            <div className="metric-change negative">-2.1%</div>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <h3>완료율</h3>
            <div className="metric-value">
              {statisticsData ? 
                ((statisticsData.statusStats.find(s => s.label === '완료')?.value || 0) / 
                 statisticsData.statusStats.reduce((sum, s) => sum + s.value, 0) * 100).toFixed(1)
                : 0}%
            </div>
            <div className="metric-change positive">+5.2%</div>
          </div>
        </div>
      </div>

      {/* 차트 섹션 */}
      <div className="charts-grid">
        {/* 주문 추이 */}
        <div className="chart-container full-width">
          <SimpleChart
            data={selectedPeriod === 'daily' ? statisticsData?.dailyOrders || [] : statisticsData?.monthlyOrders || []}
            type="line"
            title={`${selectedPeriod === 'daily' ? '일별' : '월별'} 주문 추이`}
            height={300}
          />
        </div>

        {/* 매출 추이 */}
        <div className="chart-container full-width">
          <SimpleChart
            data={statisticsData?.revenueStats.map(item => ({
              ...item,
              value: item.value / 1000000 // 백만원 단위로 변환
            })) || []}
            type="bar"
            title="일별 매출 추이 (백만원)"
            height={300}
          />
        </div>

        {/* 요금제별 가입 통계 */}
        <div className="chart-container">
          <SimpleChart
            data={statisticsData?.planStats || []}
            type="pie"
            title="요금제별 가입 현황"
            height={350}
          />
        </div>

        {/* 단말기별 판매 통계 */}
        <div className="chart-container">
          <SimpleChart
            data={statisticsData?.deviceStats || []}
            type="bar"
            title="단말기별 판매 현황"
            height={350}
          />
        </div>

        {/* 주문 상태 분포 */}
        <div className="chart-container">
          <SimpleChart
            data={statisticsData?.statusStats || []}
            type="pie"
            title="주문 상태 분포"
            height={350}
          />
        </div>

        {/* 성과 지표 테이블 */}
        <div className="chart-container">
          <div className="performance-table">
            <h3>주요 성과 지표</h3>
            <table>
              <thead>
                <tr>
                  <th>지표</th>
                  <th>현재 값</th>
                  <th>전월 대비</th>
                  <th>목표</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>신규 가입자</td>
                  <td>{calculateTotalOrders().toLocaleString()}명</td>
                  <td className="positive">+12.5%</td>
                  <td>800명</td>
                </tr>
                <tr>
                  <td>평균 처리 시간</td>
                  <td>2.3시간</td>
                  <td className="positive">-15.2%</td>
                  <td>2시간</td>
                </tr>
                <tr>
                  <td>고객 만족도</td>
                  <td>4.7/5.0</td>
                  <td className="positive">+3.1%</td>
                  <td>4.5/5.0</td>
                </tr>
                <tr>
                  <td>취소율</td>
                  <td>3.2%</td>
                  <td className="positive">-1.8%</td>
                  <td>5%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminStatistics;