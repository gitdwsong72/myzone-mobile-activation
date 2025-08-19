import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

// 인증 상태 타입 정의
interface AuthState {
  isAuthenticated: boolean;
  user: {
    id: number;
    name: string;
    email: string;
    role: string;
  } | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

// 초기 상태
const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  token: localStorage.getItem('access_token'),
  loading: false,
  error: null,
};

// 비동기 액션: 로그인
export const login = createAsyncThunk(
  'auth/login',
  async (credentials: { email: string; password: string }) => {
    const response = await api.post('/auth/login', credentials);
    const { access_token, user } = response.data;
    
    // 토큰을 localStorage에 저장
    localStorage.setItem('access_token', access_token);
    
    return { token: access_token, user };
  }
);

// 비동기 액션: 로그아웃
export const logout = createAsyncThunk('auth/logout', async () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
});

// 비동기 액션: 사용자 정보 조회
export const fetchUserProfile = createAsyncThunk('auth/fetchUserProfile', async () => {
  const response = await api.get('/auth/me');
  return response.data;
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
      state.isAuthenticated = true;
    },
  },
  extraReducers: (builder) => {
    builder
      // 로그인
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.user = action.payload.user;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.token = null;
        state.user = null;
        state.error = action.error.message || '로그인에 실패했습니다.';
      })
      // 로그아웃
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.token = null;
        state.user = null;
        state.error = null;
      })
      // 사용자 정보 조회
      .addCase(fetchUserProfile.fulfilled, (state, action) => {
        state.user = action.payload;
        state.isAuthenticated = true;
      });
  },
});

export const { clearError, setToken } = authSlice.actions;
export default authSlice.reducer;