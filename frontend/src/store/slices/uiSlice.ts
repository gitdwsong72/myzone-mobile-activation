import { createSlice, PayloadAction } from '@reduxjs/toolkit';

// UI 상태 타입 정의
interface UIState {
  // 로딩 상태
  globalLoading: boolean;
  
  // 모달 상태
  modals: {
    [key: string]: boolean;
  };
  
  // 토스트 알림
  toasts: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    duration?: number;
  }>;
  
  // 사이드바 상태
  sidebarOpen: boolean;
  
  // 모바일 메뉴 상태
  mobileMenuOpen: boolean;
  
  // 현재 화면 크기
  screenSize: 'mobile' | 'tablet' | 'desktop';
  
  // 테마
  theme: 'light' | 'dark';
}

const initialState: UIState = {
  globalLoading: false,
  modals: {},
  toasts: [],
  sidebarOpen: false,
  mobileMenuOpen: false,
  screenSize: 'desktop',
  theme: 'light',
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // 전역 로딩 상태 설정
    setGlobalLoading: (state, action: PayloadAction<boolean>) => {
      state.globalLoading = action.payload;
    },
    
    // 모달 열기
    openModal: (state, action: PayloadAction<string>) => {
      state.modals[action.payload] = true;
    },
    
    // 모달 닫기
    closeModal: (state, action: PayloadAction<string>) => {
      state.modals[action.payload] = false;
    },
    
    // 모든 모달 닫기
    closeAllModals: (state) => {
      state.modals = {};
    },
    
    // 토스트 추가
    addToast: (state, action: PayloadAction<{
      type: 'success' | 'error' | 'warning' | 'info';
      message: string;
      duration?: number;
    }>) => {
      const toast = {
        id: Date.now().toString(),
        ...action.payload,
      };
      state.toasts.push(toast);
    },
    
    // 토스트 제거
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter(toast => toast.id !== action.payload);
    },
    
    // 모든 토스트 제거
    clearToasts: (state) => {
      state.toasts = [];
    },
    
    // 사이드바 토글
    toggleSidebar: (state) => {
      state.sidebarOpen = !state.sidebarOpen;
    },
    
    // 사이드바 설정
    setSidebar: (state, action: PayloadAction<boolean>) => {
      state.sidebarOpen = action.payload;
    },
    
    // 모바일 메뉴 토글
    toggleMobileMenu: (state) => {
      state.mobileMenuOpen = !state.mobileMenuOpen;
    },
    
    // 모바일 메뉴 설정
    setMobileMenu: (state, action: PayloadAction<boolean>) => {
      state.mobileMenuOpen = action.payload;
    },
    
    // 화면 크기 설정
    setScreenSize: (state, action: PayloadAction<'mobile' | 'tablet' | 'desktop'>) => {
      state.screenSize = action.payload;
    },
    
    // 테마 설정
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    
    // 테마 토글
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
  },
});

export const {
  setGlobalLoading,
  openModal,
  closeModal,
  closeAllModals,
  addToast,
  removeToast,
  clearToasts,
  toggleSidebar,
  setSidebar,
  toggleMobileMenu,
  setMobileMenu,
  setScreenSize,
  setTheme,
  toggleTheme,
} = uiSlice.actions;

export default uiSlice.reducer;