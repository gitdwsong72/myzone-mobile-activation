import math
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_admin
from ...models.admin import Admin
from ...schemas.number import (
    CategoryInfo,
    NumberCreate,
    NumberFilter,
    NumberListResponse,
    NumberPatternAnalysis,
    NumberReservationRequest,
    NumberReservationResponse,
    NumberResponse,
    NumberSearchRequest,
    NumberUpdate,
)
from ...services.number_service import NumberService

router = APIRouter()


def get_number_service(db: Session = Depends(get_db)) -> NumberService:
    """전화번호 서비스 의존성"""
    return NumberService(db)


@router.get("/", response_model=NumberListResponse)
async def get_numbers(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    status: Optional[str] = Query("available", description="상태 필터"),
    is_premium: Optional[bool] = Query(None, description="프리미엄 번호 필터"),
    pattern_type: Optional[str] = Query(None, description="패턴 유형 필터"),
    search: Optional[str] = Query(None, description="번호 검색"),
    min_fee: Optional[Decimal] = Query(None, description="최소 추가 요금"),
    max_fee: Optional[Decimal] = Query(None, description="최대 추가 요금"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    number_service: NumberService = Depends(get_number_service),
):
    """
    전화번호 목록 조회

    - **category**: 카테고리별 필터링 (일반, 연속, 특별)
    - **status**: 상태 필터 (available, reserved, assigned)
    - **is_premium**: 프리미엄 번호 필터
    - **pattern_type**: 패턴 유형 필터
    - **search**: 번호 검색 (끝자리 또는 패턴)
    - **min_fee**: 최소 추가 요금
    - **max_fee**: 최대 추가 요금
    - **page**: 페이지 번호 (기본값: 1)
    - **size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    filters = NumberFilter(
        category=category,
        status=status,
        is_premium=is_premium,
        pattern_type=pattern_type,
        search=search,
        min_fee=min_fee,
        max_fee=max_fee,
    )

    numbers, total = number_service.get_numbers(filters, page, size)
    total_pages = math.ceil(total / size)

    return NumberListResponse(numbers=numbers, total=total, page=page, size=size, total_pages=total_pages)


@router.get("/categories", response_model=List[CategoryInfo])
async def get_number_categories(number_service: NumberService = Depends(get_number_service)):
    """
    사용 가능한 전화번호 카테고리 정보 조회
    """
    return number_service.get_categories()


@router.get("/available", response_model=List[NumberResponse])
async def get_available_numbers(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    limit: int = Query(20, ge=1, le=100, description="결과 개수 제한"),
    number_service: NumberService = Depends(get_number_service),
):
    """
    사용 가능한 전화번호 목록 조회
    """
    return number_service.get_available_numbers(category, limit)


@router.post("/search", response_model=List[NumberResponse])
async def search_numbers(search_request: NumberSearchRequest, number_service: NumberService = Depends(get_number_service)):
    """
    전화번호 패턴 검색

    - **pattern**: 검색할 패턴 (끝자리 숫자 또는 특정 패턴)
    - **category**: 카테고리 필터 (선택사항)
    - **limit**: 결과 개수 제한 (기본값: 20, 최대: 100)
    """
    return number_service.search_numbers(search_request)


@router.get("/{number_id}", response_model=NumberResponse)
async def get_number(number_id: int, number_service: NumberService = Depends(get_number_service)):
    """
    전화번호 상세 정보 조회
    """
    return number_service.get_number_by_id(number_id)


@router.post("/{number_id}/reserve", response_model=NumberReservationResponse)
async def reserve_number(
    number_id: int, reservation_request: NumberReservationRequest, number_service: NumberService = Depends(get_number_service)
):
    """
    전화번호 예약

    - **order_id**: 주문 ID
    - **minutes**: 예약 시간 (분, 기본값: 30분, 최대: 60분)
    """
    number = number_service.reserve_number(number_id, reservation_request)

    return NumberReservationResponse(
        number_id=number.id,
        number=number.number,
        reserved_until=number.reserved_until,
        order_id=reservation_request.order_id,
        message="번호가 성공적으로 예약되었습니다.",
    )


@router.delete("/{number_id}/reservation")
async def release_number_reservation(
    number_id: int,
    order_id: str = Query(..., description="주문 ID"),
    number_service: NumberService = Depends(get_number_service),
):
    """
    전화번호 예약 해제
    """
    number_service.release_reservation(number_id, order_id)
    return {"message": "번호 예약이 해제되었습니다."}


@router.post("/analyze", response_model=NumberPatternAnalysis)
async def analyze_number_pattern(
    number: str = Query(..., description="분석할 전화번호"), number_service: NumberService = Depends(get_number_service)
):
    """
    전화번호 패턴 분석

    번호의 패턴을 분석하여 프리미엄 여부와 점수를 반환합니다.
    """
    return number_service.analyze_number_pattern(number)


# 관리자 전용 엔드포인트
@router.post("/", response_model=NumberResponse)
async def create_number(
    number_data: NumberCreate,
    number_service: NumberService = Depends(get_number_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    전화번호 생성 (관리자 전용)
    """
    return number_service.create_number(number_data)


@router.put("/{number_id}", response_model=NumberResponse)
async def update_number(
    number_id: int,
    number_data: NumberUpdate,
    number_service: NumberService = Depends(get_number_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    전화번호 수정 (관리자 전용)
    """
    return number_service.update_number(number_id, number_data)


@router.delete("/{number_id}")
async def delete_number(
    number_id: int,
    number_service: NumberService = Depends(get_number_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    전화번호 삭제 (관리자 전용)
    """
    number_service.delete_number(number_id)
    return {"message": "전화번호가 삭제되었습니다."}


@router.post("/{number_id}/assign", response_model=NumberResponse)
async def assign_number(
    number_id: int,
    number_service: NumberService = Depends(get_number_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    전화번호 할당 (관리자 전용) - 개통 완료 처리
    """
    number = number_service.assign_number(number_id)
    return number


@router.get("/admin/all", response_model=NumberListResponse)
async def get_all_numbers_for_admin(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    status: Optional[str] = Query(None, description="상태 필터"),
    is_premium: Optional[bool] = Query(None, description="프리미엄 번호 필터"),
    pattern_type: Optional[str] = Query(None, description="패턴 유형 필터"),
    search: Optional[str] = Query(None, description="번호 검색"),
    min_fee: Optional[Decimal] = Query(None, description="최소 추가 요금"),
    max_fee: Optional[Decimal] = Query(None, description="최대 추가 요금"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    number_service: NumberService = Depends(get_number_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    모든 전화번호 조회 (관리자 전용) - 모든 상태 포함
    """
    filters = NumberFilter(
        category=category,
        status=status,
        is_premium=is_premium,
        pattern_type=pattern_type,
        search=search,
        min_fee=min_fee,
        max_fee=max_fee,
    )

    numbers, total = number_service.get_numbers(filters, page, size)
    total_pages = math.ceil(total / size)

    return NumberListResponse(numbers=numbers, total=total, page=page, size=size, total_pages=total_pages)
