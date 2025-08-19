import { configureStore } from '@reduxjs/toolkit';
import orderSlice, {
  setCurrentStep,
  setUserInfo,
  setPlan,
  setDevice,
  setNumber,
  setDeliveryInfo,
  setPaymentInfo,
  createOrderStart,
  createOrderSuccess,
  createOrderFailure,
  fetchOrderStart,
  fetchOrderSuccess,
  fetchOrderFailure,
  clearOrder,
  clearError,
  OrderState
} from '../orderSlice';
import { mockUser, mockPlan, mockDevice, mockNumber, mockOrder } from '../../../test-utils';

describe('orderSlice', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        order: orderSlice,
      },
    });
  });

  test('초기 상태가 올바르게 설정된다', () => {
    const state = store.getState().order;
    
    expect(state).toEqual({
      currentStep: 1,
      userInfo: null,
      selectedPlan: null,
      selectedDevice: null,
      selectedNumber: null,
      deliveryInfo: null,
      paymentInfo: null,
      currentOrder: null,
      loading: false,
      error: null,
    });
  });

  test('setCurrentStep 액션이 올바르게 처리된다', () => {
    store.dispatch(setCurrentStep(3));
    const state = store.getState().order;
    
    expect(state.currentStep).toBe(3);
  });

  test('setUserInfo 액션이 올바르게 처리된다', () => {
    store.dispatch(setUserInfo(mockUser));
    const state = store.getState().order;
    
    expect(state.userInfo).toEqual(mockUser);
  });

  test('setPlan 액션이 올바르게 처리된다', () => {
    store.dispatch(setPlan(mockPlan));
    const state = store.getState().order;
    
    expect(state.selectedPlan).toEqual(mockPlan);
  });

  test('setDevice 액션이 올바르게 처리된다', () => {
    store.dispatch(setDevice(mockDevice));
    const state = store.getState().order;
    
    expect(state.selectedDevice).toEqual(mockDevice);
  });

  test('setNumber 액션이 올바르게 처리된다', () => {
    store.dispatch(setNumber(mockNumber));
    const state = store.getState().order;
    
    expect(state.selectedNumber).toEqual(mockNumber);
  });

  test('setDeliveryInfo 액션이 올바르게 처리된다', () => {
    const deliveryInfo = {
      address: '서울시 강남구 테헤란로 123',
      detailAddress: '456호',
      zipCode: '12345',
      recipientName: '홍길동',
      recipientPhone: '010-1234-5678',
      deliveryRequest: '문 앞에 놓아주세요'
    };
    
    store.dispatch(setDeliveryInfo(deliveryInfo));
    const state = store.getState().order;
    
    expect(state.deliveryInfo).toEqual(deliveryInfo);
  });

  test('setPaymentInfo 액션이 올바르게 처리된다', () => {
    const paymentInfo = {
      method: 'credit_card',
      cardNumber: '**** **** **** 1234',
      installment: 12,
      amount: 1255000
    };
    
    store.dispatch(setPaymentInfo(paymentInfo));
    const state = store.getState().order;
    
    expect(state.paymentInfo).toEqual(paymentInfo);
  });

  test('createOrderStart 액션이 올바르게 처리된다', () => {
    store.dispatch(createOrderStart());
    const state = store.getState().order;
    
    expect(state.loading).toBe(true);
    expect(state.error).toBe(null);
  });

  test('createOrderSuccess 액션이 올바르게 처리된다', () => {
    store.dispatch(createOrderSuccess(mockOrder));
    const state = store.getState().order;
    
    expect(state.currentOrder).toEqual(mockOrder);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  test('createOrderFailure 액션이 올바르게 처리된다', () => {
    const errorMessage = '주문 생성에 실패했습니다.';
    
    store.dispatch(createOrderFailure(errorMessage));
    const state = store.getState().order;
    
    expect(state.currentOrder).toBe(null);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(errorMessage);
  });

  test('fetchOrderStart 액션이 올바르게 처리된다', () => {
    store.dispatch(fetchOrderStart());
    const state = store.getState().order;
    
    expect(state.loading).toBe(true);
    expect(state.error).toBe(null);
  });

  test('fetchOrderSuccess 액션이 올바르게 처리된다', () => {
    store.dispatch(fetchOrderSuccess(mockOrder));
    const state = store.getState().order;
    
    expect(state.currentOrder).toEqual(mockOrder);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  test('fetchOrderFailure 액션이 올바르게 처리된다', () => {
    const errorMessage = '주문 조회에 실패했습니다.';
    
    store.dispatch(fetchOrderFailure(errorMessage));
    const state = store.getState().order;
    
    expect(state.loading).toBe(false);
    expect(state.error).toBe(errorMessage);
  });

  test('clearOrder 액션이 올바르게 처리된다', () => {
    // 먼저 주문 정보를 설정
    store.dispatch(setUserInfo(mockUser));
    store.dispatch(setPlan(mockPlan));
    store.dispatch(setDevice(mockDevice));
    store.dispatch(setNumber(mockNumber));
    store.dispatch(createOrderSuccess(mockOrder));
    
    // 주문 정보 클리어
    store.dispatch(clearOrder());
    const state = store.getState().order;
    
    expect(state.currentStep).toBe(1);
    expect(state.userInfo).toBe(null);
    expect(state.selectedPlan).toBe(null);
    expect(state.selectedDevice).toBe(null);
    expect(state.selectedNumber).toBe(null);
    expect(state.deliveryInfo).toBe(null);
    expect(state.paymentInfo).toBe(null);
    expect(state.currentOrder).toBe(null);
    expect(state.error).toBe(null);
  });

  test('clearError 액션이 올바르게 처리된다', () => {
    // 먼저 에러 상태로 만들기
    store.dispatch(createOrderFailure('테스트 에러'));
    
    // 에러 클리어
    store.dispatch(clearError());
    const state = store.getState().order;
    
    expect(state.error).toBe(null);
  });

  test('주문 플로우가 올바르게 진행된다', () => {
    // 1단계: 요금제 선택
    store.dispatch(setCurrentStep(1));
    store.dispatch(setPlan(mockPlan));
    
    let state = store.getState().order;
    expect(state.currentStep).toBe(1);
    expect(state.selectedPlan).toEqual(mockPlan);
    
    // 2단계: 사용자 정보 입력
    store.dispatch(setCurrentStep(2));
    store.dispatch(setUserInfo(mockUser));
    
    state = store.getState().order;
    expect(state.currentStep).toBe(2);
    expect(state.userInfo).toEqual(mockUser);
    
    // 3단계: 단말기 선택
    store.dispatch(setCurrentStep(3));
    store.dispatch(setDevice(mockDevice));
    
    state = store.getState().order;
    expect(state.currentStep).toBe(3);
    expect(state.selectedDevice).toEqual(mockDevice);
    
    // 4단계: 번호 선택
    store.dispatch(setCurrentStep(4));
    store.dispatch(setNumber(mockNumber));
    
    state = store.getState().order;
    expect(state.currentStep).toBe(4);
    expect(state.selectedNumber).toEqual(mockNumber);
    
    // 5단계: 주문 생성
    store.dispatch(setCurrentStep(5));
    store.dispatch(createOrderStart());
    store.dispatch(createOrderSuccess(mockOrder));
    
    state = store.getState().order;
    expect(state.currentStep).toBe(5);
    expect(state.currentOrder).toEqual(mockOrder);
    expect(state.loading).toBe(false);
  });

  test('상태 불변성이 유지된다', () => {
    const initialState = store.getState().order;
    
    store.dispatch(setCurrentStep(2));
    const newState = store.getState().order;
    
    // 새로운 상태 객체가 생성되어야 함
    expect(newState).not.toBe(initialState);
    
    // 하지만 변경되지 않은 속성들은 같은 참조를 유지해야 함
    expect(newState.userInfo).toBe(initialState.userInfo);
    expect(newState.selectedPlan).toBe(initialState.selectedPlan);
  });

  test('복잡한 객체 업데이트가 올바르게 처리된다', () => {
    const deliveryInfo = {
      address: '서울시 강남구 테헤란로 123',
      detailAddress: '456호',
      zipCode: '12345',
      recipientName: '홍길동',
      recipientPhone: '010-1234-5678',
      deliveryRequest: '문 앞에 놓아주세요'
    };
    
    store.dispatch(setDeliveryInfo(deliveryInfo));
    
    // 배송 정보 일부 수정
    const updatedDeliveryInfo = {
      ...deliveryInfo,
      deliveryRequest: '경비실에 맡겨주세요'
    };
    
    store.dispatch(setDeliveryInfo(updatedDeliveryInfo));
    const state = store.getState().order;
    
    expect(state.deliveryInfo?.deliveryRequest).toBe('경비실에 맡겨주세요');
    expect(state.deliveryInfo?.address).toBe('서울시 강남구 테헤란로 123');
  });

  test('에러 상태 관리가 올바르게 작동한다', () => {
    // 주문 생성 실패
    store.dispatch(createOrderFailure('결제 정보가 올바르지 않습니다.'));
    expect(store.getState().order.error).toBe('결제 정보가 올바르지 않습니다.');
    
    // 에러 클리어 후 다시 시도
    store.dispatch(clearError());
    expect(store.getState().order.error).toBe(null);
    
    store.dispatch(createOrderStart());
    expect(store.getState().order.loading).toBe(true);
    expect(store.getState().order.error).toBe(null);
    
    // 성공
    store.dispatch(createOrderSuccess(mockOrder));
    const finalState = store.getState().order;
    expect(finalState.currentOrder).toEqual(mockOrder);
    expect(finalState.loading).toBe(false);
    expect(finalState.error).toBe(null);
  });

  test('로딩 상태가 올바르게 관리된다', () => {
    expect(store.getState().order.loading).toBe(false);
    
    // 주문 생성 시작
    store.dispatch(createOrderStart());
    expect(store.getState().order.loading).toBe(true);
    
    // 주문 생성 성공
    store.dispatch(createOrderSuccess(mockOrder));
    expect(store.getState().order.loading).toBe(false);
    
    // 주문 조회 시작
    store.dispatch(fetchOrderStart());
    expect(store.getState().order.loading).toBe(true);
    
    // 주문 조회 실패
    store.dispatch(fetchOrderFailure('주문을 찾을 수 없습니다.'));
    expect(store.getState().order.loading).toBe(false);
  });
});