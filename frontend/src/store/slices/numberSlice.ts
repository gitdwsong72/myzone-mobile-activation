import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// 번호 타입 정의
interface PhoneNumber {
  id: number;
  number: string;
  category: string;
  additionalFee: number;
  status: string;
  reservedUntil: string | null;
}

interface NumberState {
  numbers: PhoneNumber[];
  filteredNumbers: PhoneNumber[];
  selectedCategory: string;
  searchPattern: string;
  reservedNumber: PhoneNumber | null;
  reservationTimer: number;
  loading: boolean;
  error: string | null;
}

const initialState: NumberState = {
  numbers: [],
  filteredNumbers: [],
  selectedCategory: 'all',
  searchPattern: '',
  reservedNumber: null,
  reservationTimer: 0,
  loading: false,
  error: null,
};

// 비동기 액션: 번호 목록 조회
export const fetchNumbers = createAsyncThunk('numbers/fetchNumbers', async () => {
  const response = await api.get('/numbers');
  return response.data;
});

// 비동기 액션: 번호 검색
export const searchNumbers = createAsyncThunk(
  'numbers/searchNumbers',
  async (pattern: string) => {
    const response = await api.get(`/numbers/search?pattern=${pattern}`);
    return response.data;
  }
);

// 비동기 액션: 번호 예약
export const reserveNumber = createAsyncThunk(
  'numbers/reserveNumber',
  async (numberId: number) => {
    const response = await api.post(`/numbers/${numberId}/reserve`);
    return response.data;
  }
);

// 비동기 액션: 번호 예약 해제
export const releaseNumber = createAsyncThunk(
  'numbers/releaseNumber',
  async (numberId: number) => {
    const response = await api.delete(`/numbers/${numberId}/reserve`);
    return response.data;
  }
);

const numberSlice = createSlice({
  name: 'numbers',
  initialState,
  reducers: {
    // 카테고리별 필터링
    filterByCategory: (state, action) => {
      const category = action.payload;
      state.selectedCategory = category;
      
      if (category === 'all') {
        state.filteredNumbers = state.numbers;
      } else {
        state.filteredNumbers = state.numbers.filter(number => number.category === category);
      }
    },
    
    // 검색 패턴 설정
    setSearchPattern: (state, action) => {
      state.searchPattern = action.payload;
    },
    
    // 예약 타이머 설정
    setReservationTimer: (state, action) => {
      state.reservationTimer = action.payload;
    },
    
    // 예약 타이머 감소
    decrementTimer: (state) => {
      if (state.reservationTimer > 0) {
        state.reservationTimer -= 1;
      }
    },
    
    // 예약 해제
    clearReservation: (state) => {
      state.reservedNumber = null;
      state.reservationTimer = 0;
    },
    
    // 에러 클리어
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 번호 목록 조회
      .addCase(fetchNumbers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchNumbers.fulfilled, (state, action) => {
        state.loading = false;
        state.numbers = action.payload;
        state.filteredNumbers = action.payload;
        state.error = null;
      })
      .addCase(fetchNumbers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '번호 조회에 실패했습니다.';
      })
      // 번호 검색
      .addCase(searchNumbers.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(searchNumbers.fulfilled, (state, action) => {
        state.loading = false;
        state.filteredNumbers = action.payload;
        state.error = null;
      })
      .addCase(searchNumbers.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '번호 검색에 실패했습니다.';
      })
      // 번호 예약
      .addCase(reserveNumber.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(reserveNumber.fulfilled, (state, action) => {
        state.loading = false;
        state.reservedNumber = action.payload;
        state.reservationTimer = 1800; // 30분 = 1800초
        state.error = null;
      })
      .addCase(reserveNumber.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '번호 예약에 실패했습니다.';
      })
      // 번호 예약 해제
      .addCase(releaseNumber.fulfilled, (state) => {
        state.reservedNumber = null;
        state.reservationTimer = 0;
        state.error = null;
      });
  },
});

export const {
  filterByCategory,
  setSearchPattern,
  setReservationTimer,
  decrementTimer,
  clearReservation,
  clearError,
} = numberSlice.actions;

export default numberSlice.reducer;