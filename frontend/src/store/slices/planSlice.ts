import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// 요금제 타입 정의
interface Plan {
  id: number;
  name: string;
  description: string;
  monthlyFee: number;
  dataLimit: string;
  callMinutes: number;
  smsCount: number;
  category: string;
  isActive: boolean;
  createdAt: string;
}

interface PlanState {
  plans: Plan[];
  filteredPlans: Plan[];
  selectedCategory: string;
  loading: boolean;
  error: string | null;
}

const initialState: PlanState = {
  plans: [],
  filteredPlans: [],
  selectedCategory: 'all',
  loading: false,
  error: null,
};

// 비동기 액션: 요금제 목록 조회
export const fetchPlans = createAsyncThunk('plans/fetchPlans', async () => {
  const response = await api.get('/plans');
  return response.data;
});

// 비동기 액션: 요금제 상세 조회
export const fetchPlanById = createAsyncThunk(
  'plans/fetchPlanById',
  async (planId: number) => {
    const response = await api.get(`/plans/${planId}`);
    return response.data;
  }
);

const planSlice = createSlice({
  name: 'plans',
  initialState,
  reducers: {
    // 카테고리별 필터링
    filterByCategory: (state, action) => {
      const category = action.payload;
      state.selectedCategory = category;
      
      if (category === 'all') {
        state.filteredPlans = state.plans;
      } else {
        state.filteredPlans = state.plans.filter(plan => plan.category === category);
      }
    },
    
    // 에러 클리어
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 요금제 목록 조회
      .addCase(fetchPlans.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPlans.fulfilled, (state, action) => {
        state.loading = false;
        state.plans = action.payload;
        state.filteredPlans = action.payload;
        state.error = null;
      })
      .addCase(fetchPlans.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '요금제 조회에 실패했습니다.';
      })
      // 요금제 상세 조회
      .addCase(fetchPlanById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchPlanById.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(fetchPlanById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '요금제 상세 조회에 실패했습니다.';
      });
  },
});

export const { filterByCategory, clearError } = planSlice.actions;
export default planSlice.reducer;