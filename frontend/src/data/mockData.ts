// 데모 모드용 목업 데이터
export const mockPlans = [
  {
    id: 1,
    name: "기본 요금제",
    category: "basic",
    price: 35000,
    data: "10GB",
    voice: "무제한",
    sms: "무제한",
    features: ["5G 지원", "데이터 쉐어링", "해외로밍"],
    description: "가장 인기있는 기본 요금제입니다."
  },
  {
    id: 2,
    name: "프리미엄 요금제",
    category: "premium",
    price: 55000,
    data: "무제한",
    voice: "무제한",
    sms: "무제한",
    features: ["5G 지원", "데이터 쉐어링", "해외로밍", "넷플릭스 무료", "YouTube 프리미엄"],
    description: "모든 기능이 포함된 프리미엄 요금제입니다."
  },
  {
    id: 3,
    name: "청소년 요금제",
    category: "youth",
    price: 25000,
    data: "5GB",
    voice: "무제한",
    sms: "무제한",
    features: ["5G 지원", "학습 앱 무료", "자녀 안심 서비스"],
    description: "청소년을 위한 특별 요금제입니다."
  }
];

export const mockDevices = [
  {
    id: 1,
    brand: "Samsung",
    model: "Galaxy S24",
    price: 1200000,
    color: ["미드나이트 블랙", "크림", "바이올렛"],
    storage: ["256GB", "512GB"],
    image: "/images/galaxy-s24.jpg",
    features: ["6.2인치 Dynamic AMOLED", "50MP 트리플 카메라", "4000mAh 배터리"]
  },
  {
    id: 2,
    brand: "Apple",
    model: "iPhone 15",
    price: 1350000,
    color: ["블랙", "블루", "그린", "옐로우", "핑크"],
    storage: ["128GB", "256GB", "512GB"],
    image: "/images/iphone-15.jpg",
    features: ["6.1인치 Super Retina XDR", "48MP 메인 카메라", "USB-C 포트"]
  },
  {
    id: 3,
    brand: "Samsung",
    model: "Galaxy A54",
    price: 600000,
    color: ["어썸 바이올렛", "어썸 화이트", "어썸 그래파이트"],
    storage: ["128GB", "256GB"],
    image: "/images/galaxy-a54.jpg",
    features: ["6.4인치 Super AMOLED", "50MP 트리플 카메라", "5000mAh 배터리"]
  }
];

export const mockNumbers = [
  {
    id: 1,
    number: "010-1234-5678",
    type: "일반",
    price: 0,
    available: true,
    reserved: false
  },
  {
    id: 2,
    number: "010-7777-8888",
    type: "프리미엄",
    price: 50000,
    available: true,
    reserved: false
  },
  {
    id: 3,
    number: "010-1111-2222",
    type: "프리미엄",
    price: 100000,
    available: true,
    reserved: false
  },
  {
    id: 4,
    number: "010-9999-0000",
    type: "골드",
    price: 200000,
    available: true,
    reserved: false
  },
  {
    id: 5,
    number: "010-5555-6666",
    type: "일반",
    price: 0,
    available: true,
    reserved: false
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