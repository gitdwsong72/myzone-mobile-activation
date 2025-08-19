from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from enum import Enum

class Token(BaseModel):
    """토큰 응답 모델"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class TokenData(BaseModel):
    """토큰 데이터 모델"""
    user_id: Optional[int] = None

class UserLogin(BaseModel):
    """사용자 로그인 요청 모델"""
    phone: str
    password: str

class AdminLogin(BaseModel):
    """관리자 로그인 요청 모델"""
    username: str
    password: str

class RefreshTokenRequest(BaseModel):
    """리프레시 토큰 요청 모델"""
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 모델"""
    current_password: str
    new_password: str

class ResetPasswordRequest(BaseModel):
    """비밀번호 재설정 요청 모델"""
    phone: str
    verification_code: str
    new_password: str

class SMSVerificationRequest(BaseModel):
    """SMS 인증 요청 모델"""
    phone: str

class SMSVerificationConfirm(BaseModel):
    """SMS 인증 확인 모델"""
    phone: str
    verification_code: str

class AuthResponse(BaseModel):
    """인증 응답 기본 모델"""
    success: bool
    message: str
    data: Optional[dict] = None


class AdminRole(str, Enum):
    """관리자 역할"""
    OPERATOR = "operator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AdminCreate(BaseModel):
    """관리자 생성 스키마"""
    username: str
    email: EmailStr
    password: str
    role: AdminRole = AdminRole.ADMIN
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('사용자명은 3자 이상이어야 합니다.')
        if len(v) > 50:
            raise ValueError('사용자명은 50자 이하여야 합니다.')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v


class AdminUpdate(BaseModel):
    """관리자 수정 스키마"""
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[AdminRole] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v and len(v) < 8:
            raise ValueError('비밀번호는 8자 이상이어야 합니다.')
        return v