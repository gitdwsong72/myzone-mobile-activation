from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base import BaseModel


class Admin(BaseModel):
    """관리자 모델"""
    __tablename__ = "admins"
    
    # 기본 정보
    username = Column(String(50), unique=True, nullable=False, index=True, comment="관리자 아이디")
    email = Column(String(255), unique=True, nullable=False, comment="이메일")
    
    # 인증 정보
    password_hash = Column(String(255), nullable=False, comment="해시된 비밀번호")
    
    # 권한 정보
    role = Column(String(50), default="admin", nullable=False, comment="역할 (admin, super_admin, operator)")
    
    # 상태 정보
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")
    is_superuser = Column(Boolean, default=False, nullable=False, comment="슈퍼유저 여부")
    
    # 로그인 정보
    last_login = Column(DateTime, nullable=True, comment="마지막 로그인 시간")
    login_count = Column(String(10), default="0", nullable=False, comment="로그인 횟수")
    
    # 추가 정보
    full_name = Column(String(100), nullable=True, comment="실명")
    department = Column(String(100), nullable=True, comment="부서")
    phone = Column(String(20), nullable=True, comment="연락처")
    
    # 관계 설정
    order_histories = relationship("OrderStatusHistory", back_populates="admin")
    
    def __repr__(self):
        return f"<Admin(id={self.id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_super_admin(self):
        """슈퍼 관리자 여부"""
        return self.role == "super_admin" or self.is_superuser
    
    @property
    def can_manage_orders(self):
        """주문 관리 권한 여부"""
        return self.role in ["admin", "super_admin", "operator"] and self.is_active
    
    @property
    def can_manage_users(self):
        """사용자 관리 권한 여부"""
        return self.role in ["admin", "super_admin"] and self.is_active
    
    @property
    def can_view_statistics(self):
        """통계 조회 권한 여부"""
        return self.role in ["admin", "super_admin"] and self.is_active