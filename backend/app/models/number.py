from datetime import datetime, timedelta
from sqlalchemy import Column, String, Numeric, DateTime, Boolean, Index
from sqlalchemy.orm import relationship
from .base import BaseModel


class Number(BaseModel):
    """전화번호 모델"""
    __tablename__ = "numbers"
    
    # 번호 정보
    number = Column(String(20), unique=True, nullable=False, index=True, comment="전화번호")
    category = Column(String(50), nullable=False, index=True, comment="번호 카테고리 (일반, 연속, 특별)")
    
    # 가격 정보
    additional_fee = Column(Numeric(10, 2), default=0, nullable=False, comment="번호 추가 요금")
    
    # 상태 관리
    status = Column(String(20), default="available", nullable=False, index=True, comment="상태 (available, reserved, assigned)")
    
    # 예약 정보
    reserved_until = Column(DateTime, nullable=True, comment="예약 만료 시간")
    reserved_by_order_id = Column(String(50), nullable=True, comment="예약한 주문 ID")
    
    # 번호 특성
    is_premium = Column(Boolean, default=False, nullable=False, comment="프리미엄 번호 여부")
    pattern_type = Column(String(50), nullable=True, comment="패턴 유형 (연속, 반복, 대칭 등)")
    
    # 관계 설정
    orders = relationship("Order", back_populates="number")
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_number_status_category', 'status', 'category'),
        Index('idx_number_reserved_until', 'reserved_until'),
    )
    
    def __repr__(self):
        return f"<Number(id={self.id}, number='{self.number}', status='{self.status}')>"
    
    @property
    def is_available(self):
        """사용 가능한 번호인지 확인"""
        if self.status != "available":
            return False
        
        # 예약 만료 시간이 지났으면 available로 변경
        if self.reserved_until and self.reserved_until < datetime.utcnow():
            self.status = "available"
            self.reserved_until = None
            self.reserved_by_order_id = None
            return True
            
        return self.reserved_until is None
    
    def reserve(self, order_id: str, minutes: int = 30):
        """번호 예약"""
        if not self.is_available:
            raise ValueError("이미 예약되었거나 사용 중인 번호입니다.")
        
        self.status = "reserved"
        self.reserved_until = datetime.utcnow() + timedelta(minutes=minutes)
        self.reserved_by_order_id = order_id
    
    def assign(self):
        """번호 할당 (개통 완료)"""
        self.status = "assigned"
        self.reserved_until = None
        self.reserved_by_order_id = None
    
    def release(self):
        """번호 해제 (다시 사용 가능하게)"""
        self.status = "available"
        self.reserved_until = None
        self.reserved_by_order_id = None