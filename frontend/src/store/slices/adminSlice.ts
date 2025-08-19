import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

// 관리자 상태 타입 정의
interface AdminState {
  isAuthenticated: boolean;
  admin: {
    id: number;
    username: string;
    email: string;
    role: string;
    last_login: string;
  } | null;
  token: string | null;
  loading: boolean;
  error: string | null;
  dashboardStats: {
    todayOrders: number;
    pendingOrders: number;
    completedOrders: number;
    totalRevenue: number;
  } | null;
  statsLoading: boolean;
}

// 초기 상태
const initialState: AdminState = {
  isAuthenticated: false,
  admin: null,
  token: localStorage.getItem('admin_access_token'),
  loading: false,
  error: null,
  dashboardStats: null,
  statsLoading: false,
};

// 비동기 액션: 관리자 로그인
export const adminLogin = createAsyncThunk(
  'admin/login',
  async (credentials: { username: string; password: string }) => {
    const response = await api.post('/admin/login', credentials);
    const { access_token, admin } = response.data;
    
    // 관리자 토큰을 localStorage에 저장
    localStorage.setItem('admin_access_token', access_token);
    
    return { token: access_token, admin };
  }
);

// 비동기 액션: 관리자 로그아웃
export const adminLogout = createAsyncThunk('admin/logout', async () => {
  localStorage.removeItem('admin_access_token');
  localStorage.removeItem('admin_refresh_token');
});

// 비동기 액션: 대시보드 통계 조회
export const fetchDashboardStats = createAsyncThunk('admin/fetchDashboardStats', async () => {
  const response = await api.get('/admin/dashboard/stats');
  return response.data;
});

// 비동기 액션: 관리자 프로필 조회
export const fetchAdminProfile = createAsyncThunk('admin/fetchAdminProfile', async () => {
  const response = await api.get('/admin/me');
  return response.data;
});

const adminSlice = createSlice({
  name: 'admin',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setAdminToken: (state, action: PayloadAction<string>) => {
      state.token = action.payload;
      state.isAuthenticated = true;
    },
  },
  extraReducers: (builder) => {
    builder
      // 관리자 로그인
      .addCase(adminLogin.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(adminLogin.fulfilled, (state, action) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.token = action.payload.token;
        state.admin = action.payload.admin;
        state.error = null;
      })
      .addCase(adminLogin.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.token = null;
        state.admin = null;
        state.error = action.error.message || '관리자 로그인에 실패했습니다.';
      })
      // 관리자 로그아웃
      .addCase(adminLogout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.token = null;
        state.admin = null;
        state.error = null;
        state.dashboardStats = null;
      })
      // 대시보드 통계 조회
      .addCase(fetchDashboardStats.pending, (state) => {
        state.statsLoading = true;
      })
      .addCase(fetchDashboardStats.fulfilled, (state, action) => {
        state.statsLoading = false;
        state.dashboardStats = action.payload;
      })
      .addCase(fetchDashboardStats.rejected, (state) => {
        state.statsLoading = false;
      })
      // 관리자 프로필 조회
      .addCase(fetchAdminProfile.fulfilled, (state, action) => {
        state.admin = action.payload;
        state.isAuthenticated = true;
      });
  },
});

export const { clearError, setAdminToken } = adminSlice.actions;
export default adminSlice.reducer;