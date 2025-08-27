import axios from 'axios';
import { demoService, withDemoFallback } from './demoService';

// API 기본 설정
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 인증 토큰 자동 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 에러 처리
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 토큰 만료 시 로그아웃 처리
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API 서비스 함수들
export const authAPI = {
  login: (credentials: { email: string; password: string }) => withDemoFallback(
    () => api.post('/auth/login', credentials).then(res => res.data),
    () => demoService.login(credentials),
    '로그인을 데모 모드로 처리합니다'
  ),
  logout: () => withDemoFallback(
    () => api.post('/auth/logout').then(res => res.data),
    () => Promise.resolve({ success: true, message: '로그아웃되었습니다 (데모)' }),
    '로그아웃을 데모 모드로 처리합니다'
  ),
  getProfile: () => withDemoFallback(
    () => api.get('/auth/me').then(res => res.data),
    () => demoService.getProfile(),
    '프로필 정보를 데모 데이터로 표시합니다'
  ),
  refreshToken: () => withDemoFallback(
    () => api.post('/auth/refresh').then(res => res.data),
    () => Promise.resolve({ access_token: 'demo_refreshed_token' }),
    '토큰 갱신을 데모 모드로 처리합니다'
  ),
};

export const planAPI = {
  getAll: () => withDemoFallback(
    () => api.get('/plans').then(res => res.data),
    () => demoService.getPlans(),
    '요금제 정보를 데모 데이터로 표시합니다'
  ),
  getById: (id: number) => withDemoFallback(
    () => api.get(`/plans/${id}`).then(res => res.data),
    () => demoService.getPlanById(id),
    '요금제 상세 정보를 데모 데이터로 표시합니다'
  ),
  getByCategory: (category: string) => withDemoFallback(
    () => api.get(`/plans?category=${category}`).then(res => res.data),
    () => demoService.getPlans().then(plans => plans.filter(p => p.category === category)),
    '카테고리별 요금제를 데모 데이터로 표시합니다'
  ),
};

export const deviceAPI = {
  getAll: () => withDemoFallback(
    () => api.get('/devices').then(res => res.data),
    () => demoService.getDevices(),
    '기기 정보를 데모 데이터로 표시합니다'
  ),
  getById: (id: number) => withDemoFallback(
    () => api.get(`/devices/${id}`).then(res => res.data),
    () => demoService.getDeviceById(id),
    '기기 상세 정보를 데모 데이터로 표시합니다'
  ),
  getByBrand: (brand: string) => withDemoFallback(
    () => api.get(`/devices?brand=${brand}`).then(res => res.data),
    () => demoService.getDevices().then(devices => devices.filter(d => d.brand === brand)),
    '브랜드별 기기를 데모 데이터로 표시합니다'
  ),
};

export const numberAPI = {
  getAll: () => withDemoFallback(
    () => api.get('/numbers').then(res => res.data),
    () => demoService.getNumbers(),
    '번호 정보를 데모 데이터로 표시합니다'
  ),
  search: (pattern: string) => withDemoFallback(
    () => api.get(`/numbers/search?pattern=${pattern}`).then(res => res.data),
    () => demoService.searchNumbers(pattern),
    '번호 검색 결과를 데모 데이터로 표시합니다'
  ),
  reserve: (id: number) => withDemoFallback(
    () => api.post(`/numbers/${id}/reserve`).then(res => res.data),
    () => demoService.reserveNumber(id),
    '번호 예약을 데모 모드로 처리합니다'
  ),
  release: (id: number) => withDemoFallback(
    () => api.delete(`/numbers/${id}/reserve`).then(res => res.data),
    () => Promise.resolve({ success: true, message: '번호 예약이 해제되었습니다 (데모)' }),
    '번호 예약 해제를 데모 모드로 처리합니다'
  ),
};

export const orderAPI = {
  create: (orderData: any) => withDemoFallback(
    () => api.post('/orders', orderData).then(res => res.data),
    () => demoService.createOrder(orderData),
    '주문을 데모 모드로 생성합니다'
  ),
  getById: (id: number) => withDemoFallback(
    () => api.get(`/orders/${id}`).then(res => res.data),
    () => demoService.getOrderById(id),
    '주문 정보를 데모 데이터로 표시합니다'
  ),
  getByOrderNumber: (orderNumber: string) => withDemoFallback(
    () => api.get(`/orders/number/${orderNumber}`).then(res => res.data),
    () => demoService.getOrderByNumber(orderNumber),
    '주문 조회를 데모 데이터로 표시합니다'
  ),
  updateStatus: (id: number, status: string) => withDemoFallback(
    () => api.patch(`/orders/${id}/status`, { status }).then(res => res.data),
    () => Promise.resolve({ success: true, message: '주문 상태가 업데이트되었습니다 (데모)' }),
    '주문 상태 업데이트를 데모 모드로 처리합니다'
  ),
};

export const paymentAPI = {
  create: (paymentData: any) => withDemoFallback(
    () => api.post('/payments', paymentData).then(res => res.data),
    () => demoService.createPayment(paymentData),
    '결제를 데모 모드로 처리합니다'
  ),
  getById: (id: number) => withDemoFallback(
    () => api.get(`/payments/${id}`).then(res => res.data),
    () => Promise.resolve({ id, status: 'completed', message: '결제 완료 (데모)' }),
    '결제 정보를 데모 데이터로 표시합니다'
  ),
  verify: (transactionId: string) => withDemoFallback(
    () => api.post(`/payments/verify`, { transactionId }).then(res => res.data),
    () => demoService.verifyPayment(transactionId),
    '결제 검증을 데모 모드로 처리합니다'
  ),
};

export const userAPI = {
  create: (userData: any) => withDemoFallback(
    () => api.post('/users', userData).then(res => res.data),
    () => demoService.createUser(userData),
    '사용자 생성을 데모 모드로 처리합니다'
  ),
  getById: (id: number) => withDemoFallback(
    () => api.get(`/users/${id}`).then(res => res.data),
    () => Promise.resolve({ id, name: '데모 사용자', email: 'demo@myzone.com' }),
    '사용자 정보를 데모 데이터로 표시합니다'
  ),
  update: (id: number, userData: any) => withDemoFallback(
    () => api.patch(`/users/${id}`, userData).then(res => res.data),
    () => Promise.resolve({ ...userData, id, message: '사용자 정보가 업데이트되었습니다 (데모)' }),
    '사용자 정보 업데이트를 데모 모드로 처리합니다'
  ),
  verify: (verificationData: any) => withDemoFallback(
    () => api.post('/users/verify', verificationData).then(res => res.data),
    () => demoService.verifyUser(verificationData),
    '사용자 인증을 데모 모드로 처리합니다'
  ),
};

export const adminAPI = {
  getOrders: (params?: any) => api.get('/admin/orders', { params }),
  getOrderById: (id: number) => api.get(`/admin/orders/${id}`),
  updateOrderStatus: (id: number, status: string, note?: string) =>
    api.patch(`/admin/orders/${id}/status`, { status, note }),
  getStatistics: (params?: any) => api.get('/admin/statistics', { params }),
};

export default api;