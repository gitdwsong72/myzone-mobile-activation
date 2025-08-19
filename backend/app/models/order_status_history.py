from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class OrderStatusHistory(BaseModel):
    """주문 상태 변경 이력 모델"""
    __tablename__ = "order_status_history"
    
    # 주문 관계
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True, comment="주문 ID")
    
    # 상태 정보
    status = Column(String(50), nullable=False, comment="변경된 상태")
    previous_status = Column(String(50), nullable=True, comment="이전 상태")
    
    # 처리 정보
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=True, comment="처리한 관리자 ID")
    note = Column(Text, nullable=True, comment="상태 변경 메모")
    
    # 자동/수동 처리 구분
    is_automatic = Column(String(10), default="false", nullable=False, comment="자동 처리 여부")
    
    # 관계 설정
    order = relationship("Order", back_populates="status_history")
    admin = relationship("Admin", back_populates="order_histories")
    
    def __repr__(self):
        return f"<OrderStatusHistory(id={self.id}, order_id={self.order_id}, status='{self.status}')>"