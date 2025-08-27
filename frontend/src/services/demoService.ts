import { 
  mockPlans, 
  mockDevices, 
  mockNumbers, 
  mockUser, 
  mockOrder, 
  mockPayment,
  simulateApiDelay,
  shouldSimulateError
} from '../data/mockData';
import { isDemoMode } from '../config/demo';

// 데모 모드 API 서비스
export class DemoService {
  // 에러 시뮬레이션
  private async simulateApiCall<T>(data: T, errorMessage?: string): Promise<T> {
    await simulateApiDelay(500 + Math.random() * 1000); // 0.5-1.5초 지연
    
    if (shouldSimulateError() && errorMessage) {
      throw new Error(errorMessage);
    }
    
    return data;
  }

  // 요금제 API
  async getPlans() {
    return this.simulateApiCall(mockPlans, "요금제 정보를 불러올 수 없습니다");
  }

  async getPlanById(id: number) {
    const plan = mockPlans.find(p => p.id === id);
    if (!plan) {
      throw new Error("요금제를 찾을 수 없습니다");
    }
    return this.simulateApiCall(plan);
  }

  // 기기 API
  async getDevices() {
    return this.simulateApiCall(mockDevices, "기기 정보를 불러올 수 없습니다");
  }

  async getDeviceById(id: number) {
    const device = mockDevices.find(d => d.id === id);
    if (!device) {
      throw new Error("기기를 찾을 수 없습니다");
    }
    return this.simulateApiCall(device);
  }

  // 번호 API
  async getNumbers() {
    return this.simulateApiCall(mockNumbers, "번호 정보를 불러올 수 없습니다");
  }

  async searchNumbers(pattern: string) {
    const filteredNumbers = mockNumbers.filter(n => 
      n.number.includes(pattern) || n.type.includes(pattern)
    );
    return this.simulateApiCall(filteredNumbers);
  }

  async reserveNumber(id: number) {
    const number = mockNumbers.find(n => n.id === id);
    if (!number) {
      throw new Error("번호를 찾을 수 없습니다");
    }
    if (number.reserved) {
      throw new Error("이미 예약된 번호입니다");
    }
    
    // 목업 데이터 업데이트
    number.reserved = true;
    return this.simulateApiCall({ success: true, message: "번호가 예약되었습니다" });
  }

  // 사용자 API
  async createUser(userData: any) {
    const newUser = { ...mockUser, ...userData, id: Date.now() };
    return this.simulateApiCall(newUser, "사용자 생성에 실패했습니다");
  }

  async verifyUser(verificationData: any) {
    await simulateApiDelay(2000); // 인증 시간 시뮬레이션
    return this.simulateApiCall({ 
      success: true, 
      message: "인증이 완료되었습니다 (데모)" 
    });
  }

  // 주문 API
  async createOrder(orderData: any) {
    const newOrder = {
      ...mockOrder,
      id: Date.now(),
      orderNumber: `MZ${Date.now()}`,
      ...orderData,
      createdAt: new Date().toISOString()
    };
    return this.simulateApiCall(newOrder, "주문 생성에 실패했습니다");
  }

  async getOrderById(id: number) {
    return this.simulateApiCall(mockOrder);
  }

  async getOrderByNumber(orderNumber: string) {
    const order = { ...mockOrder, orderNumber };
    return this.simulateApiCall(order);
  }

  // 결제 API
  async createPayment(paymentData: any) {
    const newPayment = {
      ...mockPayment,
      id: Date.now(),
      transactionId: `TXN${Date.now()}`,
      ...paymentData,
      createdAt: new Date().toISOString()
    };
    return this.simulateApiCall(newPayment, "결제 처리에 실패했습니다");
  }

  async verifyPayment(transactionId: string) {
    await simulateApiDelay(3000); // 결제 검증 시간 시뮬레이션
    return this.simulateApiCall({
      success: true,
      status: "completed",
      message: "결제가 완료되었습니다 (데모)"
    });
  }

  // 인증 API
  async login(credentials: any) {
    await simulateApiDelay(1500);
    return this.simulateApiCall({
      access_token: "demo_access_token",
      refresh_token: "demo_refresh_token",
      user: mockUser
    });
  }

  async getProfile() {
    return this.simulateApiCall(mockUser);
  }
}

// 데모 서비스 인스턴스
export const demoService = new DemoService();

// API 호출 래퍼 - 실제 API 실패 시 데모 서비스 사용
export const withDemoFallback = async <T>(
  apiCall: () => Promise<T>,
  demoCall: () => Promise<T>,
  fallbackMessage?: string
): Promise<T> => {
  try {
    // 데모 모드가 활성화된 경우 바로 데모 서비스 사용
    if (isDemoMode()) {
      console.log('🎭 Demo mode: Using mock data');
      return await demoCall();
    }
    
    // 실제 API 호출 시도
    return await apiCall();
  } catch (error) {
    console.warn('API call failed, falling back to demo data:', error);
    
    // 실패 시 데모 데이터 사용
    try {
      const result = await demoCall();
      
      // 사용자에게 데모 모드임을 알림
      if (fallbackMessage) {
        console.log(`🎭 ${fallbackMessage}`);
      }
      
      return result;
    } catch (demoError) {
      console.error('Demo fallback also failed:', demoError);
      throw new Error('서비스에 일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    }
  }
};