import { configureStore } from '@reduxjs/toolkit';

// 슬라이스 import
import authSlice from './slices/authSlice';
import orderSlice from './slices/orderSlice';
import planSlice from './slices/planSlice';
import deviceSlice from './slices/deviceSlice';
import numberSlice from './slices/numberSlice';
import uiSlice from './slices/uiSlice';
import adminSlice from './slices/adminSlice';

export const store = configureStore({
  reducer: {
    auth: authSlice,
    order: orderSlice,
    plans: planSlice,
    devices: deviceSlice,
    numbers: numberSlice,
    ui: uiSlice,
    admin: adminSlice,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;