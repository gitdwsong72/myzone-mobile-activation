// 데모 모드용 목업 데이터
export const mockPlans = [
  {
    id: 1,
    name: "5G 베이직",
    description: "가장 인기있는 기본 요금제입니다",
    monthlyFee: 35000,
    dataLimit: "10",
    callMinutes: -1, // -1은 무제한
    smsCount: -1,
    category: "5G",
    isActive: true,
    originalPrice: 40000,
    discount: 12,
    features: ["5G 지원", "데이터 쉐어링", "해외로밍"],
    terms: "약정 기간: 24개월, 중도 해지 시 위약금 발생",
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 2,
    name: "5G 프리미엄",
    description: "모든 기능이 포함된 프리미엄 요금제입니다",
    monthlyFee: 55000,
    dataLimit: "unlimited",
    callMinutes: -1,
    smsCount: -1,
    category: "5G",
    isActive: true,
    originalPrice: 65000,
    discount: 15,
    features: ["5G 지원", "데이터 쉐어링", "해외로밍", "넷플릭스 무료", "YouTube 프리미엄"],
    terms: "약정 기간: 24개월, 중도 해지 시 위약금 발생",
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 3,
    name: "청소년 스페셜",
    description: "청소년을 위한 특별 요금제입니다",
    monthlyFee: 25000,
    dataLimit: "5",
    callMinutes: -1,
    smsCount: -1,
    category: "data",
    isActive: true,
    originalPrice: 30000,
    discount: 17,
    features: ["5G 지원", "학습 앱 무료", "자녀 안심 서비스"],
    terms: "만 19세 미만 가입 가능, 부모 동의 필요",
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 4,
    name: "LTE 라이트",
    description: "경제적인 LTE 요금제입니다",
    monthlyFee: 20000,
    dataLimit: "3",
    callMinutes: 300,
    smsCount: 100,
    category: "LTE",
    isActive: true,
    features: ["LTE 지원", "기본 통화/문자"],
    terms: "약정 기간: 12개월",
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 5,
    name: "통화 중심",
    description: "통화를 많이 하시는 분을 위한 요금제입니다",
    monthlyFee: 30000,
    dataLimit: "5",
    callMinutes: -1,
    smsCount: -1,
    category: "call",
    isActive: true,
    features: ["무제한 통화", "기본 데이터", "국제전화 할인"],
    terms: "약정 기간: 24개월",
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 6,
    name: "가족 쉐어링",
    description: "가족이 함께 사용하는 요금제입니다",
    monthlyFee: 89000,
    dataLimit: "50",
    callMinutes: -1,
    smsCount: -1,
    category: "family",
    isActive: true,
    originalPrice: 120000,
    discount: 26,
    features: ["4인 가족 공유", "데이터 쉐어링", "가족 할인", "부가서비스 무료"],
    terms: "최대 4회선까지 가능, 주 회선 기준 약정",
    createdAt: "2024-01-01T00:00:00Z"
  }
];

export const mockDevices = [
  {
    id: 1,
    brand: "Samsung",
    model: "Galaxy S24",
    name: "갤럭시 S24",
    price: 1200000,
    originalPrice: 1400000,
    discount: 14,
    colors: [
      { name: "미드나이트 블랙", code: "#1a1a1a" },
      { name: "크림", code: "#f5f5dc" },
      { name: "바이올렛", code: "#8a2be2" }
    ],
    storageOptions: [
      { size: "256GB", price: 0 },
      { size: "512GB", price: 200000 }
    ],
    image: "/images/galaxy-s24.jpg",
    images: [
      "/images/galaxy-s24-1.jpg",
      "/images/galaxy-s24-2.jpg",
      "/images/galaxy-s24-3.jpg"
    ],
    features: ["6.2인치 Dynamic AMOLED", "50MP 트리플 카메라", "4000mAh 배터리", "5G 지원"],
    specifications: {
      display: "6.2인치 Dynamic AMOLED 2X",
      processor: "Snapdragon 8 Gen 3",
      camera: "50MP + 12MP + 10MP",
      battery: "4000mAh",
      os: "Android 14"
    },
    category: "flagship",
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 2,
    brand: "Apple",
    model: "iPhone 15",
    name: "아이폰 15",
    price: 1350000,
    originalPrice: 1550000,
    discount: 13,
    colors: [
      { name: "블랙", code: "#000000" },
      { name: "블루", code: "#007aff" },
      { name: "그린", code: "#34c759" },
      { name: "옐로우", code: "#ffcc00" },
      { name: "핑크", code: "#ff2d92" }
    ],
    storageOptions: [
      { size: "128GB", price: 0 },
      { size: "256GB", price: 150000 },
      { size: "512GB", price: 400000 }
    ],
    image: "/images/iphone-15.jpg",
    images: [
      "/images/iphone-15-1.jpg",
      "/images/iphone-15-2.jpg",
      "/images/iphone-15-3.jpg"
    ],
    features: ["6.1인치 Super Retina XDR", "48MP 메인 카메라", "USB-C 포트", "Dynamic Island"],
    specifications: {
      display: "6.1인치 Super Retina XDR",
      processor: "A16 Bionic",
      camera: "48MP + 12MP",
      battery: "최대 20시간 비디오 재생",
      os: "iOS 17"
    },
    category: "flagship",
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 3,
    brand: "Samsung",
    model: "Galaxy A54",
    name: "갤럭시 A54",
    price: 600000,
    originalPrice: 700000,
    discount: 14,
    colors: [
      { name: "어썸 바이올렛", code: "#8a2be2" },
      { name: "어썸 화이트", code: "#ffffff" },
      { name: "어썸 그래파이트", code: "#2f2f2f" }
    ],
    storageOptions: [
      { size: "128GB", price: 0 },
      { size: "256GB", price: 100000 }
    ],
    image: "/images/galaxy-a54.jpg",
    images: [
      "/images/galaxy-a54-1.jpg",
      "/images/galaxy-a54-2.jpg"
    ],
    features: ["6.4인치 Super AMOLED", "50MP 트리플 카메라", "5000mAh 배터리", "IP67 방수"],
    specifications: {
      display: "6.4인치 Super AMOLED",
      processor: "Exynos 1380",
      camera: "50MP + 12MP + 5MP",
      battery: "5000mAh",
      os: "Android 13"
    },
    category: "mid-range",
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 4,
    brand: "Apple",
    model: "iPhone SE",
    name: "아이폰 SE",
    price: 650000,
    colors: [
      { name: "미드나이트", code: "#1a1a1a" },
      { name: "스타라이트", code: "#f5f5dc" },
      { name: "레드", code: "#ff3b30" }
    ],
    storageOptions: [
      { size: "64GB", price: 0 },
      { size: "128GB", price: 50000 },
      { size: "256GB", price: 150000 }
    ],
    image: "/images/iphone-se.jpg",
    features: ["4.7인치 Retina HD", "12MP 카메라", "Touch ID", "A15 Bionic"],
    specifications: {
      display: "4.7인치 Retina HD",
      processor: "A15 Bionic",
      camera: "12MP",
      battery: "최대 15시간 비디오 재생",
      os: "iOS 17"
    },
    category: "budget",
    isActive: true,
    createdAt: "2024-01-01T00:00:00Z"
  }
];

