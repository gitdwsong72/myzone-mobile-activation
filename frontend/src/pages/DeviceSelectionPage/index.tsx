import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { fetchDevices, filterByBrand } from '../../store/slices/deviceSlice';
import { useToast } from '../../components/Common/Toast';
import Button from '../../components/Common/Button';
import Modal from '../../components/Common/Modal';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import ProgressBar from '../../components/Common/ProgressBar';
import './DeviceSelectionPage.css';

interface Device {
  id: number;
  brand: string;
  model: string;
  colors: string[];
  price: number;
  stockQuantity: number;
  specifications: {
    display: string;
    camera: string;
    battery: string;
    storage: string;
    ram: string;
    os: string;
  };
  images: {
    [color: string]: string[];
  };
  isActive: boolean;
  isPopular?: boolean;
  discount?: number;
  originalPrice?: number;
}

interface DeliveryInfo {
  address: {
    zipCode: string;
    address1: string;
    address2: string;
  };
  deliveryTime: string;
  deliveryNote: string;
  receiverName: string;
  receiverPhone: string;
}

const DeviceSelectionPage: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { showError, showSuccess, showInfo } = useToast();
  
  const { filteredDevices, selectedBrand, loading, error } = useAppSelector(state => state.devices);
  
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [selectedColor, setSelectedColor] = useState<string>('');
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showDeliveryModal, setShowDeliveryModal] = useState(false);
  const [deliveryInfo, setDeliveryInfo] = useState<DeliveryInfo>({
    address: {
      zipCode: '',
      address1: '',
      address2: '',
    },
    deliveryTime: '',
    deliveryNote: '',
    receiverName: '',
    receiverPhone: '',
  });
  const [sortBy, setSortBy] = useState<'popular' | 'price-low' | 'price-high' | 'brand'>('popular');

  const brands = [
    { id: 'all', name: '전체', icon: '📱' },
    { id: 'Samsung', name: '삼성', icon: '📱' },
    { id: 'Apple', name: '애플', icon: '🍎' },
    { id: 'LG', name: 'LG', icon: '📱' },
    { id: 'Google', name: '구글', icon: '🔍' },
    { id: 'Xiaomi', name: '샤오미', icon: '📱' },
  ];

  const deliveryTimes = [
    { value: 'morning', label: '오전 (09:00~12:00)' },
    { value: 'afternoon', label: '오후 (12:00~18:00)' },
    { value: 'evening', label: '저녁 (18:00~21:00)' },
    { value: 'anytime', label: '시간 무관' },
  ];

  // 모의 데이터 (실제로는 API에서 가져옴)
  const mockDevices: Device[] = [
    {
      id: 1,
      brand: 'Samsung',
      model: 'Galaxy S24 Ultra',
      colors: ['Titanium Black', 'Titanium Gray', 'Titanium Violet', 'Titanium Yellow'],
      price: 1398000,
      originalPrice: 1498000,
      discount: 7,
      stockQuantity: 15,
      specifications: {
        display: '6.8인치 Dynamic AMOLED 2X',
        camera: '200MP + 50MP + 12MP + 10MP',
        battery: '5000mAh',
        storage: '256GB',
        ram: '12GB',
        os: 'Android 14'
      },
      images: {
        'Titanium Black': ['/images/galaxy-s24-ultra-black-1.jpg', '/images/galaxy-s24-ultra-black-2.jpg'],
        'Titanium Gray': ['/images/galaxy-s24-ultra-gray-1.jpg', '/images/galaxy-s24-ultra-gray-2.jpg'],
        'Titanium Violet': ['/images/galaxy-s24-ultra-violet-1.jpg', '/images/galaxy-s24-ultra-violet-2.jpg'],
        'Titanium Yellow': ['/images/galaxy-s24-ultra-yellow-1.jpg', '/images/galaxy-s24-ultra-yellow-2.jpg'],
      },
      isActive: true,
      isPopular: true,
    },
    {
      id: 2,
      brand: 'Apple',
      model: 'iPhone 15 Pro',
      colors: ['Natural Titanium', 'Blue Titanium', 'White Titanium', 'Black Titanium'],
      price: 1350000,
      stockQuantity: 8,
      specifications: {
        display: '6.1인치 Super Retina XDR',
        camera: '48MP + 12MP + 12MP',
        battery: '3274mAh',
        storage: '128GB',
        ram: '8GB',
        os: 'iOS 17'
      },
      images: {
        'Natural Titanium': ['/images/iphone-15-pro-natural-1.jpg', '/images/iphone-15-pro-natural-2.jpg'],
        'Blue Titanium': ['/images/iphone-15-pro-blue-1.jpg', '/images/iphone-15-pro-blue-2.jpg'],
        'White Titanium': ['/images/iphone-15-pro-white-1.jpg', '/images/iphone-15-pro-white-2.jpg'],
        'Black Titanium': ['/images/iphone-15-pro-black-1.jpg', '/images/iphone-15-pro-black-2.jpg'],
      },
      isActive: true,
      isPopular: true,
    },
    {
      id: 3,
      brand: 'Google',
      model: 'Pixel 8 Pro',
      colors: ['Obsidian', 'Porcelain', 'Bay'],
      price: 1199000,
      originalPrice: 1299000,
      discount: 8,
      stockQuantity: 0,
      specifications: {
        display: '6.7인치 LTPO OLED',
        camera: '50MP + 48MP + 48MP',
        battery: '5050mAh',
        storage: '128GB',
        ram: '12GB',
        os: 'Android 14'
      },
      images: {
        'Obsidian': ['/images/pixel-8-pro-obsidian-1.jpg', '/images/pixel-8-pro-obsidian-2.jpg'],
        'Porcelain': ['/images/pixel-8-pro-porcelain-1.jpg', '/images/pixel-8-pro-porcelain-2.jpg'],
        'Bay': ['/images/pixel-8-pro-bay-1.jpg', '/images/pixel-8-pro-bay-2.jpg'],
      },
      isActive: true,
    },
  ];

  useEffect(() => {
    // 실제로는 dispatch(fetchDevices()) 사용
    // 여기서는 모의 데이터 사용
  }, [dispatch]);

  useEffect(() => {
    if (error) {
      showError(error);
    }
  }, [error, showError]);

  const handleBrandFilter = (brand: string) => {
    dispatch(filterByBrand(brand));
  };

  const handleDeviceSelect = (device: Device) => {
    if (device.stockQuantity === 0) {
      showError('품절된 상품입니다. 다른 모델을 선택해주세요.');
      return;
    }
    
    setSelectedDevice(device);
    setSelectedColor(device.colors[0]);
    setCurrentImageIndex(0);
    setShowDetailModal(true);
  };

  const handleColorSelect = (color: string) => {
    setSelectedColor(color);
    setCurrentImageIndex(0);
  };

  const handleImageNavigation = (direction: 'prev' | 'next') => {
    if (!selectedDevice || !selectedColor) return;
    
    const images = selectedDevice.images[selectedColor] || [];
    if (direction === 'prev') {
      setCurrentImageIndex(prev => prev > 0 ? prev - 1 : images.length - 1);
    } else {
      setCurrentImageIndex(prev => prev < images.length - 1 ? prev + 1 : 0);
    }
  };

  const handleProceedToDelivery = () => {
    if (!selectedDevice || !selectedColor) {
      showError('단말기와 색상을 선택해주세요.');
      return;
    }
    
    setShowDetailModal(false);
    setShowDeliveryModal(true);
  };

  const handleDeliveryInfoChange = (field: string, value: string) => {
    if (field.startsWith('address.')) {
      const addressField = field.split('.')[1];
      setDeliveryInfo(prev => ({
        ...prev,
        address: {
          ...prev.address,
          [addressField]: value,
        },
      }));
    } else {
      setDeliveryInfo(prev => ({
        ...prev,
        [field]: value,
      }));
    }
  };

  const validateDeliveryInfo = () => {
    const { address, receiverName, receiverPhone, deliveryTime } = deliveryInfo;
    
    if (!address.zipCode || !address.address1) {
      showError('배송 주소를 입력해주세요.');
      return false;
    }
    
    if (!receiverName.trim()) {
      showError('수령인 이름을 입력해주세요.');
      return false;
    }
    
    if (!receiverPhone.trim()) {
      showError('수령인 연락처를 입력해주세요.');
      return false;
    }
    
    if (!deliveryTime) {
      showError('희망 배송 시간을 선택해주세요.');
      return false;
    }
    
    return true;
  };

  const handleConfirmSelection = () => {
    if (!validateDeliveryInfo()) return;
    
    // Redux store에 선택된 단말기와 배송 정보 저장
    showSuccess(`${selectedDevice?.model} (${selectedColor})이(가) 선택되었습니다.`);
    navigate('/numbers');
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR').format(price);
  };

  const getSortedDevices = () => {
    const devices = [...mockDevices];
    switch (sortBy) {
      case 'price-low':
        return devices.sort((a, b) => a.price - b.price);
      case 'price-high':
        return devices.sort((a, b) => b.price - a.price);
      case 'brand':
        return devices.sort((a, b) => a.brand.localeCompare(b.brand));
      case 'popular':
      default:
        return devices.sort((a, b) => (b.isPopular ? 1 : 0) - (a.isPopular ? 1 : 0));
    }
  };

  const getFilteredDevices = () => {
    const sorted = getSortedDevices();
    if (selectedBrand === 'all') return sorted;
    return sorted.filter(device => device.brand === selectedBrand);
  };

  if (loading) {
    return (
      <div className="device-selection-page">
        <div className="loading-container">
          <LoadingSpinner size="large" />
          <p>단말기 정보를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="device-selection-page">
      {/* 진행률 표시 */}
      <div className="progress-section">
        <ProgressBar current={3} total={5} />
        <p className="progress-text">3단계: 단말기 선택</p>
      </div>

      {/* 페이지 헤더 */}
      <div className="page-header">
        <h1 className="page-title">단말기 선택</h1>
        <p className="page-description">
          원하는 스마트폰을 선택하고 배송 정보를 입력해주세요
        </p>
      </div>

      {/* 브랜드 필터 */}
      <div className="brand-filter">
        <div className="brand-tabs">
          {brands.map(brand => (
            <button
              key={brand.id}
              className={`brand-tab ${selectedBrand === brand.id ? 'active' : ''}`}
              onClick={() => handleBrandFilter(brand.id)}
            >
              <span className="brand-icon">{brand.icon}</span>
              <span className="brand-name">{brand.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* 정렬 옵션 */}
      <div className="filter-controls">
        <div className="sort-options">
          <label htmlFor="sort-select">정렬:</label>
          <select
            id="sort-select"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="sort-select"
          >
            <option value="popular">인기순</option>
            <option value="price-low">가격 낮은순</option>
            <option value="price-high">가격 높은순</option>
            <option value="brand">브랜드순</option>
          </select>
        </div>
      </div>

      {/* 단말기 목록 */}
      <div className="devices-grid">
        {getFilteredDevices().map(device => (
          <div key={device.id} className="device-card">
            {device.isPopular && (
              <div className="device-badge popular">인기</div>
            )}
            {device.discount && (
              <div className="device-badge discount">{device.discount}% 할인</div>
            )}
            {device.stockQuantity === 0 && (
              <div className="device-badge sold-out">품절</div>
            )}
            
            <div className="device-image">
              <img
                src={device.images[device.colors[0]]?.[0] || '/images/device-placeholder.jpg'}
                alt={device.model}
                onError={(e) => {
                  (e.target as HTMLImageElement).src = '/images/device-placeholder.jpg';
                }}
              />
            </div>

            <div className="device-info">
              <div className="device-brand">{device.brand}</div>
              <h3 className="device-model">{device.model}</h3>
              
              <div className="device-specs">
                <div className="spec-item">
                  <span className="spec-label">디스플레이:</span>
                  <span className="spec-value">{device.specifications.display}</span>
                </div>
                <div className="spec-item">
                  <span className="spec-label">저장용량:</span>
                  <span className="spec-value">{device.specifications.storage}</span>
                </div>
              </div>

              <div className="device-colors">
                <span className="colors-label">색상:</span>
                <div className="color-options">
                  {device.colors.slice(0, 4).map(color => (
                    <div
                      key={color}
                      className="color-option"
                      title={color}
                      style={{
                        backgroundColor: getColorCode(color)
                      }}
                    />
                  ))}
                  {device.colors.length > 4 && (
                    <span className="more-colors">+{device.colors.length - 4}</span>
                  )}
                </div>
              </div>

              <div className="device-price">
                {device.originalPrice && (
                  <span className="original-price">
                    {formatPrice(device.originalPrice)}원
                  </span>
                )}
                <span className="current-price">
                  {formatPrice(device.price)}원
                </span>
              </div>

              <div className="device-stock">
                {device.stockQuantity > 0 ? (
                  <span className="in-stock">재고 {device.stockQuantity}대</span>
                ) : (
                  <span className="out-of-stock">품절</span>
                )}
              </div>
            </div>

            <div className="device-actions">
              <Button
                variant="primary"
                fullWidth
                onClick={() => handleDeviceSelect(device)}
                disabled={device.stockQuantity === 0}
                className="select-button"
              >
                {device.stockQuantity === 0 ? '품절' : '선택하기'}
              </Button>
            </div>
          </div>
        ))}
      </div>

      {getFilteredDevices().length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📱</div>
          <h3>해당 브랜드의 단말기가 없습니다</h3>
          <p>다른 브랜드를 선택해보세요</p>
        </div>
      )}

      {/* 단말기 상세 모달 */}
      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title={selectedDevice?.model || ''}
        size="large"
      >
        {selectedDevice && (
          <div className="device-detail-modal">
            <div className="detail-content">
              <div className="detail-images">
                <div className="main-image">
                  <img
                    src={selectedDevice.images[selectedColor]?.[currentImageIndex] || '/images/device-placeholder.jpg'}
                    alt={`${selectedDevice.model} ${selectedColor}`}
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = '/images/device-placeholder.jpg';
                    }}
                  />
                  <div className="image-navigation">
                    <button
                      className="nav-button prev"
                      onClick={() => handleImageNavigation('prev')}
                    >
                      ‹
                    </button>
                    <button
                      className="nav-button next"
                      onClick={() => handleImageNavigation('next')}
                    >
                      ›
                    </button>
                  </div>
                </div>
                
                <div className="image-thumbnails">
                  {selectedDevice.images[selectedColor]?.map((image, index) => (
                    <img
                      key={index}
                      src={image}
                      alt={`${selectedDevice.model} ${selectedColor} ${index + 1}`}
                      className={`thumbnail ${index === currentImageIndex ? 'active' : ''}`}
                      onClick={() => setCurrentImageIndex(index)}
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = '/images/device-placeholder.jpg';
                      }}
                    />
                  ))}
                </div>
              </div>

              <div className="detail-info">
                <div className="detail-header">
                  <h3>{selectedDevice.brand} {selectedDevice.model}</h3>
                  <div className="detail-price">
                    {selectedDevice.originalPrice && (
                      <span className="original-price">
                        {formatPrice(selectedDevice.originalPrice)}원
                      </span>
                    )}
                    <span className="current-price">
                      {formatPrice(selectedDevice.price)}원
                    </span>
                  </div>
                </div>

                <div className="color-selection">
                  <h4>색상 선택</h4>
                  <div className="color-options">
                    {selectedDevice.colors.map(color => (
                      <button
                        key={color}
                        className={`color-option ${selectedColor === color ? 'selected' : ''}`}
                        onClick={() => handleColorSelect(color)}
                      >
                        <div
                          className="color-swatch"
                          style={{ backgroundColor: getColorCode(color) }}
                        />
                        <span className="color-name">{color}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="specifications">
                  <h4>주요 사양</h4>
                  <div className="spec-list">
                    <div className="spec-row">
                      <span className="spec-label">디스플레이</span>
                      <span className="spec-value">{selectedDevice.specifications.display}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-label">카메라</span>
                      <span className="spec-value">{selectedDevice.specifications.camera}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-label">배터리</span>
                      <span className="spec-value">{selectedDevice.specifications.battery}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-label">저장용량</span>
                      <span className="spec-value">{selectedDevice.specifications.storage}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-label">RAM</span>
                      <span className="spec-value">{selectedDevice.specifications.ram}</span>
                    </div>
                    <div className="spec-row">
                      <span className="spec-label">운영체제</span>
                      <span className="spec-value">{selectedDevice.specifications.os}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="detail-actions">
              <Button
                variant="outline"
                onClick={() => setShowDetailModal(false)}
              >
                취소
              </Button>
              <Button
                variant="primary"
                onClick={handleProceedToDelivery}
              >
                배송 정보 입력
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* 배송 정보 모달 */}
      <Modal
        isOpen={showDeliveryModal}
        onClose={() => setShowDeliveryModal(false)}
        title="배송 정보 입력"
        size="medium"
      >
        <div className="delivery-modal">
          <div className="selected-device-summary">
            <h4>선택된 단말기</h4>
            <div className="device-summary">
              <span className="device-name">
                {selectedDevice?.brand} {selectedDevice?.model}
              </span>
              <span className="device-color">색상: {selectedColor}</span>
              <span className="device-price">
                {selectedDevice && formatPrice(selectedDevice.price)}원
              </span>
            </div>
          </div>

          <form className="delivery-form">
            <div className="form-section">
              <h4>수령인 정보</h4>
              <div className="form-group">
                <label className="form-label">수령인 이름 *</label>
                <input
                  type="text"
                  className="form-input"
                  value={deliveryInfo.receiverName}
                  onChange={(e) => handleDeliveryInfoChange('receiverName', e.target.value)}
                  placeholder="수령인 이름을 입력하세요"
                />
              </div>
              <div className="form-group">
                <label className="form-label">연락처 *</label>
                <input
                  type="tel"
                  className="form-input"
                  value={deliveryInfo.receiverPhone}
                  onChange={(e) => handleDeliveryInfoChange('receiverPhone', e.target.value)}
                  placeholder="010-0000-0000"
                />
              </div>
            </div>

            <div className="form-section">
              <h4>배송 주소</h4>
              <div className="form-group">
                <div className="address-input-group">
                  <input
                    type="text"
                    className="form-input"
                    value={deliveryInfo.address.zipCode}
                    placeholder="우편번호"
                    readOnly
                  />
                  <Button variant="outline" size="small">
                    주소 검색
                  </Button>
                </div>
              </div>
              <div className="form-group">
                <input
                  type="text"
                  className="form-input"
                  value={deliveryInfo.address.address1}
                  placeholder="기본 주소"
                  readOnly
                />
              </div>
              <div className="form-group">
                <input
                  type="text"
                  className="form-input"
                  value={deliveryInfo.address.address2}
                  onChange={(e) => handleDeliveryInfoChange('address.address2', e.target.value)}
                  placeholder="상세 주소를 입력하세요"
                />
              </div>
            </div>

            <div className="form-section">
              <h4>배송 옵션</h4>
              <div className="form-group">
                <label className="form-label">희망 배송 시간 *</label>
                <div className="delivery-time-options">
                  {deliveryTimes.map(time => (
                    <label key={time.value} className="radio-option">
                      <input
                        type="radio"
                        name="deliveryTime"
                        value={time.value}
                        checked={deliveryInfo.deliveryTime === time.value}
                        onChange={(e) => handleDeliveryInfoChange('deliveryTime', e.target.value)}
                      />
                      <span className="radio-text">{time.label}</span>
                    </label>
                  ))}
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">배송 요청사항</label>
                <textarea
                  className="form-textarea"
                  value={deliveryInfo.deliveryNote}
                  onChange={(e) => handleDeliveryInfoChange('deliveryNote', e.target.value)}
                  placeholder="배송 시 요청사항이 있으시면 입력해주세요"
                  rows={3}
                />
              </div>
            </div>
          </form>

          <div className="delivery-actions">
            <Button
              variant="outline"
              onClick={() => setShowDeliveryModal(false)}
            >
              이전
            </Button>
            <Button
              variant="primary"
              onClick={handleConfirmSelection}
            >
              선택 완료
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
};

// 색상 이름을 CSS 색상 코드로 변환하는 헬퍼 함수
const getColorCode = (colorName: string): string => {
  const colorMap: { [key: string]: string } = {
    'Titanium Black': '#2c2c2c',
    'Titanium Gray': '#8c8c8c',
    'Titanium Violet': '#8b5cf6',
    'Titanium Yellow': '#fbbf24',
    'Natural Titanium': '#d4af8c',
    'Blue Titanium': '#3b82f6',
    'White Titanium': '#f8fafc',
    'Black Titanium': '#1e293b',
    'Obsidian': '#1f2937',
    'Porcelain': '#f8fafc',
    'Bay': '#0ea5e9',
  };
  
  return colorMap[colorName] || '#6b7280';
};

export default DeviceSelectionPage;