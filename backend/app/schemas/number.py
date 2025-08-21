import re
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class NumberBase(BaseModel):
    """전화번호 기본 스키마"""

    number: str = Field(..., description="전화번호")
    category: str = Field(..., description="번호 카테고리")
    additional_fee: Decimal = Field(0, description="번호 추가 요금")
    is_premium: bool = Field(False, description="프리미엄 번호 여부")
    pattern_type: Optional[str] = Field(None, description="패턴 유형")

    @validator("number")
    def validate_number(cls, v):
        # 전화번호 형식 검증 (010-XXXX-XXXX)
        pattern = r"^010-\d{4}-\d{4}$"
        if not re.match(pattern, v):
            raise ValueError("전화번호는 010-XXXX-XXXX 형식이어야 합니다.")
        return v


class NumberCreate(NumberBase):
    """전화번호 생성 스키마"""

    pass


class NumberUpdate(BaseModel):
    """전화번호 수정 스키마"""

    category: Optional[str] = None
    additional_fee: Optional[Decimal] = None
    is_premium: Optional[bool] = None
    pattern_type: Optional[str] = None


class NumberResponse(NumberBase):
    """전화번호 응답 스키마"""

    id: int
    status: str = Field(..., description="상태")
    reserved_until: Optional[datetime] = Field(None, description="예약 만료 시간")
    is_available: bool = Field(..., description="사용 가능 여부")

    class Config:
        from_attributes = True


class NumberListResponse(BaseModel):
    """전화번호 목록 응답 스키마"""

    numbers: List[NumberResponse]
    total: int
    page: int
    size: int
    total_pages: int


class NumberFilter(BaseModel):
    """전화번호 필터링 스키마"""

    category: Optional[str] = Field(None, description="카테고리 필터")
    status: Optional[str] = Field("available", description="상태 필터")
    is_premium: Optional[bool] = Field(None, description="프리미엄 번호 필터")
    pattern_type: Optional[str] = Field(None, description="패턴 유형 필터")
    search: Optional[str] = Field(None, description="번호 검색 (끝자리 또는 패턴)")
    min_fee: Optional[Decimal] = Field(None, description="최소 추가 요금")
    max_fee: Optional[Decimal] = Field(None, description="최대 추가 요금")


class NumberSearchRequest(BaseModel):
    """번호 검색 요청 스키마"""

    pattern: str = Field(..., description="검색 패턴 (끝자리 또는 특정 패턴)")
    category: Optional[str] = Field(None, description="카테고리 필터")
    limit: int = Field(20, ge=1, le=100, description="결과 개수 제한")


class NumberReservationRequest(BaseModel):
    """번호 예약 요청 스키마"""

    order_id: str = Field(..., description="주문 ID")
    minutes: int = Field(30, ge=5, le=60, description="예약 시간 (분)")


class NumberReservationResponse(BaseModel):
    """번호 예약 응답 스키마"""

    number_id: int
    number: str
    reserved_until: datetime
    order_id: str
    message: str


class CategoryInfo(BaseModel):
    """카테고리 정보 스키마"""

    category: str
    count: int
    min_fee: Decimal
    max_fee: Decimal
    description: str


class NumberPatternAnalysis(BaseModel):
    """번호 패턴 분석 스키마"""

    number: str
    pattern_type: str
    is_premium: bool
    score: int = Field(..., description="패턴 점수 (높을수록 좋은 번호)")
    description: str
