from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class PaymentBase(BaseModel):
    """결제 기본 스키마"""
    order_id: int = Field(..., description="주문 ID")
    payment_method: str = Field(..., description="결제 방법")
    amount: Decimal = Field(..., description="결제 금액")


class PaymentCreate(PaymentBase):
    """결제 생성 스키마"""
    pass


class PaymentUpdate(BaseModel):
    """결제 수정 스키마"""
    status: Optional[str] = None
    transaction_id: Optional[str] = None
    failure_reason: Optional[str] = None


class PaymentResponse(BaseModel):
    """결제 응답 스키마"""
    id: int
    order_id: int
    payment_method: str
    amount: Decimal
    status: str
    transaction_id: Optional[str]
    failure_reason: Optional[str]
    paid_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """결제 목록 응답 스키마"""
    payments: List[PaymentResponse]
    total: int
    page: int
    size: int
    total_pages: int