export const mockNumbers = [
  {
    id: 1,
    number: "010-1234-5678",
    displayNumber: "010-1234-5678",
    type: "일반",
    category: "normal",
    price: 0,
    monthlyFee: 0,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["일반 번호"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 2,
    number: "010-7777-8888",
    displayNumber: "010-7777-8888",
    type: "프리미엄",
    category: "premium",
    price: 50000,
    monthlyFee: 5000,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["연속 번호", "기억하기 쉬운 번호"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 3,
    number: "010-1111-2222",
    displayNumber: "010-1111-2222",
    type: "프리미엄",
    category: "premium",
    price: 100000,
    monthlyFee: 10000,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["연속 번호", "기억하기 쉬운 번호"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 4,
    number: "010-9999-0000",
    displayNumber: "010-9999-0000",
    type: "골드",
    category: "gold",
    price: 200000,
    monthlyFee: 20000,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["특급 번호", "VIP 서비스", "우선 고객지원"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 5,
    number: "010-5555-6666",
    displayNumber: "010-5555-6666",
    type: "프리미엄",
    category: "premium",
    price: 80000,
    monthlyFee: 8000,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["연속 번호", "기억하기 쉬운 번호"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 6,
    number: "010-3456-7890",
    displayNumber: "010-3456-7890",
    type: "일반",
    category: "normal",
    price: 0,
    monthlyFee: 0,
    available: true,
    reserved: false,
    region: "경기",
    carrier: "MyZone",
    features: ["일반 번호"],
    createdAt: "2024-01-01T00:00:00Z"
  },
  {
    id: 7,
    number: "010-8888-9999",
    displayNumber: "010-8888-9999",
    type: "골드",
    category: "gold",
    price: 300000,
    monthlyFee: 30000,
    available: true,
    reserved: false,
    region: "서울",
    carrier: "MyZone",
    features: ["특급 번호", "VIP 서비스", "우선 고객지원", "전용 상담사"],
    createdAt: "2024-01-01T00:00:00Z"
  }
];

export const mockUser = {
  id: 1,
  name: "홍길동",
  email: "demo@myzone.com",
  phone: "010-1234-5678",
  birthDate: "1990-01-01",
  gender: "M",
  address: "서울특별시 강남구 테헤란로 123",
  verified: true
};

export const mockOrder = {
  id: 1,
  orderNumber: "MZ20241227001",
  status: "processing",
  user: mockUser,
  plan: mockPlans[0],
  device: mockDevices[0],
  number: mockNumbers[0],
  totalAmount: 1235000,
  createdAt: new Date().toISOString(),
  estimatedActivation: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
};

export const mockPayment = {
  id: 1,
  orderId: 1,
  amount: 1235000,
  method: "card",
  status: "completed",
  transactionId: "TXN20241227001",
  createdAt: new Date().toISOString()
};

// API 응답 시뮬레이션을 위한 지연 함수
export const simulateApiDelay = (ms: number = 1000): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// 랜덤 에러 시뮬레이션 (10% 확률)
export const shouldSimulateError = (): boolean => {
  return Math.random() < 0.1;
};