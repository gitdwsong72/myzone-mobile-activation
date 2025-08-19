from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


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


class AdminResponse(BaseModel):
    """관리자 응답 스키마"""
    id: int
    username: str
    email: str
    role: str
    full_name: Optional[str]
    department: Optional[str]
    phone: Optional[str]
    is_active: bool
    last_login: Optional[datetime]
    login_count: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class AdminListResponse(BaseModel):
    """관리자 목록 응답 스키마"""
    admins: List[AdminResponse]
    total: int
    skip: int
    limit: int


class AdminActivityLogResponse(BaseModel):
    """관리자 활동 로그 응답 스키마"""
    id: int
    admin_id: int
    admin_username: Optional[str]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[int]
    method: Optional[str]
    endpoint: Optional[str]
    ip_address: Optional[str]
    description: Optional[str]
    success: str
    error_message: Optional[str]
    created_at: datetime


class AdminActivityLogListResponse(BaseModel):
    """관리자 활동 로그 목록 응답 스키마"""
    logs: List[AdminActivityLogResponse]
    total: int
    skip: int
    limit: int


class AdminDashboardResponse(BaseModel):
    """관리자 대시보드 응답 스키마"""
    overview: Dict[str, int]
    order_status: Dict[str, int]
    recent_orders: List[Dict[str, Any]]
    popular_plans: List[Dict[str, Any]]


class AdminPermissionResponse(BaseModel):
    """관리자 권한 응답 스키마"""
    admin_id: int
    role: str
    permissions: List[str]


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청 스키마"""
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('새 비밀번호는 8자 이상이어야 합니다.')
        return v


class AdminLoginRequest(BaseModel):
    """관리자 로그인 요청 스키마"""
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    """관리자 로그인 응답 스키마"""
    admin: AdminResponse
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AdminSessionResponse(BaseModel):
    """관리자 세션 정보 응답 스키마"""
    admin_id: int
    username: str
    role: str
    permissions: List[str]
    last_login: Optional[datetime]
    session_expires_at: Optional[datetime]