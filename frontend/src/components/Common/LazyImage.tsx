import React, { useState, useRef, useEffect } from 'react';
import './LazyImage.css';

interface LazyImageProps {
  src: string;
  alt: string;
  className?: string;
  placeholder?: string;
  width?: number | string;
  height?: number | string;
  onLoad?: () => void;
  onError?: () => void;
}

const LazyImage: React.FC<LazyImageProps> = ({
  src,
  alt,
  className = '',
  placeholder = '/images/placeholder.jpg',
  width,
  height,
  onLoad,
  onError
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const [hasError, setHasError] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        threshold: 0.1,
        rootMargin: '50px'
      }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    onError?.();
  };

  return (
    <div 
      className={`lazy-image-container ${className}`}
      style={{ width, height }}
    >
      {/* 플레이스홀더 */}
      {!isLoaded && !hasError && (
        <div className="lazy-image-placeholder">
          <div className="lazy-image-skeleton" />
        </div>
      )}

      {/* 실제 이미지 */}
      <img
        ref={imgRef}
        src={isInView ? src : undefined}
        alt={alt}
        className={`lazy-image ${isLoaded ? 'loaded' : ''} ${hasError ? 'error' : ''}`}
        onLoad={handleLoad}
        onError={handleError}
        loading="lazy"
        decoding="async"
        style={{ width, height }}
      />

      {/* 에러 상태 */}
      {hasError && (
        <div className="lazy-image-error">
          <span>이미지를 불러올 수 없습니다</span>
        </div>
      )}
    </div>
  );
};

export default LazyImage;