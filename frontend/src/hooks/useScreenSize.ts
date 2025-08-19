import { useState, useEffect } from 'react';
import { useAppDispatch } from '../store/hooks';
import { setScreenSize } from '../store/slices/uiSlice';

type ScreenSize = 'mobile' | 'tablet' | 'desktop';

const getScreenSize = (width: number): ScreenSize => {
  if (width < 768) return 'mobile';
  if (width < 1024) return 'tablet';
  return 'desktop';
};

export const useScreenSize = () => {
  const dispatch = useAppDispatch();
  const [screenSize, setLocalScreenSize] = useState<ScreenSize>(() => 
    getScreenSize(window.innerWidth)
  );

  useEffect(() => {
    const handleResize = () => {
      const newSize = getScreenSize(window.innerWidth);
      setLocalScreenSize(newSize);
      dispatch(setScreenSize(newSize));
    };

    // 초기 화면 크기 설정
    dispatch(setScreenSize(screenSize));

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [dispatch, screenSize]);

  return {
    screenSize,
    isMobile: screenSize === 'mobile',
    isTablet: screenSize === 'tablet',
    isDesktop: screenSize === 'desktop',
    isMobileOrTablet: screenSize === 'mobile' || screenSize === 'tablet',
  };
};