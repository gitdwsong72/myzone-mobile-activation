import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router-dom';
import { RootState, AppDispatch } from '../../store/store';
import { adminLogin, clearError } from '../../store/slices/adminSlice';
import Button from '../../components/Common/Button';
import LoadingSpinner from '../../components/Common/LoadingSpinner';
import './AdminLogin.css';

const AdminLogin: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { loading, error, isAuthenticated } = useSelector((state: RootState) => state.admin);

  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/admin/dashboard');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    // 컴포넌트 마운트 시 에러 클리어
    dispatch(clearError());
  }, [dispatch]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.username.trim() || !formData.password.trim()) {
      return;
    }

    try {
      await dispatch(adminLogin(formData)).unwrap();
    } catch (error) {
      console.error('로그인 실패:', error);
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="admin-login">
      <div className="admin-login__container">
        <div className="admin-login__header">
          <div className="admin-login__logo">
            <h1>MyZone</h1>
            <span>관리자</span>
          </div>
          <h2>관리자 로그인</h2>
          <p>관리자 계정으로 로그인하여 시스템을 관리하세요</p>
        </div>

        <form className="admin-login__form" onSubmit={handleSubmit}>
          {error && (
            <div className="admin-login__error">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">사용자명</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="관리자 사용자명을 입력하세요"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <div className="password-input">
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="비밀번호를 입력하세요"
                required
                disabled={loading}
              />
              <button
                type="button"
                className="password-toggle"
                onClick={togglePasswordVisibility}
                disabled={loading}
              >
                {showPassword ? '🙈' : '👁️'}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            variant="primary"
            size="large"
            disabled={loading || !formData.username.trim() || !formData.password.trim()}
            className="admin-login__submit"
          >
            {loading ? <LoadingSpinner size="small" /> : '로그인'}
          </Button>
        </form>

        <div className="admin-login__footer">
          <p>
            <span className="security-icon">🔒</span>
            보안을 위해 관리자 계정 정보를 안전하게 관리하세요
          </p>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;