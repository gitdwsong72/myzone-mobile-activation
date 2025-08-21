from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Plan(BaseModel):
    """요금제 모델"""

    __tablename__ = "plans"

    # 기본 정보
    name = Column(String(100), nullable=False, comment="요금제 이름")
    description = Column(Text, nullable=True, comment="요금제 설명")
    category = Column(String(50), nullable=False, index=True, comment="카테고리 (5G, LTE, 데이터중심, 통화중심)")

    # 요금 정보
    monthly_fee = Column(Numeric(10, 2), nullable=False, comment="월 요금")
    setup_fee = Column(Numeric(10, 2), default=0, nullable=False, comment="개통비")

    # 서비스 제공량
    data_limit = Column(Integer, nullable=True, comment="데이터 제공량 (MB, NULL=무제한)")
    call_minutes = Column(Integer, nullable=True, comment="통화 시간 (분, NULL=무제한)")
    sms_count = Column(Integer, nullable=True, comment="문자 개수 (개, NULL=무제한)")

    # 부가 서비스
    additional_services = Column(Text, nullable=True, comment="부가 서비스 목록 (JSON)")

    # 할인 정보
    discount_rate = Column(Numeric(5, 2), default=0, nullable=False, comment="할인율 (%)")
    promotion_text = Column(String(200), nullable=True, comment="프로모션 문구")

    # 상태
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")
    display_order = Column(Integer, default=0, nullable=False, comment="표시 순서")

    # 관계 설정
    orders = relationship("Order", back_populates="plan")

    def __repr__(self):
        return f"<Plan(id={self.id}, name='{self.name}', monthly_fee={self.monthly_fee})>"

    @property
    def discounted_price(self):
        """할인 적용된 가격 계산"""
        if self.discount_rate > 0:
            return self.monthly_fee * (1 - self.discount_rate / 100)
        return self.monthly_fee
