import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import api from '../../services/api';

// 단말기 타입 정의
interface Device {
  id: number;
  brand: string;
  model: string;
  color: string;
  price: number;
  stockQuantity: number;
  specifications: string;
  imageUrl: string;
  isActive: boolean;
}

interface DeviceState {
  devices: Device[];
  filteredDevices: Device[];
  selectedBrand: string;
  loading: boolean;
  error: string | null;
}

const initialState: DeviceState = {
  devices: [],
  filteredDevices: [],
  selectedBrand: 'all',
  loading: false,
  error: null,
};

// 비동기 액션: 단말기 목록 조회
export const fetchDevices = createAsyncThunk('devices/fetchDevices', async () => {
  const response = await api.get('/devices');
  return response.data;
});

// 비동기 액션: 단말기 상세 조회
export const fetchDeviceById = createAsyncThunk(
  'devices/fetchDeviceById',
  async (deviceId: number) => {
    const response = await api.get(`/devices/${deviceId}`);
    return response.data;
  }
);

const deviceSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    // 브랜드별 필터링
    filterByBrand: (state, action) => {
      const brand = action.payload;
      state.selectedBrand = brand;
      
      if (brand === 'all') {
        state.filteredDevices = state.devices;
      } else {
        state.filteredDevices = state.devices.filter(device => device.brand === brand);
      }
    },
    
    // 에러 클리어
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // 단말기 목록 조회
      .addCase(fetchDevices.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.loading = false;
        state.devices = action.payload;
        state.filteredDevices = action.payload;
        state.error = null;
      })
      .addCase(fetchDevices.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '단말기 조회에 실패했습니다.';
      })
      // 단말기 상세 조회
      .addCase(fetchDeviceById.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchDeviceById.fulfilled, (state, action) => {
        state.loading = false;
        state.error = null;
      })
      .addCase(fetchDeviceById.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '단말기 상세 조회에 실패했습니다.';
      });
  },
});

export const { filterByBrand, clearError } = deviceSlice.actions;
export default deviceSlice.reducer;