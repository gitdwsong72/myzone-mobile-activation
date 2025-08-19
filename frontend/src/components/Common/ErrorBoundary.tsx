import React, { Component, ErrorInfo, ReactNode } from 'react';
import Button from './Button';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="error-boundary">
          <div className="error-content">
            <div className="error-icon">⚠️</div>
            <h2 className="error-title">문제가 발생했습니다</h2>
            <p className="error-message">
              예상치 못한 오류가 발생했습니다. 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.
            </p>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary>오류 상세 정보</summary>
                <pre className="error-stack">
                  {this.state.error.toString()}
                  {this.state.error.stack}
                </pre>
              </details>
            )}
            
            <div className="error-actions">
              <Button onClick={this.handleRetry} variant="primary">
                다시 시도
              </Button>
              <Button 
                onClick={() => window.location.reload()} 
                variant="secondary"
              >
                페이지 새로고침
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// 함수형 컴포넌트용 에러 처리 훅
export const useErrorHandler = () => {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = () => setError(null);

  const handleError = React.useCallback((error: Error) => {
    console.error('Error caught by useErrorHandler:', error);
    setError(error);
  }, []);

  React.useEffect(() => {
    if (error) {
      throw error;
    }
  }, [error]);

  return { handleError, resetError };
};

// 에러 표시 컴포넌트
interface ErrorDisplayProps {
  error?: Error | string;
  title?: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  title = '오류가 발생했습니다',
  onRetry,
  showRetry = true,
}) => {
  const errorMessage = typeof error === 'string' ? error : error?.message || '알 수 없는 오류가 발생했습니다.';

  return (
    <div className="error-display">
      <div className="error-content">
        <div className="error-icon">❌</div>
        <h3 className="error-title">{title}</h3>
        <p className="error-message">{errorMessage}</p>
        
        {showRetry && onRetry && (
          <div className="error-actions">
            <Button onClick={onRetry} variant="primary">
              다시 시도
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ErrorBoundary;