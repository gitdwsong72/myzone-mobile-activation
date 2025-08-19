from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field

from .user import UserResponse
from .plan import PlanResponse
from .device import DeviceResponse
from .number import NumberResponse
from .payment import PaymentResponse


class OrderBase(BaseModel):
    """주문 기본 스키마"""
    user_id: int = Field(..., description="사용자 ID")
    plan_id: int = Field(..., description="요금제 ID")
    device_id: Optional[int] = Field(None, description="단말기 ID")
    number_id: Optional[int] = Field(None, description="번호 ID")
    delivery_address: Optional[str] = Field(None, description="배송 주소")
    delivery_request: Optional[str] = Field(None, description="배송 요청사항")
    preferred_delivery_time: Optional[str] = Field(None, description="희망 배송 시간")
    terms_agreed: bool = Field(..., description="약관 동의 여부")
    privacy_agreed: bool = Field(..., description="개인정보 처리 동의")
    marketing_agreed: bool = Field(False, description="마케팅 수신 동의")
    notes: Optional[str] = Field(None, description="주문 메모")


class OrderCreate(OrderBase):
    """주문 생성 스키마"""
    pass


class OrderUpdate(BaseModel):
    """주문 수정 스키마"""
    device_id: Optional[int] = None
    number_id: Optional[int] = None
    delivery_address: Optional[str] = None
    delivery_request: Optional[str] = None
    preferred_delivery_time: Optional[str] = None
    notes: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """주문 상태 변경 스키마"""
    status: str = Field(..., description="변경할 상태")
    note: Optional[str] = Field(None, description="상태 변경 메모")


class OrderStatusHistoryResponse(BaseModel):
    """주문 상태 이력 응답 스키마"""
    id: int
    status: str
    previous_status: Optional[str]
    note: Optional[str]
    is_automatic: str
    admin_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """주문 응답 스키마"""
    id: int
    order_number: str
    status: str
    total_amount: Decimal
    plan_fee: Decimal
    device_fee: Decimal
    setup_fee: Decimal
    number_fee: Decimal
    delivery_address: Optional[str]
    delivery_request: Optional[str]
    preferred_delivery_time: Optional[str]
    terms_agreed: bool
    privacy_agreed: bool
    marketing_agreed: bool
    notes: Optional[str]
    is_paid: bool
    can_cancel: bool
    created_at: datetime
    updated_at: datetime
    
    # 관계 데이터
    user: Optional[UserResponse] = None
    plan: Optional[PlanResponse] = None
    device: Optional[DeviceResponse] = None
    number: Optional[NumberResponse] = None
    payment: Optional[PaymentResponse] = None
    status_history: List[OrderStatusHistoryResponse] = []
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """주문 목록 응답 스키마"""
    orders: List[OrderResponse]
    total: int
    page: int
    size: int
    total_pages: int


class OrderSummaryResponse(BaseModel):
    """주문 요약 응답 스키마"""
    id: int
    order_number: str
    status: str
    total_amount: Decimal
    user_name: str
    plan_name: str
    device_name: Optional[str]
    number: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderFilter(BaseModel):
    """주문 필터링 스키마"""
    status: Optional[str] = Field(None, description="상태 필터")
    user_id: Optional[int] = Field(None, description="사용자 ID 필터")
    plan_id: Optional[int] = Field(None, description="요금제 ID 필터")
    device_id: Optional[int] = Field(None, description="단말기 ID 필터")
    is_paid: Optional[bool] = Field(None, description="결제 완료 여부 필터")
    date_from: Optional[datetime] = Field(None, description="시작 날짜")
    date_to: Optional[datetime] = Field(None, description="종료 날짜")
    search: Optional[str] = Field(None, description="검색어 (주문번호, 사용자명)")


class OrderStatusStats(BaseModel):
    """주문 상태 통계 스키마"""
    status: str
    count: int
    percentage: float


class OrderDashboard(BaseModel):
    """주문 대시보드 스키마"""
    total_orders: int
    pending_orders: int
    processing_orders: int
    completed_orders: int
    cancelled_orders: int
    today_orders: int
    total_revenue: Decimal
    status_stats: List[OrderStatusStats]