from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class PlanBase(BaseModel):
    """요금제 기본 스키마"""
    name: str = Field(..., description="요금제 이름")
    description: Optional[str] = Field(None, description="요금제 설명")
    category: str = Field(..., description="카테고리 (5G, LTE, 데이터중심, 통화중심)")
    monthly_fee: Decimal = Field(..., description="월 요금")
    setup_fee: Decimal = Field(0, description="개통비")
    data_limit: Optional[int] = Field(None, description="데이터 제공량 (MB, null=무제한)")
    call_minutes: Optional[int] = Field(None, description="통화 시간 (분, null=무제한)")
    sms_count: Optional[int] = Field(None, description="문자 개수 (개, null=무제한)")
    additional_services: Optional[str] = Field(None, description="부가 서비스 목록")
    discount_rate: Decimal = Field(0, description="할인율 (%)")
    promotion_text: Optional[str] = Field(None, description="프로모션 문구")
    is_active: bool = Field(True, description="활성화 상태")
    display_order: int = Field(0, description="표시 순서")


class PlanCreate(PlanBase):
    """요금제 생성 스키마"""
    pass


class PlanUpdate(BaseModel):
    """요금제 수정 스키마"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    monthly_fee: Optional[Decimal] = None
    setup_fee: Optional[Decimal] = None
    data_limit: Optional[int] = None
    call_minutes: Optional[int] = None
    sms_count: Optional[int] = None
    additional_services: Optional[str] = None
    discount_rate: Optional[Decimal] = None
    promotion_text: Optional[str] = None
    is_active: Optional[bool] = None
    display_order: Optional[int] = None


class PlanResponse(PlanBase):
    """요금제 응답 스키마"""
    id: int
    discounted_price: Decimal = Field(..., description="할인 적용된 가격")
    
    class Config:
        from_attributes = True


class PlanListResponse(BaseModel):
    """요금제 목록 응답 스키마"""
    plans: List[PlanResponse]
    total: int
    page: int
    size: int
    total_pages: int


class PlanFilter(BaseModel):
    """요금제 필터링 스키마"""
    category: Optional[str] = Field(None, description="카테고리 필터")
    min_price: Optional[Decimal] = Field(None, description="최소 가격")
    max_price: Optional[Decimal] = Field(None, description="최대 가격")
    is_active: Optional[bool] = Field(True, description="활성화 상태 필터")
    search: Optional[str] = Field(None, description="검색어 (이름, 설명)")