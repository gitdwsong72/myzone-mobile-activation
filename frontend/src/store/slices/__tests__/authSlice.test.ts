import { configureStore } from '@reduxjs/toolkit';
import authSlice, {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  refreshTokenStart,
  refreshTokenSuccess,
  refreshTokenFailure,
  clearError,
  AuthState
} from '../authSlice';

describe('authSlice', () => {
  let store: ReturnType<typeof configureStore>;

  beforeEach(() => {
    store = configureStore({
      reducer: {
        auth: authSlice,
      },
    });
  });

  test('초기 상태가 올바르게 설정된다', () => {
    const state = store.getState().auth;
    
    expect(state).toEqual({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      loading: false,
      error: null,
    });
  });

  test('loginStart 액션이 올바르게 처리된다', () => {
    store.dispatch(loginStart());
    const state = store.getState().auth;
    
    expect(state.loading).toBe(true);
    expect(state.error).toBe(null);
  });

  test('loginSuccess 액션이 올바르게 처리된다', () => {
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin'
    };
    
    const mockTokens = {
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token'
    };

    store.dispatch(loginSuccess({
      user: mockUser,
      ...mockTokens
    }));
    
    const state = store.getState().auth;
    
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe('mock-access-token');
    expect(state.refreshToken).toBe('mock-refresh-token');
    expect(state.isAuthenticated).toBe(true);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  test('loginFailure 액션이 올바르게 처리된다', () => {
    const errorMessage = '로그인에 실패했습니다.';
    
    store.dispatch(loginFailure(errorMessage));
    const state = store.getState().auth;
    
    expect(state.user).toBe(null);
    expect(state.token).toBe(null);
    expect(state.refreshToken).toBe(null);
    expect(state.isAuthenticated).toBe(false);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(errorMessage);
  });

  test('logout 액션이 올바르게 처리된다', () => {
    // 먼저 로그인 상태로 만들기
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin'
    };
    
    store.dispatch(loginSuccess({
      user: mockUser,
      access_token: 'mock-access-token',
      refresh_token: 'mock-refresh-token'
    }));
    
    // 로그아웃 실행
    store.dispatch(logout());
    const state = store.getState().auth;
    
    expect(state.user).toBe(null);
    expect(state.token).toBe(null);
    expect(state.refreshToken).toBe(null);
    expect(state.isAuthenticated).toBe(false);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  test('refreshTokenStart 액션이 올바르게 처리된다', () => {
    store.dispatch(refreshTokenStart());
    const state = store.getState().auth;
    
    expect(state.loading).toBe(true);
    expect(state.error).toBe(null);
  });

  test('refreshTokenSuccess 액션이 올바르게 처리된다', () => {
    const newTokens = {
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token'
    };

    store.dispatch(refreshTokenSuccess(newTokens));
    const state = store.getState().auth;
    
    expect(state.token).toBe('new-access-token');
    expect(state.refreshToken).toBe('new-refresh-token');
    expect(state.loading).toBe(false);
    expect(state.error).toBe(null);
  });

  test('refreshTokenFailure 액션이 올바르게 처리된다', () => {
    const errorMessage = '토큰 갱신에 실패했습니다.';
    
    store.dispatch(refreshTokenFailure(errorMessage));
    const state = store.getState().auth;
    
    expect(state.user).toBe(null);
    expect(state.token).toBe(null);
    expect(state.refreshToken).toBe(null);
    expect(state.isAuthenticated).toBe(false);
    expect(state.loading).toBe(false);
    expect(state.error).toBe(errorMessage);
  });

  test('clearError 액션이 올바르게 처리된다', () => {
    // 먼저 에러 상태로 만들기
    store.dispatch(loginFailure('테스트 에러'));
    
    // 에러 클리어
    store.dispatch(clearError());
    const state = store.getState().auth;
    
    expect(state.error).toBe(null);
  });

  test('연속된 액션들이 올바르게 처리된다', () => {
    // 로그인 시작
    store.dispatch(loginStart());
    expect(store.getState().auth.loading).toBe(true);
    
    // 로그인 실패
    store.dispatch(loginFailure('첫 번째 실패'));
    expect(store.getState().auth.error).toBe('첫 번째 실패');
    expect(store.getState().auth.loading).toBe(false);
    
    // 에러 클리어
    store.dispatch(clearError());
    expect(store.getState().auth.error).toBe(null);
    
    // 다시 로그인 시작
    store.dispatch(loginStart());
    expect(store.getState().auth.loading).toBe(true);
    
    // 로그인 성공
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin'
    };
    
    store.dispatch(loginSuccess({
      user: mockUser,
      access_token: 'token',
      refresh_token: 'refresh'
    }));
    
    const finalState = store.getState().auth;
    expect(finalState.isAuthenticated).toBe(true);
    expect(finalState.user).toEqual(mockUser);
    expect(finalState.loading).toBe(false);
    expect(finalState.error).toBe(null);
  });

  test('상태 불변성이 유지된다', () => {
    const initialState = store.getState().auth;
    
    store.dispatch(loginStart());
    const newState = store.getState().auth;
    
    // 새로운 상태 객체가 생성되어야 함
    expect(newState).not.toBe(initialState);
    
    // 하지만 변경되지 않은 속성들은 같은 참조를 유지해야 함
    expect(newState.user).toBe(initialState.user);
    expect(newState.token).toBe(initialState.token);
  });

  test('타입 안전성이 보장된다', () => {
    // TypeScript 컴파일 시점에서 타입 체크가 이루어지므로
    // 런타임에서는 올바른 타입의 액션만 디스패치될 수 있음
    
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin'
    };
    
    // 올바른 타입의 페이로드
    store.dispatch(loginSuccess({
      user: mockUser,
      access_token: 'token',
      refresh_token: 'refresh'
    }));
    
    const state = store.getState().auth;
    expect(state.user?.id).toBe(1);
    expect(state.user?.username).toBe('admin');
  });

  test('localStorage와의 동기화가 올바르게 작동한다', () => {
    const mockUser = {
      id: 1,
      username: 'admin',
      email: 'admin@example.com',
      role: 'admin'
    };
    
    // 로그인 성공 시 localStorage에 저장되어야 함
    store.dispatch(loginSuccess({
      user: mockUser,
      access_token: 'token',
      refresh_token: 'refresh'
    }));
    
    expect(localStorage.setItem).toHaveBeenCalledWith('token', 'token');
    expect(localStorage.setItem).toHaveBeenCalledWith('refreshToken', 'refresh');
    expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(mockUser));
    
    // 로그아웃 시 localStorage에서 제거되어야 함
    store.dispatch(logout());
    
    expect(localStorage.removeItem).toHaveBeenCalledWith('token');
    expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken');
    expect(localStorage.removeItem).toHaveBeenCalledWith('user');
  });
});