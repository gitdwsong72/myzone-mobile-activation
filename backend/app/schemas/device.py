from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class DeviceBase(BaseModel):
    """단말기 기본 스키마"""

    brand: str = Field(..., description="브랜드")
    model: str = Field(..., description="모델명")
    color: str = Field(..., description="색상")
    price: Decimal = Field(..., description="단말기 가격")
    discount_price: Optional[Decimal] = Field(None, description="할인 가격")
    stock_quantity: int = Field(0, description="재고 수량")
    specifications: Optional[Dict[str, Any]] = Field(None, description="상세 스펙")
    description: Optional[str] = Field(None, description="상품 설명")
    image_url: Optional[str] = Field(None, description="대표 이미지 URL")
    image_urls: Optional[List[str]] = Field(None, description="추가 이미지 URL 목록")
    is_active: bool = Field(True, description="판매 활성화 상태")
    is_featured: bool = Field(False, description="추천 상품 여부")
    display_order: int = Field(0, description="표시 순서")
    release_date: Optional[str] = Field(None, description="출시일")


class DeviceCreate(DeviceBase):
    """단말기 생성 스키마"""

    pass


class DeviceUpdate(BaseModel):
    """단말기 수정 스키마"""

    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    price: Optional[Decimal] = None
    discount_price: Optional[Decimal] = None
    stock_quantity: Optional[int] = None
    specifications: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    display_order: Optional[int] = None
    release_date: Optional[str] = None


class DeviceResponse(DeviceBase):
    """단말기 응답 스키마"""

    id: int
    final_price: Decimal = Field(..., description="최종 판매 가격")
    is_in_stock: bool = Field(..., description="재고 보유 여부")
    full_name: str = Field(..., description="전체 상품명")

    class Config:
        from_attributes = True


class DeviceListResponse(BaseModel):
    """단말기 목록 응답 스키마"""

    devices: List[DeviceResponse]
    total: int
    page: int
    size: int
    total_pages: int


class DeviceFilter(BaseModel):
    """단말기 필터링 스키마"""

    brand: Optional[str] = Field(None, description="브랜드 필터")
    min_price: Optional[Decimal] = Field(None, description="최소 가격")
    max_price: Optional[Decimal] = Field(None, description="최대 가격")
    in_stock_only: Optional[bool] = Field(None, description="재고 있는 상품만")
    is_active: Optional[bool] = Field(True, description="활성화 상태 필터")
    is_featured: Optional[bool] = Field(None, description="추천 상품 필터")
    search: Optional[str] = Field(None, description="검색어 (브랜드, 모델명)")


class DeviceImageUpload(BaseModel):
    """단말기 이미지 업로드 스키마"""

    image_url: str = Field(..., description="이미지 URL")
    is_main: bool = Field(False, description="대표 이미지 여부")


class DeviceStockUpdate(BaseModel):
    """재고 수량 업데이트 스키마"""

    stock_quantity: int = Field(..., ge=0, description="재고 수량")


class BrandInfo(BaseModel):
    """브랜드 정보 스키마"""

    brand: str
    device_count: int
    models: List[str]
