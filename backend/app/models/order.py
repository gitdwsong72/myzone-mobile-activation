import enum
import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Order(BaseModel):
    """주문 모델"""

    __tablename__ = "orders"

    # 주문 기본 정보
    order_number = Column(String(50), unique=True, nullable=False, index=True, comment="주문번호")

    # 외래키 관계
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID")
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False, comment="요금제 ID")
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=True, comment="단말기 ID")
    number_id = Column(Integer, ForeignKey("numbers.id"), nullable=True, comment="번호 ID")

    # 주문 상태
    status = Column(String(50), default=OrderStatus.PENDING, nullable=False, index=True, comment="주문 상태")

    # 금액 정보
    total_amount = Column(Numeric(12, 2), nullable=False, comment="총 주문 금액")
    plan_fee = Column(Numeric(10, 2), nullable=False, comment="요금제 비용")
    device_fee = Column(Numeric(10, 2), default=0, nullable=False, comment="단말기 비용")
    setup_fee = Column(Numeric(10, 2), default=0, nullable=False, comment="개통비")
    number_fee = Column(Numeric(10, 2), default=0, nullable=False, comment="번호 추가 요금")

    # 배송 정보
    delivery_address = Column(Text, nullable=True, comment="배송 주소")
    delivery_request = Column(Text, nullable=True, comment="배송 요청사항")
    preferred_delivery_time = Column(String(50), nullable=True, comment="희망 배송 시간")

    # 약관 동의
    terms_agreed = Column(Boolean, default=False, nullable=False, comment="약관 동의 여부")
    privacy_agreed = Column(Boolean, default=False, nullable=False, comment="개인정보 처리 동의")
    marketing_agreed = Column(Boolean, default=False, nullable=False, comment="마케팅 수신 동의")

    # 추가 정보
    notes = Column(Text, nullable=True, comment="주문 메모")

    # 관계 설정
    user = relationship("User", back_populates="orders")
    plan = relationship("Plan", back_populates="orders")
    device = relationship("Device", back_populates="orders")
    number = relationship("Number", back_populates="orders")
    payment = relationship("Payment", back_populates="order", uselist=False)
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.order_number:
            self.order_number = self.generate_order_number()

    def __repr__(self):
        return f"<Order(id={self.id}, order_number='{self.order_number}', status='{self.status}')>"

    @staticmethod
    def generate_order_number():
        """주문번호 생성"""
        import datetime

        now = datetime.datetime.now()
        date_str = now.strftime("%Y%m%d")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"MZ{date_str}{unique_id}"

    def calculate_total_amount(self):
        """총 주문 금액 계산"""
        total = self.plan_fee + self.device_fee + self.setup_fee + self.number_fee
        self.total_amount = total
        return total

    @property
    def is_paid(self):
        """결제 완료 여부"""
        return self.payment and self.payment.status == "completed"

    @property
    def can_cancel(self):
        """취소 가능 여부"""
        return self.status in ["pending", "confirmed"] and not self.is_paid
