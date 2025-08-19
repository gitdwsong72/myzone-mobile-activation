import { useState, useEffect, useRef, RefObject } from 'react';

interface TouchPosition {
  x: number;
  y: number;
}

interface SwipeDirection {
  direction: 'left' | 'right' | 'up' | 'down' | null;
  distance: number;
}

export const useTouch = (elementRef?: RefObject<HTMLElement>) => {
  const [isTouch, setIsTouch] = useState(false);
  const [touchStart, setTouchStart] = useState<TouchPosition | null>(null);
  const [touchEnd, setTouchEnd] = useState<TouchPosition | null>(null);
  const [swipe, setSwipe] = useState<SwipeDirection>({ direction: null, distance: 0 });

  // 터치 지원 감지
  useEffect(() => {
    const checkTouch = () => {
      setIsTouch('ontouchstart' in window || navigator.maxTouchPoints > 0);
    };

    checkTouch();
    window.addEventListener('resize', checkTouch);
    return () => window.removeEventListener('resize', checkTouch);
  }, []);

  // 스와이프 감지
  useEffect(() => {
    if (!touchStart || !touchEnd) return;

    const distanceX = touchStart.x - touchEnd.x;
    const distanceY = touchStart.y - touchEnd.y;
    const isLeftSwipe = distanceX > 50;
    const isRightSwipe = distanceX < -50;
    const isUpSwipe = distanceY > 50;
    const isDownSwipe = distanceY < -50;

    let direction: SwipeDirection['direction'] = null;
    let distance = 0;

    if (Math.abs(distanceX) > Math.abs(distanceY)) {
      // 수평 스와이프
      if (isLeftSwipe) {
        direction = 'left';
        distance = Math.abs(distanceX);
      } else if (isRightSwipe) {
        direction = 'right';
        distance = Math.abs(distanceX);
      }
    } else {
      // 수직 스와이프
      if (isUpSwipe) {
        direction = 'up';
        distance = Math.abs(distanceY);
      } else if (isDownSwipe) {
        direction = 'down';
        distance = Math.abs(distanceY);
      }
    }

    setSwipe({ direction, distance });
  }, [touchStart, touchEnd]);

  const handleTouchStart = (e: Event) => {
    const touchEvent = e as TouchEvent;
    setTouchEnd(null);
    setTouchStart({
      x: touchEvent.targetTouches[0].clientX,
      y: touchEvent.targetTouches[0].clientY,
    });
  };

  const handleTouchMove = (e: Event) => {
    const touchEvent = e as TouchEvent;
    setTouchEnd({
      x: touchEvent.targetTouches[0].clientX,
      y: touchEvent.targetTouches[0].clientY,
    });
  };

  const handleTouchEnd = () => {
    if (!touchStart) return;
    // touchEnd는 touchMove에서 설정됨
  };

  // 이벤트 리스너 등록
  useEffect(() => {
    const element = elementRef?.current || document;

    if (isTouch) {
      element.addEventListener('touchstart', handleTouchStart, { passive: true });
      element.addEventListener('touchmove', handleTouchMove, { passive: true });
      element.addEventListener('touchend', handleTouchEnd, { passive: true });

      return () => {
        element.removeEventListener('touchstart', handleTouchStart);
        element.removeEventListener('touchmove', handleTouchMove);
        element.removeEventListener('touchend', handleTouchEnd);
      };
    }
  }, [isTouch, elementRef]);

  return {
    isTouch,
    swipe,
    touchStart,
    touchEnd,
    resetSwipe: () => setSwipe({ direction: null, distance: 0 }),
  };
};

// 길게 누르기 감지 훅
export const useLongPress = (
  callback: () => void,
  duration: number = 500
) => {
  const [isPressed, setIsPressed] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const start = () => {
    setIsPressed(true);
    timeoutRef.current = setTimeout(() => {
      callback();
    }, duration);
  };

  const stop = () => {
    setIsPressed(false);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  };

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    isPressed,
    handlers: {
      onMouseDown: start,
      onMouseUp: stop,
      onMouseLeave: stop,
      onTouchStart: start,
      onTouchEnd: stop,
    },
  };
};