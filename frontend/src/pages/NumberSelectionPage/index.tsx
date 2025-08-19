import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { 
  fetchNumbers, 
  searchNumbers, 
  reserveNumber, 
  releaseNumber,
  filterByCategory, 
  setSearchPattern,
  decrementTimer,
  clearReservation 
} from '../../store/slices/numberSlice';
import { useToast } from '../../components/Common/Toast';
import Button from '../../components/Common/Button';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import ProgressBar from '../../components/Common/ProgressBar';
import './NumberSelectionPage.css';

interface PhoneNumber {
  id: number;
  number: string;
  category: string;
  additionalFee: number;
  status: 'available' | 'reserved' | 'taken';
  reservedUntil?: string;
  isPopular?: boolean;
  pattern?: string;
}

const NumberSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { showError, showSuccess, showInfo } = useToast();
  
  const { 
    filteredNumbers, 
    selectedCategory, 
    searchPattern,
    reservedNumber, 
    reservationTimer,
    loading, 
    error 
  } = useAppSelector(state => state.numbers);
  
  const [searchInput, setSearchInput] = useState('');
  const [selectedNumber, setSelectedNumber] = useState<PhoneNumber | null>(null);

  const categories = [
    { id: 'all', name: '전체', icon: '📱', description: '모든 번호' },
    { id: 'general', name: '일반번호', icon: '📞', description: '추가 요금 없음' },
    { id: 'consecutive', name: '연속번호', icon: '🔢', description: '1234, 5678 등' },
    { id: 'special', name: '특별번호', icon: '⭐', description: '0000, 1111 등' },
    { id: 'lucky', name: '행운번호', icon: '🍀', description: '7777, 8888 등' },
    { id: 'premium', name: '프리미엄', icon: '💎', description: '최고급 번호' },
  ];

  // 모의 데이터 (실제로는 API에서 가져옴)
  const mockNumbers: PhoneNumber[] = [
    // 일반번호
    { id: 1, number: '010-1234-5678', category: 'general', additionalFee: 0, status: 'available' },
    { id: 2, number: '010-2345-6789', category: 'general', additionalFee: 0, status: 'available' },
    { id: 3, number: '010-3456-7890', category: 'general', additionalFee: 0, status: 'available' },
    { id: 4, number: '010-4567-8901', category: 'general', additionalFee: 0, status: 'available' },
    { id: 5, number: '010-5678-9012', category: 'general', additionalFee: 0, status: 'available' },
    
    // 연속번호
    { id: 6, number: '010-1234-1234', category: 'consecutive', additionalFee: 10000, status: 'available', pattern: '1234' },
    { id: 7, number: '010-5678-5678', category: 'consecutive', additionalFee: 10000, status: 'available', pattern: '5678' },
    { id: 8, number: '010-9876-9876', category: 'consecutive', additionalFee: 10000, status: 'reserved', pattern: '9876' },
    { id: 9, number: '010-1357-1357', category: 'consecutive', additionalFee: 15000, status: 'available', pattern: '1357' },
    
    // 특별번호
    { id: 10, number: '010-0000-1234', category: 'special', additionalFee: 30000, status: 'available', pattern: '0000', isPopular: true },
    { id: 11, number: '010-1111-2345', category: 'special', additionalFee: 30000, status: 'available', pattern: '1111', isPopular: true },
    { id: 12, number: '010-2222-3456', category: 'special', additionalFee: 30000, status: 'taken', pattern: '2222' },
    { id: 13, number: '010-3333-4567', category: 'special', additionalFee: 30000, status: 'available', pattern: '3333' },
    
    // 행운번호
    { id: 14, number: '010-7777-1234', category: 'lucky', additionalFee: 50000, status: 'available', pattern: '7777', isPopular: true },
    { id: 15, number: '010-8888-2345', category: 'lucky', additionalFee: 50000, status: 'available', pattern: '8888', isPopular: true },
    { id: 16, number: '010-9999-3456', category: 'lucky', additionalFee: 50000, status: 'reserved', pattern: '9999' },
    
    // 프리미엄
    { id: 17, number: '010-0001-0001', category: 'premium', additionalFee: 100000, status: 'available', pattern: '0001', isPopular: true },
    { id: 18, number: '010-1004-1004', category: 'premium', additionalFee: 80000, status: 'available', pattern: '1004' },
    { id: 19, number: '010-1212-1212', category: 'premium', additionalFee: 70000, status: 'available', pattern: '1212' },
  ];

  useEffect(() => {
    // 실제로는 dispatch(fetchNumbers()) 사용
    // 여기서는 모의 데이터 사용
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      showError(error);
    }
  }, [error, showError]);

  // 예약 타이머 관리
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (reservationTimer > 0) {
      interval = setInterval(() => {
        dispatch(decrementTimer());
      }, 1000);
    } else if (reservationTimer === 0 && reservedNumber) {
      dispatch(clearReservation());
      showInfo('번호 예약이 만료되었습니다.');
    }
    return () => clearInterval(interval);
  }, [reservationTimer, reservedNumber, dispatch, showInfo]);

  const handleCategoryFilter = (category: string) => {
    dispatch(filterByCategory(category));
  };

  const handleSearch = () => {
    if (!searchInput.trim()) {
      showError('검색어를 입력해주세요.');
      return;
    }
    
    dispatch(setSearchPattern(searchInput));
    // 실제로는 dispatch(searchNumbers(searchInput)) 사용
    showInfo(`"${searchInput}" 패턴으로 검색합니다.`);
  };

  const handleNumberReserve = async (number: PhoneNumber) => {
    if (number.status !== 'available') {
      showError('선택할 수 없는 번호입니다.');
      return;
    }

    if (reservedNumber) {
      showError('이미 예약된 번호가 있습니다. 기존 예약을 해제하고 다시 시도해주세요.');
      return;
    }

    try {
      // 실제로는 dispatch(reserveNumber(number.id)) 사용
      setSelectedNumber(number);
      showSuccess(`${number.number} 번호가 30분간 예약되었습니다.`);
      
      // 모의 예약 처리
      setTimeout(() => {
        dispatch({
          type: 'numbers/reserveNumber/fulfilled',
          payload: number
        });
      }, 500);
    } catch (error) {
      showError('번호 예약 중 오류가 발생했습니다.');
    }
  };

  const handleReservationRelease = () => {
    if (!reservedNumber) return;
    
    dispatch(releaseNumber(reservedNumber.id));
    setSelectedNumber(null);
    showSuccess('번호 예약이 해제되었습니다.');
  };

  const handleConfirmSelection = () => {
    if (!reservedNumber) {
      showError('번호를 선택해주세요.');
      return;
    }
    
    showSuccess(`${reservedNumber.number} 번호가 최종 선택되었습니다.`);
    navigate('/summary');
  };

  const formatPrice = (price: number) => {
    if (price === 0) return '무료';
    return `+${new Intl.NumberFormat('ko-KR').format(price)}원`;
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getFilteredNumbers = () => {
    let filtered = mockNumbers;
    
    // 카테고리 필터링
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(number => number.category === selectedCategory);
    }
    
    // 검색 패턴 필터링
    if (searchPattern) {
      filtered = filtered.filter(number => 
        number.number.includes(searchPattern) || 
        (number.pattern && number.pattern.includes(searchPattern))
      );
    }
    
    return filtered;
  };

  const getSuggestedNumbers = (originalNumber: PhoneNumber) => {
    return mockNumbers
      .filter(num => 
        num.id !== originalNumber.id && 
        num.category === originalNumber.category &&
        num.status === 'available'
      )
      .slice(0, 3);
  };

  if (loading) {
    return (
      <div className="number-selection-page">
        <div className="loading-container">
          <LoadingSpinner size="large" />
          <p>번호 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="number-selection-page">
      {/* 진행률 표시 */}
      <div className="progress-section">
        <ProgressBar current={4} total={5} />
        <p className="progress-text">4단계: 번호 선택</p>
      </div>

      {/* 페이지 헤더 */}
      <div className="page-header">
        <h1 className="page-title">번호 선택</h1>
        <p className="page-description">
          원하는 전화번호를 선택하세요. 선택한 번호는 30분간 예약됩니다.
        </p>
      </div>

      {/* 예약 상태 표시 */}
      {reservedNumber && (
        <div className="reservation-status">
          <div className="reservation-info">
            <div className="reserved-number">
              <span className="number-text">{reservedNumber.number}</span>
              <span className="reservation-label">예약됨</span>
            </div>
            <div className="reservation-timer">
              <span className="timer-label">남은 시간:</span>
              <span className="timer-value">{formatTimer(reservationTimer)}</span>
            </div>
          </div>
          <div className="reservation-actions">
            <Button
              variant="outline"
              size="small"
              onClick={handleReservationRelease}
            >
              예약 해제
            </Button>
            <Button
              variant="primary"
              size="small"
              onClick={handleConfirmSelection}
            >
              선택 완료
            </Button>
          </div>
        </div>
      )}

      {/* 검색 섹션 */}
      <div className="search-section">
        <div className="search-container">
          <div className="search-input-group">
            <input
              type="text"
              className="search-input"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="원하는 번호나 패턴을 입력하세요 (예: 1234, 7777)"
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button
              variant="primary"
              onClick={handleSearch}
              className="search-button"
            >
              검색
            </Button>
          </div>
          <div className="search-tips">
            <span className="tips-label">검색 팁:</span>
            <span className="tip-item">끝자리 4자리 (예: 1234)</span>
            <span className="tip-item">반복 패턴 (예: 7777)</span>
            <span className="tip-item">특정 숫자 포함 (예: 8)</span>
          </div>
        </div>
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
              <div className="category-info">
                <span className="category-name">{category.name}</span>
                <span className="category-description">{category.description}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 번호 목록 */}
      <div className="numbers-section">
        <div className="section-header">
          <h3 className="section-title">
            {selectedCategory === 'all' ? '전체 번호' : categories.find(c => c.id === selectedCategory)?.name}
          </h3>
          <span className="numbers-count">
            {getFilteredNumbers().length}개 번호
          </span>
        </div>

        <div className="numbers-grid">
          {getFilteredNumbers().map(number => (
            <div 
              key={number.id} 
              className={`number-card ${number.status} ${reservedNumber?.id === number.id ? 'reserved-by-me' : ''}`}
            >
              {number.isPopular && (
                <div className="number-badge popular">인기</div>
              )}
              {number.status === 'reserved' && reservedNumber?.id !== number.id && (
                <div className="number-badge reserved">예약중</div>
              )}
              {number.status === 'taken' && (
                <div className="number-badge taken">사용중</div>
              )}
              
              <div className="number-display">
                <span className="number-text">{number.number}</span>
                {number.pattern && (
                  <span className="number-pattern">패턴: {number.pattern}</span>
                )}
              </div>

              <div className="number-info">
                <div className="number-category">
                  <span className="category-icon">
                    {categories.find(c => c.id === number.category)?.icon}
                  </span>
                  <span className="category-name">
                    {categories.find(c => c.id === number.category)?.name}
                  </span>
                </div>
                
                <div className="number-fee">
                  <span className="fee-label">추가 요금:</span>
                  <span className="fee-value">{formatPrice(number.additionalFee)}</span>
                </div>
              </div>

              <div className="number-actions">
                {number.status === 'available' && (
                  <Button
                    variant="primary"
                    fullWidth
                    onClick={() => handleNumberReserve(number)}
                    disabled={!!reservedNumber}
                    className="reserve-button"
                  >
                    {reservedNumber ? '다른 번호 예약중' : '이 번호 선택'}
                  </Button>
                )}
                
                {number.status === 'reserved' && reservedNumber?.id === number.id && (
                  <Button
                    variant="success"
                    fullWidth
                    disabled
                    className="reserved-button"
                  >
                    예약됨 ({formatTimer(reservationTimer)})
                  </Button>
                )}
                
                {number.status === 'reserved' && reservedNumber?.id !== number.id && (
                  <div className="unavailable-info">
                    <span className="unavailable-text">다른 고객이 예약중</span>
                    <div className="suggested-numbers">
                      <span className="suggested-label">비슷한 번호:</span>
                      <div className="suggested-list">
                        {getSuggestedNumbers(number).map(suggested => (
                          <button
                            key={suggested.id}
                            className="suggested-number"
                            onClick={() => handleNumberReserve(suggested)}
                            disabled={!!reservedNumber}
                          >
                            {suggested.number.split('-')[2]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
                
                {number.status === 'taken' && (
                  <div className="unavailable-info">
                    <span className="unavailable-text">사용중인 번호</span>
                    <div className="suggested-numbers">
                      <span className="suggested-label">대안 번호:</span>
                      <div className="suggested-list">
                        {getSuggestedNumbers(number).map(suggested => (
                          <button
                            key={suggested.id}
                            className="suggested-number"
                            onClick={() => handleNumberReserve(suggested)}
                            disabled={!!reservedNumber}
                          >
                            {suggested.number.split('-')[2]}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {getFilteredNumbers().length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">📱</div>
            <h3>검색 결과가 없습니다</h3>
            <p>다른 검색어나 카테고리를 시도해보세요</p>
            <Button
              variant="outline"
              onClick={() => {
                setSearchInput('');
                dispatch(setSearchPattern(''));
                handleCategoryFilter('all');
              }}
            >
              전체 번호 보기
            </Button>
          </div>
        )}
      </div>

      {/* 하단 액션 */}
      <div className="page-actions">
        <Button
          variant="outline"
          size="large"
          onClick={() => navigate('/devices')}
          className="back-button"
        >
          이전 단계
        </Button>
        <Button
          variant="primary"
          size="large"
          onClick={handleConfirmSelection}
          disabled={!reservedNumber}
          className="next-button"
        >
          다음 단계
        </Button>
      </div>
    </div>
  );
};

export default NumberSelectionPage;