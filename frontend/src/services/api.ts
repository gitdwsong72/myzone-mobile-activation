import axios from 'axios';

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
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/login', credentials),
  logout: () => api.post('/auth/logout'),
  getProfile: () => api.get('/auth/me'),
  refreshToken: () => api.post('/auth/refresh'),
};

export const planAPI = {
  getAll: () => api.get('/plans'),
  getById: (id: number) => api.get(`/plans/${id}`),
  getByCategory: (category: string) => api.get(`/plans?category=${category}`),
};

export const deviceAPI = {
  getAll: () => api.get('/devices'),
  getById: (id: number) => api.get(`/devices/${id}`),
  getByBrand: (brand: string) => api.get(`/devices?brand=${brand}`),
};

export const numberAPI = {
  getAll: () => api.get('/numbers'),
  search: (pattern: string) => api.get(`/numbers/search?pattern=${pattern}`),
  reserve: (id: number) => api.post(`/numbers/${id}/reserve`),
  release: (id: number) => api.delete(`/numbers/${id}/reserve`),
};

export const orderAPI = {
  create: (orderData: any) => api.post('/orders', orderData),
  getById: (id: number) => api.get(`/orders/${id}`),
  getByOrderNumber: (orderNumber: string) => api.get(`/orders/number/${orderNumber}`),
  updateStatus: (id: number, status: string) => api.patch(`/orders/${id}/status`, { status }),
};

export const paymentAPI = {
  create: (paymentData: any) => api.post('/payments', paymentData),
  getById: (id: number) => api.get(`/payments/${id}`),
  verify: (transactionId: string) => api.post(`/payments/verify`, { transactionId }),
};

export const userAPI = {
  create: (userData: any) => api.post('/users', userData),
  getById: (id: number) => api.get(`/users/${id}`),
  update: (id: number, userData: any) => api.patch(`/users/${id}`, userData),
  verify: (verificationData: any) => api.post('/users/verify', verificationData),
};

export const adminAPI = {
  getOrders: (params?: any) => api.get('/admin/orders', { params }),
  getOrderById: (id: number) => api.get(`/admin/orders/${id}`),
  updateOrderStatus: (id: number, status: string, note?: string) =>
    api.patch(`/admin/orders/${id}/status`, { status, note }),
  getStatistics: (params?: any) => api.get('/admin/statistics', { params }),
};

export default api;