import React, { PropsWithChildren } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { configureStore, PreloadedState } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';

import { RootState, store } from './store/store';
import authSlice from './store/slices/authSlice';
import orderSlice from './store/slices/orderSlice';
import planSlice from './store/slices/planSlice';
import deviceSlice from './store/slices/deviceSlice';
import numberSlice from './store/slices/numberSlice';
import uiSlice from './store/slices/uiSlice';
import adminSlice from './store/slices/adminSlice';

// This type interface extends the default options for render from RTL, as well
// as allows the user to specify other things such as initialState, store.
interface ExtendedRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  preloadedState?: PreloadedState<RootState>;
  store?: typeof store;
}

export function renderWithProviders(
  ui: React.ReactElement,
  {
    preloadedState = {},
    // Automatically create a store instance if no store was passed in
    store = configureStore({
      reducer: {
        auth: authSlice,
        order: orderSlice,
        plans: planSlice,
        devices: deviceSlice,
        numbers: numberSlice,
        ui: uiSlice,
        admin: adminSlice,
      },
      preloadedState,
    }),
    ...renderOptions
  }: ExtendedRenderOptions = {}
) {
  function Wrapper({ children }: PropsWithChildren<{}>): JSX.Element {
    return (
      <Provider store={store}>
        <BrowserRouter basename={process.env.PUBLIC_URL}>
          {children}
        </BrowserRouter>
      </Provider>
    );
  }

  // Return an object with the store and all of RTL's query functions
  return { store, ...render(ui, { wrapper: Wrapper, ...renderOptions }) };
}

// Mock data for testing
export const mockUser = {
  id: 1,
  name: '홍길동',
  phone: '010-1234-5678',
  email: 'hong@example.com',
  birth_date: '1990-01-01',
  gender: 'M',
  address: '서울시 강남구 테헤란로 123',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z'
};

export const mockPlan = {
  id: 1,
  name: '5G 프리미엄',
  description: '무제한 데이터 요금제',
  monthly_fee: 55000,
  data_limit: -1,
  call_minutes: -1,
  sms_count: -1,
  category: '5G',
  is_active: true,
  created_at: '2023-01-01T00:00:00Z'
};

export const mockDevice = {
  id: 1,
  brand: 'Samsung',
  model: 'Galaxy S24',
  color: 'Black',
  price: 1200000,
  stock_quantity: 10,
  specifications: '6.2인치, 256GB, 12GB RAM',
  image_url: '/images/galaxy-s24-black.jpg',
  is_active: true,
  created_at: '2023-01-01T00:00:00Z'
};

export const mockNumber = {
  id: 1,
  number: '010-1111-2222',
  category: '일반',
  additional_fee: 0,
  status: 'available',
  created_at: '2023-01-01T00:00:00Z'
};

export const mockOrder = {
  id: 1,
  order_number: 'ORD123456789',
  user_id: 1,
  plan_id: 1,
  device_id: 1,
  number_id: 1,
  status: 'pending',
  total_amount: 1255000,
  delivery_address: '서울시 강남구 테헤란로 123',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  user: mockUser,
  plan: mockPlan,
  device: mockDevice,
  number: mockNumber
};

export const mockAdmin = {
  id: 1,
  username: 'admin',
  email: 'admin@myzone.com',
  role: 'admin',
  last_login: '2023-01-01T00:00:00Z',
  created_at: '2023-01-01T00:00:00Z'
};

// Re-export everything
export * from '@testing-library/react';