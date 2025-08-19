from sqlalchemy import Column, String, Date, Text, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel
from ..core.database_encryption import EncryptedString, EncryptedText


class User(BaseModel):
    """사용자 모델"""
    __tablename__ = "users"
    
    # 기본 정보 (민감한 정보는 암호화)
    name = Column(EncryptedString(100), nullable=False, comment="사용자 이름 (암호화)")
    phone = Column(String(20), unique=True, nullable=False, index=True, comment="휴대폰 번호")
    email = Column(String(255), unique=True, nullable=True, index=True, comment="이메일 주소")
    birth_date = Column(Date, nullable=False, comment="생년월일")
    gender = Column(String(10), nullable=False, comment="성별")
    
    # 주소 정보 (암호화)
    address = Column(EncryptedText(), nullable=False, comment="주소 (암호화)")
    
    # 인증 정보
    password_hash = Column(String(255), nullable=True, comment="해시된 비밀번호")
    
    # 인증 상태
    is_verified = Column(Boolean, default=False, nullable=False, comment="본인인증 완료 여부")
    verification_method = Column(String(50), nullable=True, comment="인증 방법")
    
    # 계정 상태
    is_active = Column(Boolean, default=True, nullable=False, comment="계정 활성화 상태")
    
    # 관계 설정
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, phone='{self.phone}')>"
    
    def get_masked_info(self):
        """마스킹된 정보 반환"""
        from ..core.encryption import encryption_service
        return {
            "name": encryption_service.mask_name(self.name),
            "phone": encryption_service.mask_phone_number(self.phone),
            "email": encryption_service.mask_email(self.email) if self.email else None
        }