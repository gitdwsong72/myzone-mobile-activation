import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

// 주문 관련 타입 정의
interface Plan {
  id: number;
  name: string;
  monthlyFee: number;
  dataLimit: string;
  callMinutes: number;
  smsCount: number;
}

interface Device {
  id: number;
  brand: string;
  model: string;
  color: string;
  price: number;
}

interface PhoneNumber {
  id: number;
  number: string;
  category: string;
  additionalFee: number;
}

interface UserInfo {
  name: string;
  phone: string;
  email: string;
  birthDate: string;
  gender: string;
  address: string;
}

interface Order {
  id?: number;
  orderNumber?: string;
  status?: string;
  totalAmount?: number;
  createdAt?: string;
}

interface OrderState {
  // 선택된 항목들
  selectedPlan: Plan | null;
  selectedDevice: Device | null;
  selectedNumber: PhoneNumber | null;
  userInfo: UserInfo | null;
  
  // 현재 주문
  currentOrder: Order | null;
  
  // 진행 단계
  currentStep: number;
  
  // 로딩 및 에러 상태
  loading: boolean;
  error: string | null;
}

const initialState: OrderState = {
  selectedPlan: null,
  selectedDevice: null,
  selectedNumber: null,
  userInfo: null,
  currentOrder: null,
  currentStep: 1,
  loading: false,
  error: null,
};

// 비동기 액션: 주문 생성
export const createOrder = createAsyncThunk(
  'order/create',
  async (orderData: {
    planId: number;
    deviceId: number;
    numberId: number;
    userInfo: UserInfo;
  }) => {
    const response = await api.post('/orders', orderData);
    return response.data;
  }
);

// 비동기 액션: 주문 상태 조회
export const fetchOrderStatus = createAsyncThunk(
  'order/fetchStatus',
  async (orderNumber: string) => {
    const response = await api.get(`/orders/${orderNumber}`);
    return response.data;
  }
);

const orderSlice = createSlice({
  name: 'order',
  initialState,
  reducers: {
    // 요금제 선택
    selectPlan: (state, action: PayloadAction<Plan>) => {
      state.selectedPlan = action.payload;
    },
    
    // 단말기 선택
    selectDevice: (state, action: PayloadAction<Device>) => {
      state.selectedDevice = action.payload;
    },
    
    // 번호 선택
    selectNumber: (state, action: PayloadAction<PhoneNumber>) => {
      state.selectedNumber = action.payload;
    },
    
    // 사용자 정보 설정
    setUserInfo: (state, action: PayloadAction<UserInfo>) => {
      state.userInfo = action.payload;
    },
    
    // 진행 단계 설정
    setCurrentStep: (state, action: PayloadAction<number>) => {
      state.currentStep = action.payload;
    },
    
    // 다음 단계로 이동
    nextStep: (state) => {
      state.currentStep += 1;
    },
    
    // 이전 단계로 이동
    prevStep: (state) => {
      if (state.currentStep > 1) {
        state.currentStep -= 1;
      }
    },
    
    // 주문 초기화
    resetOrder: (state) => {
      state.selectedPlan = null;
      state.selectedDevice = null;
      state.selectedNumber = null;
      state.userInfo = null;
      state.currentOrder = null;
      state.currentStep = 1;
      state.error = null;
    },
    
    // 에러 클리어
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 주문 생성
      .addCase(createOrder.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createOrder.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
        state.error = null;
      })
      .addCase(createOrder.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '주문 생성에 실패했습니다.';
      })
      // 주문 상태 조회
      .addCase(fetchOrderStatus.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOrderStatus.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
        state.error = null;
      })
      .addCase(fetchOrderStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '주문 조회에 실패했습니다.';
      });
  },
});

export const {
  selectPlan,
  selectDevice,
  selectNumber,
  setUserInfo,
  setCurrentStep,
  nextStep,
  prevStep,
  resetOrder,
  clearError,
} = orderSlice.actions;

export default orderSlice.reducer;