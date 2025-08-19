import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchPlans, filterByCategory } from '../../store/slices/planSlice';
import { useToast } from '../../components/Common/Toast';
import Button from '../../components/Common/Button';
import Modal from '../../components/Common/Modal';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import ProgressBar from '../../components/Common/ProgressBar';
import './PlanSelectionPage.css';

interface Plan {
  id: number;
  name: string;
  description: string;
  monthlyFee: number;
  dataLimit: string;
  callMinutes: number;
  smsCount: number;
  category: string;
  isActive: boolean;
  originalPrice?: number;
  discount?: number;
  features?: string[];
  terms?: string;
}

const PlanSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { showError, showSuccess } = useToast();
  
  const { filteredPlans, selectedCategory, loading, error } = useAppSelector(state => state.plans);
  
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [compareList, setCompareList] = useState<Plan[]>([]);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [sortBy, setSortBy] = useState<'price' | 'data' | 'popular'>('popular');

  const categories = [
    { id: 'all', name: '전체', icon: '📱' },
    { id: '5G', name: '5G 요금제', icon: '🚀' },
    { id: 'LTE', name: 'LTE 요금제', icon: '📶' },
    { id: 'data', name: '데이터 중심', icon: '📊' },
    { id: 'call', name: '통화 중심', icon: '📞' },
    { id: 'family', name: '가족 요금제', icon: '👨‍👩‍👧‍👦' },
  ];

  useEffect(() => {
    dispatch(fetchPlans());
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      showError(error);
    }
  }, [error, showError]);

  const handleCategoryFilter = (category: string) => {
    dispatch(filterByCategory(category));
  };

  const handlePlanSelect = (plan: Plan) => {
    // 주문 상태에 선택된 요금제 저장 (Redux)
    // dispatch(setSelectedPlan(plan));
    showSuccess(`${plan.name} 요금제가 선택되었습니다.`);
    navigate('/user-info');
  };

  const handleShowDetail = (plan: Plan) => {
    setSelectedPlan(plan);
    setShowDetailModal(true);
  };

  const handleAddToCompare = (plan: Plan) => {
    if (compareList.length >= 3) {
      showError('최대 3개까지만 비교할 수 있습니다.');
      return;
    }
    
    if (compareList.find(p => p.id === plan.id)) {
      showError('이미 비교 목록에 추가된 요금제입니다.');
      return;
    }
    
    setCompareList([...compareList, plan]);
    showSuccess(`${plan.name}이(가) 비교 목록에 추가되었습니다.`);
  };

  const handleRemoveFromCompare = (planId: number) => {
    setCompareList(compareList.filter(p => p.id !== planId));
  };

  const handleShowCompare = () => {
    if (compareList.length < 2) {
      showError('비교하려면 최소 2개의 요금제를 선택해주세요.');
      return;
    }
    setShowCompareModal(true);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  const formatData = (dataLimit: string) => {
    if (dataLimit === 'unlimited') return '무제한';
    if (dataLimit.includes('GB')) return dataLimit;
    return `${dataLimit}GB`;
  };

  const getSortedPlans = () => {
    const plans = [...filteredPlans];
    switch (sortBy) {
      case 'price':
        return plans.sort((a, b) => a.monthlyFee - b.monthlyFee);
      case 'data':
        return plans.sort((a, b) => {
          if (a.dataLimit === 'unlimited') return -1;
          if (b.dataLimit === 'unlimited') return 1;
          return parseInt(b.dataLimit) - parseInt(a.dataLimit);
        });
      case 'popular':
      default:
        return plans;
    }
  };

  if (loading) {
    return (
      <div className="plan-selection-page">
        <div className="loading-container">
          <LoadingSpinner size="large" />
          <p>요금제 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="plan-selection-page">
      {/* 진행률 표시 */}
      <div className="progress-section">
        <ProgressBar current={1} total={5} />
        <p className="progress-text">1단계: 요금제 선택</p>
      </div>

      {/* 페이지 헤더 */}
      <div className="page-header">
        <h1 className="page-title">요금제 선택</h1>
        <p className="page-description">
          나에게 맞는 최적의 요금제를 선택해보세요
        </p>
      </div>

      {/* 카테고리 필터 */}
      <div className="category-filter">
        <div className="category-tabs">
          {categories.map(category => (
            <button
              key={category.id}
              className={`category-tab ${selectedCategory === category.id ? 'active' : ''}`}
              onClick={() => handleCategoryFilter(category.id)}
            >
              <span className="category-icon">{category.icon}</span>
              <span className="category-name">{category.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 정렬 및 비교 옵션 */}
      <div className="filter-controls">
        <div className="sort-options">
          <label htmlFor="sort-select">정렬:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'price' | 'data' | 'popular')}
            className="sort-select"
          >
            <option value="popular">인기순</option>
            <option value="price">가격순</option>
            <option value="data">데이터순</option>
          </select>
        </div>

        <div className="compare-section">
          {compareList.length > 0 && (
            <div className="compare-info">
              <span className="compare-count">
                비교 목록: {compareList.length}/3
              </span>
              <Button
                variant="outline"
                size="small"
                onClick={handleShowCompare}
                disabled={compareList.length < 2}
              >
                비교하기
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* 요금제 목록 */}
      <div className="plans-grid">
        {getSortedPlans().map(plan => (
          <div key={plan.id} className="plan-card">
            {plan.discount && (
              <div className="plan-badge">
                {plan.discount}% 할인
              </div>
            )}
            
            <div className="plan-header">
              <h3 className="plan-name">{plan.name}</h3>
              <p className="plan-description">{plan.description}</p>
            </div>

            <div className="plan-price">
              {plan.originalPrice && (
                <span className="original-price">
                  {formatPrice(plan.originalPrice)}원
                </span>
              )}
              <span className="current-price">
                월 {formatPrice(plan.monthlyFee)}원
              </span>
            </div>

            <div className="plan-features">
              <div className="feature-item">
                <span className="feature-icon">📊</span>
                <span className="feature-text">
                  데이터 {formatData(plan.dataLimit)}
                </span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">📞</span>
                <span className="feature-text">
                  음성통화 {plan.callMinutes === -1 ? '무제한' : `${plan.callMinutes}분`}
                </span>
              </div>
              <div className="feature-item">
                <span className="feature-icon">💬</span>
                <span className="feature-text">
                  문자 {plan.smsCount === -1 ? '무제한' : `${plan.smsCount}건`}
                </span>
              </div>
            </div>

            <div className="plan-actions">
              <Button
                variant="primary"
                fullWidth
                onClick={() => handlePlanSelect(plan)}
                className="select-button"
              >
                이 요금제 선택
              </Button>
              
              <div className="secondary-actions">
                <Button
                  variant="outline"
                  size="small"
                  onClick={() => handleShowDetail(plan)}
                >
                  상세보기
                </Button>
                <Button
                  variant="outline"
                  size="small"
                  onClick={() => handleAddToCompare(plan)}
                  disabled={compareList.find(p => p.id === plan.id) !== undefined}
                >
                  비교하기
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredPlans.length === 0 && !loading && (
        <div className="empty-state">
          <div className="empty-icon">📱</div>
          <h3>해당 카테고리에 요금제가 없습니다</h3>
          <p>다른 카테고리를 선택해보세요</p>
        </div>
      )}

      {/* 요금제 상세 모달 */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title={selectedPlan?.name || ''}
        size="large"
      >
        {selectedPlan && (
          <div className="plan-detail-modal">
            <div className="detail-header">
              <div className="detail-price">
                <span className="price-label">월 요금</span>
                <span className="price-value">
                  {formatPrice(selectedPlan.monthlyFee)}원
                </span>
              </div>
            </div>

            <div className="detail-content">
              <div className="detail-section">
                <h4>포함 서비스</h4>
                <ul className="feature-list">
                  <li>데이터: {formatData(selectedPlan.dataLimit)}</li>
                  <li>음성통화: {selectedPlan.callMinutes === -1 ? '무제한' : `${selectedPlan.callMinutes}분`}</li>
                  <li>문자메시지: {selectedPlan.smsCount === -1 ? '무제한' : `${selectedPlan.smsCount}건`}</li>
                </ul>
              </div>

              {selectedPlan.features && (
                <div className="detail-section">
                  <h4>추가 혜택</h4>
                  <ul className="feature-list">
                    {selectedPlan.features.map((feature, index) => (
                      <li key={index}>{feature}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedPlan.terms && (
                <div className="detail-section">
                  <h4>이용 약관</h4>
                  <p className="terms-text">{selectedPlan.terms}</p>
                </div>
              )}
            </div>

            <div className="detail-actions">
              <Button
                variant="primary"
                onClick={() => {
                  setShowDetailModal(false);
                  handlePlanSelect(selectedPlan);
                }}
                className="select-button"
              >
                이 요금제 선택
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowDetailModal(false)}
              >
                닫기
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 요금제 비교 모달 */}
      <Modal
        isOpen={showCompareModal}
        onClose={() => setShowCompareModal(false)}
        title="요금제 비교"
        size="large"
      >
        <div className="plan-compare-modal">
          <div className="compare-table">
            <div className="compare-header">
              <div className="compare-cell">항목</div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  <div className="compare-plan-name">{plan.name}</div>
                  <Button
                    variant="outline"
                    size="small"
                    onClick={() => handleRemoveFromCompare(plan.id)}
                    className="remove-button"
                  >
                    제거
                  </Button>
                </div>
              ))}
            </div>

            <div className="compare-row">
              <div className="compare-cell compare-label">월 요금</div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  {formatPrice(plan.monthlyFee)}원
                </div>
              ))}
            </div>

            <div className="compare-row">
              <div className="compare-cell compare-label">데이터</div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  {formatData(plan.dataLimit)}
                </div>
              ))}
            </div>

            <div className="compare-row">
              <div className="compare-cell compare-label">음성통화</div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  {plan.callMinutes === -1 ? '무제한' : `${plan.callMinutes}분`}
                </div>
              ))}
            </div>

            <div className="compare-row">
              <div className="compare-cell compare-label">문자</div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  {plan.smsCount === -1 ? '무제한' : `${plan.smsCount}건`}
                </div>
              ))}
            </div>

            <div className="compare-actions">
              <div className="compare-cell"></div>
              {compareList.map(plan => (
                <div key={plan.id} className="compare-cell">
                  <Button
                    variant="primary"
                    size="small"
                    onClick={() => {
                      setShowCompareModal(false);
                      handlePlanSelect(plan);
                    }}
                  >
                    선택
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default PlanSelectionPage;