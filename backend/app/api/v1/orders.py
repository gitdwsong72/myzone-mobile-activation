import math
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.deps import get_current_admin, get_current_user
from ...models.admin import Admin
from ...models.user import User
from ...schemas.order import (
    OrderCreate,
    OrderDashboard,
    OrderFilter,
    OrderListResponse,
    OrderResponse,
    OrderStatusUpdate,
    OrderSummaryResponse,
    OrderUpdate,
)
from ...services.order_service import OrderService

router = APIRouter()


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """주문 서비스 의존성"""
    return OrderService(db)


@router.get("/", response_model=OrderListResponse)
async def get_orders(
    status: Optional[str] = Query(None, description="상태 필터"),
    is_paid: Optional[bool] = Query(None, description="결제 완료 여부"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    """
    사용자 주문 목록 조회

    - **status**: 상태 필터 (pending, confirmed, processing, completed, cancelled)
    - **is_paid**: 결제 완료 여부 필터
    - **date_from**: 시작 날짜
    - **date_to**: 종료 날짜
    - **search**: 검색어 (주문번호)
    - **page**: 페이지 번호 (기본값: 1)
    - **size**: 페이지 크기 (기본값: 20, 최대: 100)
    """
    filters = OrderFilter(
        status=status, user_id=current_user.id, is_paid=is_paid, date_from=date_from, date_to=date_to, search=search
    )

    orders, total = order_service.get_orders(filters, page, size)
    total_pages = math.ceil(total / size)

    return OrderListResponse(orders=orders, total=total, page=page, size=size, total_pages=total_pages)


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    """
    주문 생성

    새로운 주문을 생성합니다. 사용자 ID는 현재 로그인한 사용자로 자동 설정됩니다.
    """
    # 사용자 ID를 현재 로그인한 사용자로 설정
    order_data.user_id = current_user.id
    return await order_service.create_order(order_data)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int, order_service: OrderService = Depends(get_order_service), current_user: User = Depends(get_current_user)
):
    """
    주문 상세 정보 조회
    """
    order = order_service.get_order_by_id(order_id)

    # 본인 주문만 조회 가능
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    return order


@router.get("/number/{order_number}", response_model=OrderResponse)
async def get_order_by_number(
    order_number: str, order_service: OrderService = Depends(get_order_service), current_user: User = Depends(get_current_user)
):
    """
    주문번호로 주문 조회
    """
    order = order_service.get_order_by_number(order_number)

    # 본인 주문만 조회 가능
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    return order


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_data: OrderUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    """
    주문 수정

    주문 상태가 pending 또는 confirmed이고 결제가 완료되지 않은 경우에만 수정 가능합니다.
    """
    order = order_service.get_order_by_id(order_id, include_relations=False)

    # 본인 주문만 수정 가능
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    return order_service.update_order(order_id, order_data)


@router.delete("/{order_id}")
async def cancel_order(
    order_id: int,
    reason: Optional[str] = Query(None, description="취소 사유"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user),
):
    """
    주문 취소

    결제가 완료되지 않은 주문만 취소 가능합니다.
    """
    order = order_service.get_order_by_id(order_id, include_relations=False)

    # 본인 주문만 취소 가능
    if order.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="접근 권한이 없습니다.")

    await order_service.cancel_order(order_id, reason, admin_id=None)
    return {"message": "주문이 취소되었습니다."}


# 공개 API (주문번호로 조회 - 인증 불필요)
@router.get("/public/{order_number}", response_model=OrderSummaryResponse)
async def get_order_status_public(order_number: str, order_service: OrderService = Depends(get_order_service)):
    """
    주문번호로 주문 상태 조회 (공개 API)

    인증 없이 주문번호만으로 주문 상태를 확인할 수 있습니다.
    개인정보는 제한적으로만 제공됩니다.
    """
    order = order_service.get_order_by_number(order_number)

    return OrderSummaryResponse(
        id=order.id,
        order_number=order.order_number,
        status=order.status,
        total_amount=order.total_amount,
        user_name=order.user.name[:1] + "*" * (len(order.user.name) - 1),  # 이름 마스킹
        plan_name=order.plan.name,
        device_name=order.device.full_name if order.device else None,
        number=order.number.number if order.number else None,
        created_at=order.created_at,
    )


# 관리자 전용 엔드포인트
@router.get("/admin/all", response_model=OrderListResponse)
async def get_all_orders_for_admin(
    status: Optional[str] = Query(None, description="상태 필터"),
    user_id: Optional[int] = Query(None, description="사용자 ID"),
    plan_id: Optional[int] = Query(None, description="요금제 ID"),
    device_id: Optional[int] = Query(None, description="단말기 ID"),
    is_paid: Optional[bool] = Query(None, description="결제 완료 여부"),
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    search: Optional[str] = Query(None, description="검색어"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    order_service: OrderService = Depends(get_order_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    모든 주문 조회 (관리자 전용)
    """
    filters = OrderFilter(
        status=status,
        user_id=user_id,
        plan_id=plan_id,
        device_id=device_id,
        is_paid=is_paid,
        date_from=date_from,
        date_to=date_to,
        search=search,
    )

    orders, total = order_service.get_orders(filters, page, size)
    total_pages = math.ceil(total / size)

    return OrderListResponse(orders=orders, total=total, page=page, size=size, total_pages=total_pages)


@router.put("/admin/{order_id}/status", response_model=OrderResponse)
async def update_order_status_admin(
    order_id: int,
    status_update: OrderStatusUpdate,
    order_service: OrderService = Depends(get_order_service),
    current_admin: Admin = Depends(get_current_admin),
):
    """
    주문 상태 변경 (관리자 전용)
    """
    return await order_service.update_order_status(order_id, status_update, current_admin.id)


@router.get("/admin/dashboard", response_model=OrderDashboard)
async def get_order_dashboard(
    order_service: OrderService = Depends(get_order_service), current_admin: Admin = Depends(get_current_admin)
):
    """
    주문 대시보드 통계 (관리자 전용)
    """
    return order_service.get_dashboard_stats()
