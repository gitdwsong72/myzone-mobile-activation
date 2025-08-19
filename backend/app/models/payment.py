from sqlalchemy import Column, String, Integer, ForeignKey, Numeric, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class Payment(BaseModel):
    """결제 모델"""
    __tablename__ = "payments"
    
    # 주문 관계
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, unique=True, comment="주문 ID")
    
    # 결제 기본 정보
    payment_method = Column(String(50), nullable=False, comment="결제 방법 (card, bank_transfer, simple_pay)")
    payment_provider = Column(String(50), nullable=True, comment="결제 제공업체 (kakao_pay, naver_pay 등)")
    
    # 금액 정보
    amount = Column(Numeric(12, 2), nullable=False, comment="결제 금액")
    currency = Column(String(10), default="KRW", nullable=False, comment="통화")
    
    # 결제 상태
    status = Column(String(50), default="pending", nullable=False, index=True,
                   comment="결제 상태 (pending, processing, completed, failed, cancelled, refunded)")
    
    # 외부 결제 정보
    transaction_id = Column(String(100), nullable=True, unique=True, comment="PG사 거래 ID")
    pg_provider = Column(String(50), nullable=True, comment="PG사 (toss, iamport 등)")
    pg_transaction_id = Column(String(100), nullable=True, comment="PG사 내부 거래 ID")
    
    # 카드 정보 (토큰화된 정보만 저장)
    card_company = Column(String(50), nullable=True, comment="카드사")
    card_number_masked = Column(String(20), nullable=True, comment="마스킹된 카드번호")
    installment_months = Column(Integer, default=0, nullable=False, comment="할부 개월수 (0=일시불)")
    
    # 결제 시간 정보
    paid_at = Column(DateTime, nullable=True, comment="결제 완료 시간")
    failed_at = Column(DateTime, nullable=True, comment="결제 실패 시간")
    cancelled_at = Column(DateTime, nullable=True, comment="결제 취소 시간")
    
    # 실패/취소 정보
    failure_reason = Column(Text, nullable=True, comment="결제 실패 사유")
    cancel_reason = Column(Text, nullable=True, comment="결제 취소 사유")
    
    # 환불 정보
    refund_amount = Column(Numeric(12, 2), default=0, nullable=False, comment="환불 금액")
    refund_reason = Column(Text, nullable=True, comment="환불 사유")
    refunded_at = Column(DateTime, nullable=True, comment="환불 완료 시간")
    
    # 부가 정보
    receipt_url = Column(String(500), nullable=True, comment="영수증 URL")
    notes = Column(Text, nullable=True, comment="결제 메모")
    
    # 관계 설정
    order = relationship("Order", back_populates="payment")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_id={self.order_id}, status='{self.status}', amount={self.amount})>"
    
    @property
    def is_completed(self):
        """결제 완료 여부"""
        return self.status == "completed"
    
    @property
    def is_refundable(self):
        """환불 가능 여부"""
        return self.status == "completed" and self.refund_amount < self.amount
    
    @property
    def remaining_refund_amount(self):
        """남은 환불 가능 금액"""
        return self.amount - self.refund_amount if self.is_refundable else 0