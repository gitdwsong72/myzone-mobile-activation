import math
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_admin
from ...models.admin import Admin
from ...schemas.plan import PlanCreate, PlanFilter, PlanListResponse, PlanResponse, PlanUpdate
from ...services.plan_service import PlanService

router = APIRouter()


def get_plan_service(db: Session = Depends(get_db)) -> PlanService:
    """요금제 서비스 의존성"""
    return PlanService(db)


@router.get("/", response_model=PlanListResponse)
async def get_plans(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    min_price: Optional[Decimal] = Query(None, description="최소 가격"),
    max_price: Optional[Decimal] = Query(None, description="최대 가격"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    plan_service: PlanService = Depends(get_plan_service),
):
    """
    요금제 목록 조회

    - **category**: 카테고리별 필터링 (5G, LTE, 데이터중심, 통화중심)
    - **min_price**: 최소 가격 필터
    - **max_price**: 최대 가격 필터
    - **search**: 요금제 이름 또는 설명 검색
    - **page**: 페이지 번호 (기본값: 1)
    - **size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    filters = PlanFilter(category=category, min_price=min_price, max_price=max_price, search=search, is_active=True)

    plans, total = plan_service.get_plans(filters, page, size)
    total_pages = math.ceil(total / size)

    return PlanListResponse(plans=plans, total=total, page=page, size=size, total_pages=total_pages)


@router.get("/categories", response_model=List[str])
async def get_plan_categories(plan_service: PlanService = Depends(get_plan_service)):
    """
    사용 가능한 요금제 카테고리 목록 조회
    """
    return plan_service.get_available_categories()


@router.get("/recommended", response_model=List[PlanResponse])
async def get_recommended_plans(
    limit: int = Query(3, ge=1, le=10, description="추천 요금제 개수"), plan_service: PlanService = Depends(get_plan_service)
):
    """
    추천 요금제 조회 (할인율이 높은 순)
    """
    return plan_service.get_recommended_plans(limit)


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: int, plan_service: PlanService = Depends(get_plan_service)):
    """
    요금제 상세 정보 조회
    """
    plan = plan_service.get_plan_by_id(plan_id)
    if not plan.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요금제를 찾을 수 없습니다.")
    return plan


# 관리자 전용 엔드포인트
@router.post("/", response_model=PlanResponse)
async def create_plan(
    plan_data: PlanCreate,
    plan_service: PlanService = Depends(get_plan_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    요금제 생성 (관리자 전용)
    """
    return plan_service.create_plan(plan_data)


@router.put("/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    plan_service: PlanService = Depends(get_plan_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    요금제 수정 (관리자 전용)
    """
    return plan_service.update_plan(plan_id, plan_data)


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int, plan_service: PlanService = Depends(get_plan_service), current_admin: Admin = Depends(get_current_admin)
):
    """
    요금제 삭제 (관리자 전용) - 소프트 삭제
    """
    plan_service.delete_plan(plan_id)
    return {"message": "요금제가 삭제되었습니다."}


@router.get("/admin/all", response_model=PlanListResponse)
async def get_all_plans_for_admin(
    category: Optional[str] = Query(None, description="카테고리 필터"),
    min_price: Optional[Decimal] = Query(None, description="최소 가격"),
    max_price: Optional[Decimal] = Query(None, description="최대 가격"),
    search: Optional[str] = Query(None, description="검색어"),
    is_active: Optional[bool] = Query(None, description="활성화 상태"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    plan_service: PlanService = Depends(get_plan_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    모든 요금제 조회 (관리자 전용) - 비활성화된 요금제 포함
    """
    filters = PlanFilter(category=category, min_price=min_price, max_price=max_price, search=search, is_active=is_active)

    plans, total = plan_service.get_plans(filters, page, size)
    total_pages = math.ceil(total / size)

    return PlanListResponse(plans=plans, total=total, page=page, size=size, total_pages=total_pages)
