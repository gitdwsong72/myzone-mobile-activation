import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import {
  login,
  logout,
  refreshToken,
  getPlans,
  getPlanById,
  getDevices,
  getDeviceById,
  getNumbers,
  createOrder,
  getOrderByNumber,
  processPayment,
  getUserInfo,
  updateUserInfo
} from '../api';
import { mockUser, mockPlan, mockDevice, mockNumber, mockOrder } from '../../test-utils';

describe('API Service', () => {
  let mock: MockAdapter;

  beforeEach(() => {
    mock = new MockAdapter(axios);
    // localStorage mock 초기화
    localStorage.clear();
  });

  afterEach(() => {
    mock.restore();
  });

  describe('Authentication API', () => {
    test('login API가 올바르게 작동한다', async () => {
      const loginData = {
        username: 'admin',
        password: 'password123'
      };

      const responseData = {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'bearer',
        user: mockUser
      };

      mock.onPost('/api/v1/auth/login').reply(200, responseData);

      const result = await login(loginData.username, loginData.password);

      expect(result).toEqual(responseData);
      expect(mock.history.post[0].data).toBe(JSON.stringify(loginData));
    });

    test('login API 실패 시 에러를 던진다', async () => {
      mock.onPost('/api/v1/auth/login').reply(401, {
        error_code: 'INVALID_CREDENTIALS',
        message: '잘못된 인증 정보입니다.'
      });

      await expect(login('admin', 'wrong-password')).rejects.toThrow();
    });

    test('logout API가 올바르게 작동한다', async () => {
      localStorage.setItem('token', 'mock-token');
      mock.onPost('/api/v1/auth/logout').reply(200, {
        message: 'Successfully logged out'
      });

      const result = await logout();

      expect(result.message).toBe('Successfully logged out');
      expect(mock.history.post[0].headers?.Authorization).toBe('Bearer mock-token');
    });

    test('refreshToken API가 올바르게 작동한다', async () => {
      const refreshTokenValue = 'mock-refresh-token';
      const responseData = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer'
      };

      mock.onPost('/api/v1/auth/refresh').reply(200, responseData);

      const result = await refreshToken(refreshTokenValue);

      expect(result).toEqual(responseData);
      expect(JSON.parse(mock.history.post[0].data)).toEqual({
        refresh_token: refreshTokenValue
      });
    });
  });

  describe('Plans API', () => {
    test('getPlans API가 올바르게 작동한다', async () => {
      const mockPlans = [mockPlan];
      mock.onGet('/api/v1/plans/').reply(200, mockPlans);

      const result = await getPlans();

      expect(result).toEqual(mockPlans);
    });

    test('getPlans API에 쿼리 파라미터가 올바르게 전달된다', async () => {
      const mockPlans = [mockPlan];
      mock.onGet('/api/v1/plans/').reply(200, mockPlans);

      await getPlans({ category: '5G', active_only: true });

      expect(mock.history.get[0].params).toEqual({
        category: '5G',
        active_only: true
      });
    });

    test('getPlanById API가 올바르게 작동한다', async () => {
      const planId = 1;
      mock.onGet(`/api/v1/plans/${planId}`).reply(200, mockPlan);

      const result = await getPlanById(planId);

      expect(result).toEqual(mockPlan);
    });

    test('getPlanById API에서 존재하지 않는 요금제 조회 시 에러를 던진다', async () => {
      const planId = 999;
      mock.onGet(`/api/v1/plans/${planId}`).reply(404, {
        error_code: 'PLAN_NOT_FOUND',
        message: '요금제를 찾을 수 없습니다.'
      });

      await expect(getPlanById(planId)).rejects.toThrow();
    });
  });

  describe('Devices API', () => {
    test('getDevices API가 올바르게 작동한다', async () => {
      const mockDevices = [mockDevice];
      mock.onGet('/api/v1/devices/').reply(200, mockDevices);

      const result = await getDevices();

      expect(result).toEqual(mockDevices);
    });

    test('getDevices API에 필터가 올바르게 적용된다', async () => {
      const mockDevices = [mockDevice];
      mock.onGet('/api/v1/devices/').reply(200, mockDevices);

      await getDevices({ brand: 'Samsung', in_stock: true });

      expect(mock.history.get[0].params).toEqual({
        brand: 'Samsung',
        in_stock: true
      });
    });

    test('getDeviceById API가 올바르게 작동한다', async () => {
      const deviceId = 1;
      mock.onGet(`/api/v1/devices/${deviceId}`).reply(200, mockDevice);

      const result = await getDeviceById(deviceId);

      expect(result).toEqual(mockDevice);
    });
  });

  describe('Numbers API', () => {
    test('getNumbers API가 올바르게 작동한다', async () => {
      const mockNumbers = [mockNumber];
      mock.onGet('/api/v1/numbers/').reply(200, mockNumbers);

      const result = await getNumbers();

      expect(result).toEqual(mockNumbers);
    });

    test('getNumbers API에 검색 조건이 올바르게 적용된다', async () => {
      const mockNumbers = [mockNumber];
      mock.onGet('/api/v1/numbers/').reply(200, mockNumbers);

      await getNumbers({ 
        category: '일반', 
        pattern: '1111',
        available_only: true 
      });

      expect(mock.history.get[0].params).toEqual({
        category: '일반',
        pattern: '1111',
        available_only: true
      });
    });
  });

  describe('Orders API', () => {
    test('createOrder API가 올바르게 작동한다', async () => {
      const orderData = {
        user_id: 1,
        plan_id: 1,
        device_id: 1,
        number_id: 1,
        delivery_address: '서울시 강남구 테헤란로 123'
      };

      mock.onPost('/api/v1/orders/').reply(201, mockOrder);

      const result = await createOrder(orderData);

      expect(result).toEqual(mockOrder);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(orderData);
    });

    test('createOrder API 실패 시 에러를 던진다', async () => {
      const orderData = {
        user_id: 1,
        plan_id: 999, // 존재하지 않는 요금제
        device_id: 1,
        number_id: 1,
        delivery_address: '서울시 강남구 테헤란로 123'
      };

      mock.onPost('/api/v1/orders/').reply(400, {
        error_code: 'PLAN_NOT_FOUND',
        message: '요금제를 찾을 수 없습니다.'
      });

      await expect(createOrder(orderData)).rejects.toThrow();
    });

    test('getOrderByNumber API가 올바르게 작동한다', async () => {
      const orderNumber = 'ORD123456789';
      mock.onGet(`/api/v1/orders/number/${orderNumber}`).reply(200, mockOrder);

      const result = await getOrderByNumber(orderNumber);

      expect(result).toEqual(mockOrder);
    });

    test('getOrderByNumber API에서 존재하지 않는 주문 조회 시 에러를 던진다', async () => {
      const orderNumber = 'INVALID_ORDER';
      mock.onGet(`/api/v1/orders/number/${orderNumber}`).reply(404, {
        error_code: 'ORDER_NOT_FOUND',
        message: '주문을 찾을 수 없습니다.'
      });

      await expect(getOrderByNumber(orderNumber)).rejects.toThrow();
    });
  });

  describe('Payment API', () => {
    test('processPayment API가 올바르게 작동한다', async () => {
      const paymentData = {
        order_id: 1,
        payment_method: 'credit_card',
        amount: 1255000,
        card_info: {
          number: '1234-5678-9012-3456',
          expiry: '12/25',
          cvc: '123'
        }
      };

      const paymentResponse = {
        id: 1,
        order_id: 1,
        status: 'completed',
        transaction_id: 'TXN123456789',
        amount: 1255000,
        paid_at: '2023-01-01T12:00:00Z'
      };

      mock.onPost('/api/v1/payments/').reply(200, paymentResponse);

      const result = await processPayment(paymentData);

      expect(result).toEqual(paymentResponse);
      expect(JSON.parse(mock.history.post[0].data)).toEqual(paymentData);
    });

    test('processPayment API 실패 시 에러를 던진다', async () => {
      const paymentData = {
        order_id: 1,
        payment_method: 'credit_card',
        amount: 1255000,
        card_info: {
          number: 'invalid-card',
          expiry: '12/25',
          cvc: '123'
        }
      };

      mock.onPost('/api/v1/payments/').reply(400, {
        error_code: 'INVALID_CARD_INFO',
        message: '카드 정보가 올바르지 않습니다.'
      });

      await expect(processPayment(paymentData)).rejects.toThrow();
    });
  });

  describe('User API', () => {
    test('getUserInfo API가 올바르게 작동한다', async () => {
      localStorage.setItem('token', 'mock-token');
      mock.onGet('/api/v1/users/me').reply(200, mockUser);

      const result = await getUserInfo();

      expect(result).toEqual(mockUser);
      expect(mock.history.get[0].headers?.Authorization).toBe('Bearer mock-token');
    });

    test('updateUserInfo API가 올바르게 작동한다', async () => {
      localStorage.setItem('token', 'mock-token');
      const updateData = {
        name: '김철수',
        email: 'kim@example.com'
      };

      const updatedUser = { ...mockUser, ...updateData };
      mock.onPut('/api/v1/users/me').reply(200, updatedUser);

      const result = await updateUserInfo(updateData);

      expect(result).toEqual(updatedUser);
      expect(JSON.parse(mock.history.put[0].data)).toEqual(updateData);
      expect(mock.history.put[0].headers?.Authorization).toBe('Bearer mock-token');
    });
  });

  describe('Error Handling', () => {
    test('네트워크 에러가 올바르게 처리된다', async () => {
      mock.onGet('/api/v1/plans/').networkError();

      await expect(getPlans()).rejects.toThrow('Network Error');
    });

    test('타임아웃 에러가 올바르게 처리된다', async () => {
      mock.onGet('/api/v1/plans/').timeout();

      await expect(getPlans()).rejects.toThrow('timeout');
    });

    test('서버 에러(500)가 올바르게 처리된다', async () => {
      mock.onGet('/api/v1/plans/').reply(500, {
        error_code: 'INTERNAL_SERVER_ERROR',
        message: '서버 내부 오류가 발생했습니다.'
      });

      await expect(getPlans()).rejects.toThrow();
    });
  });

  describe('Request Interceptors', () => {
    test('Authorization 헤더가 자동으로 추가된다', async () => {
      localStorage.setItem('token', 'mock-token');
      mock.onGet('/api/v1/plans/').reply(200, []);

      await getPlans();

      expect(mock.history.get[0].headers?.Authorization).toBe('Bearer mock-token');
    });

    test('토큰이 없을 때는 Authorization 헤더가 추가되지 않는다', async () => {
      localStorage.removeItem('token');
      mock.onGet('/api/v1/plans/').reply(200, []);

      await getPlans();

      expect(mock.history.get[0].headers?.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptors', () => {
    test('401 에러 시 자동으로 토큰 갱신을 시도한다', async () => {
      localStorage.setItem('token', 'expired-token');
      localStorage.setItem('refreshToken', 'valid-refresh-token');

      // 첫 번째 요청은 401 에러
      mock.onGet('/api/v1/plans/').replyOnce(401, {
        error_code: 'TOKEN_EXPIRED',
        message: '토큰이 만료되었습니다.'
      });

      // 토큰 갱신 요청은 성공
      mock.onPost('/api/v1/auth/refresh').reply(200, {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token'
      });

      // 재시도 요청은 성공
      mock.onGet('/api/v1/plans/').reply(200, [mockPlan]);

      const result = await getPlans();

      expect(result).toEqual([mockPlan]);
      expect(localStorage.getItem('token')).toBe('new-access-token');
      expect(localStorage.getItem('refreshToken')).toBe('new-refresh-token');
    });

    test('토큰 갱신 실패 시 로그아웃 처리된다', async () => {
      localStorage.setItem('token', 'expired-token');
      localStorage.setItem('refreshToken', 'invalid-refresh-token');

      // 첫 번째 요청은 401 에러
      mock.onGet('/api/v1/plans/').replyOnce(401);

      // 토큰 갱신 요청도 실패
      mock.onPost('/api/v1/auth/refresh').reply(401, {
        error_code: 'INVALID_REFRESH_TOKEN',
        message: '리프레시 토큰이 유효하지 않습니다.'
      });

      await expect(getPlans()).rejects.toThrow();

      // 토큰이 제거되어야 함
      expect(localStorage.getItem('token')).toBeNull();
      expect(localStorage.getItem('refreshToken')).toBeNull();
    });
  });
});