from sqlalchemy import JSON, Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class Device(BaseModel):
    """단말기 모델"""

    __tablename__ = "devices"

    # 기본 정보
    brand = Column(String(50), nullable=False, index=True, comment="브랜드 (삼성, 애플, LG 등)")
    model = Column(String(100), nullable=False, comment="모델명")
    color = Column(String(50), nullable=False, comment="색상")

    # 가격 정보
    price = Column(Numeric(10, 2), nullable=False, comment="단말기 가격")
    discount_price = Column(Numeric(10, 2), nullable=True, comment="할인 가격")

    # 재고 정보
    stock_quantity = Column(Integer, default=0, nullable=False, comment="재고 수량")

    # 상세 정보
    specifications = Column(JSON, nullable=True, comment="상세 스펙 (JSON)")
    description = Column(Text, nullable=True, comment="상품 설명")

    # 이미지 정보
    image_url = Column(String(500), nullable=True, comment="대표 이미지 URL")
    image_urls = Column(JSON, nullable=True, comment="추가 이미지 URL 목록 (JSON)")

    # 상태
    is_active = Column(Boolean, default=True, nullable=False, comment="판매 활성화 상태")
    is_featured = Column(Boolean, default=False, nullable=False, comment="추천 상품 여부")
    display_order = Column(Integer, default=0, nullable=False, comment="표시 순서")

    # 출시 정보
    release_date = Column(String(20), nullable=True, comment="출시일")

    # 관계 설정
    orders = relationship("Order", back_populates="device")

    def __repr__(self):
        return f"<Device(id={self.id}, brand='{self.brand}', model='{self.model}', color='{self.color}')>"

    @property
    def final_price(self):
        """최종 판매 가격 (할인 적용)"""
        return self.discount_price if self.discount_price else self.price

    @property
    def is_in_stock(self):
        """재고 보유 여부"""
        return self.stock_quantity > 0

    @property
    def full_name(self):
        """전체 상품명"""
        return f"{self.brand} {self.model} ({self.color})"
