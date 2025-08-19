from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...core.deps import get_db, get_current_admin
from ...core.database import SessionLocal
from ...core.permissions import (
    require_admin_permissions,
    require_order_management,
    require_user_management,
    require_statistics_access,
    require_system_admin,
    Permission
)
from ...models.admin import Admin
from ...models.user import User
from ...models.order import Order
from ...services.admin_service import AdminService
from ...schemas.admin import (
    AdminCreate,
    AdminUpdate,
    AdminResponse,
    AdminListResponse,
    AdminActivityLogListResponse,
    AdminDashboardResponse,
    AdminPermissionResponse,
    ChangePasswordRequest
)
from ...schemas.auth import AdminCreate as AuthAdminCreate, AdminUpdate as AuthAdminUpdate

router = APIRouter()

@router.get("/dashboard", response_model=Dict[str, Any])
async def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """관리자 대시보드 데이터 조회"""
    admin_service = AdminService(db)
    
    try:
        dashboard_stats = admin_service.get_dashboard_stats()
        
        return {
            "success": True,
            "data": {
                **dashboard_stats,
                "admin_info": {
                    "id": current_admin.id,
                    "username": current_admin.username,
                    "role": current_admin.role,
                    "permissions": admin_service.get_admin_permissions(current_admin)
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대시보드 데이터 조회 중 오류가 발생했습니다."
        )

@router.get("/users", response_model=Dict[str, Any])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_user_management())
):
    """모든 사용자 조회 (사용자 관리 권한 필요)"""
    users = db.query(User).offset(skip).limit(limit).all()
    total = db.query(User).count()
    
    return {
        "success": True,
        "data": {
            "users": [
                {
                    "id": user.id,
                    "name": user.name,
                    "phone": user.phone,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "created_at": user.created_at
                }
                for user in users
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }

@router.get("/orders", response_model=Dict[str, Any])
async def get_all_orders(
    skip: int = 0,
    limit: int = 100,
    status_filter: str = None,
    user_search: str = None,
    date_from: str = None,
    date_to: str = None,
    plan_id: int = None,
    is_paid: bool = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_order_management())
):
    """모든 주문 조회 (주문 관리 권한 필요)"""
    from ...services.order_service import OrderService
    from ...schemas.order import OrderFilter
    from datetime import datetime
    
    admin_service = AdminService(db)
    order_service = OrderService(db)
    
    try:
        # 필터 생성
        filters = OrderFilter(
            status=status_filter,
            plan_id=plan_id,
            is_paid=is_paid,
            search=user_search
        )
        
        # 날짜 필터 처리
        if date_from:
            try:
                filters.date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if date_to:
            try:
                filters.date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # 주문 목록 조회
        page = (skip // limit) + 1
        orders, total = order_service.get_orders(filters, page, limit)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_ORDERS",
            description="주문 목록 조회",
            request_data={
                "filters": filters.dict(exclude_none=True),
                "skip": skip,
                "limit": limit
            }
        )
        
        return {
            "success": True,
            "data": {
                "orders": [
                    {
                        "id": order.id,
                        "order_number": order.order_number,
                        "user_id": order.user_id,
                        "user_name": order.user.name if order.user else None,
                        "user_phone": order.user.phone if order.user else None,
                        "plan_name": order.plan.name if order.plan else None,
                        "device_name": f"{order.device.brand} {order.device.model}" if order.device else None,
                        "number": order.number.number if order.number else None,
                        "status": order.status,
                        "total_amount": float(order.total_amount),
                        "is_paid": order.is_paid,
                        "payment_status": order.payment.status if order.payment else None,
                        "created_at": order.created_at,
                        "updated_at": order.updated_at
                    }
                    for order in orders
                ],
                "total": total,
                "skip": skip,
                "limit": limit,
                "filters": filters.dict(exclude_none=True)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 목록 조회 중 오류가 발생했습니다."
        )

@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_order_management())
):
    """주문 상세 정보 조회 (주문 관리 권한 필요)"""
    from ...services.order_service import OrderService
    
    admin_service = AdminService(db)
    order_service = OrderService(db)
    
    try:
        order = order_service.get_order_by_id(order_id, include_relations=True)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_ORDER",
            resource_type="order",
            resource_id=order_id,
            description=f"주문 상세 조회: {order.order_number}"
        )
        
        return {
            "success": True,
            "data": {
                "order": {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "plan_fee": float(order.plan_fee),
                    "device_fee": float(order.device_fee),
                    "setup_fee": float(order.setup_fee),
                    "number_fee": float(order.number_fee),
                    "delivery_address": order.delivery_address,
                    "delivery_request": order.delivery_request,
                    "preferred_delivery_time": order.preferred_delivery_time,
                    "terms_agreed": order.terms_agreed,
                    "privacy_agreed": order.privacy_agreed,
                    "marketing_agreed": order.marketing_agreed,
                    "notes": order.notes,
                    "is_paid": order.is_paid,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at
                },
                "user": {
                    "id": order.user.id,
                    "name": order.user.name,
                    "phone": order.user.phone,
                    "email": order.user.email,
                    "birth_date": order.user.birth_date,
                    "address": order.user.address
                } if order.user else None,
                "plan": {
                    "id": order.plan.id,
                    "name": order.plan.name,
                    "description": order.plan.description,
                    "monthly_fee": float(order.plan.monthly_fee),
                    "data_limit": order.plan.data_limit,
                    "call_minutes": order.plan.call_minutes,
                    "sms_count": order.plan.sms_count
                } if order.plan else None,
                "device": {
                    "id": order.device.id,
                    "brand": order.device.brand,
                    "model": order.device.model,
                    "color": order.device.color,
                    "price": float(order.device.price),
                    "specifications": order.device.specifications
                } if order.device else None,
                "number": {
                    "id": order.number.id,
                    "number": order.number.number,
                    "category": order.number.category,
                    "additional_fee": float(order.number.additional_fee)
                } if order.number else None,
                "payment": {
                    "id": order.payment.id,
                    "payment_method": order.payment.payment_method,
                    "amount": float(order.payment.amount),
                    "status": order.payment.status,
                    "transaction_id": order.payment.transaction_id,
                    "paid_at": order.payment.paid_at
                } if order.payment else None,
                "status_history": [
                    {
                        "id": history.id,
                        "status": history.status,
                        "previous_status": history.previous_status,
                        "note": history.note,
                        "admin_username": history.admin.username if history.admin else None,
                        "is_automatic": history.is_automatic == "true",
                        "created_at": history.created_at
                    }
                    for history in order.status_history
                ] if order.status_history else []
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 상세 정보 조회 중 오류가 발생했습니다."
        )

@router.put("/orders/{order_id}/status", response_model=Dict[str, Any])
async def update_order_status(
    order_id: int,
    status_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_order_management())
):
    """주문 상태 업데이트 (주문 관리 권한 필요)"""
    from ...services.order_service import OrderService
    from ...schemas.order import OrderStatusUpdate
    
    admin_service = AdminService(db)
    order_service = OrderService(db)
    
    try:
        # 상태 업데이트 데이터 검증
        new_status = status_data.get("status")
        note = status_data.get("note", "")
        
        if not new_status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="새로운 상태를 입력해주세요."
            )
        
        status_update = OrderStatusUpdate(status=new_status, note=note)
        
        # 주문 상태 업데이트
        order = order_service.update_order_status(order_id, status_update, current_admin.id)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="UPDATE_ORDER_STATUS",
            resource_type="order",
            resource_id=order_id,
            description=f"주문 상태 변경: {order.order_number} -> {new_status}",
            request_data=status_data
        )
        
        return {
            "success": True,
            "message": "주문 상태가 성공적으로 업데이트되었습니다.",
            "data": {
                "order_id": order.id,
                "order_number": order.order_number,
                "new_status": new_status,
                "updated_by": current_admin.username,
                "updated_at": order.updated_at
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 상태 업데이트 중 오류가 발생했습니다."
        )

@router.post("/orders/{order_id}/cancel", response_model=Dict[str, Any])
async def cancel_order(
    order_id: int,
    cancel_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_order_management())
):
    """주문 취소 (주문 관리 권한 필요)"""
    from ...services.order_service import OrderService
    
    admin_service = AdminService(db)
    order_service = OrderService(db)
    
    try:
        reason = cancel_data.get("reason", "관리자에 의한 주문 취소")
        
        # 주문 취소
        order = order_service.cancel_order(order_id, reason, current_admin.id)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="CANCEL_ORDER",
            resource_type="order",
            resource_id=order_id,
            description=f"주문 취소: {order.order_number}",
            request_data=cancel_data
        )
        
        return {
            "success": True,
            "message": "주문이 성공적으로 취소되었습니다.",
            "data": {
                "order_id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "cancelled_by": current_admin.username,
                "cancel_reason": reason
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 취소 중 오류가 발생했습니다."
        )

@router.get("/orders/{order_id}/history", response_model=Dict[str, Any])
async def get_order_status_history(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_order_management())
):
    """주문 상태 변경 이력 조회 (주문 관리 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        # 주문 존재 확인
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="주문을 찾을 수 없습니다."
            )
        
        # 상태 이력 조회
        history_records = (
            db.query(OrderStatusHistory)
            .filter(OrderStatusHistory.order_id == order_id)
            .order_by(OrderStatusHistory.created_at.desc())
            .all()
        )
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_ORDER_HISTORY",
            resource_type="order",
            resource_id=order_id,
            description=f"주문 이력 조회: {order.order_number}"
        )
        
        return {
            "success": True,
            "data": {
                "order_id": order_id,
                "order_number": order.order_number,
                "current_status": order.status,
                "history": [
                    {
                        "id": history.id,
                        "status": history.status,
                        "previous_status": history.previous_status,
                        "note": history.note,
                        "admin_id": history.admin_id,
                        "admin_username": history.admin.username if history.admin else None,
                        "is_automatic": history.is_automatic == "true",
                        "created_at": history.created_at
                    }
                    for history in history_records
                ]
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 이력 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/overview", response_model=Dict[str, Any])
async def get_overview_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """전체 개요 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        overview_stats = stats_service.get_overview_stats()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_OVERVIEW_STATISTICS",
            description="전체 개요 통계 조회"
        )
        
        return {
            "success": True,
            "data": overview_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개요 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/orders", response_model=Dict[str, Any])
async def get_order_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """주문 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        order_stats = stats_service.get_order_status_stats()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_ORDER_STATISTICS",
            description="주문 통계 조회"
        )
        
        return {
            "success": True,
            "data": order_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주문 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/daily", response_model=Dict[str, Any])
async def get_daily_statistics(
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """일별 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        if days > 365:
            days = 365  # 최대 1년
        
        daily_stats = stats_service.get_daily_stats(days)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_DAILY_STATISTICS",
            description=f"일별 통계 조회 ({days}일)",
            request_data={"days": days}
        )
        
        return {
            "success": True,
            "data": daily_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="일별 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/monthly", response_model=Dict[str, Any])
async def get_monthly_statistics(
    months: int = 12,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """월별 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        if months > 24:
            months = 24  # 최대 2년
        
        monthly_stats = stats_service.get_monthly_stats(months)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_MONTHLY_STATISTICS",
            description=f"월별 통계 조회 ({months}개월)",
            request_data={"months": months}
        )
        
        return {
            "success": True,
            "data": monthly_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="월별 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/plans", response_model=Dict[str, Any])
async def get_plan_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """요금제별 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        plan_stats = stats_service.get_plan_stats()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_PLAN_STATISTICS",
            description="요금제별 통계 조회"
        )
        
        return {
            "success": True,
            "data": plan_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="요금제 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/devices", response_model=Dict[str, Any])
async def get_device_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """단말기별 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        device_stats = stats_service.get_device_stats()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_DEVICE_STATISTICS",
            description="단말기별 통계 조회"
        )
        
        return {
            "success": True,
            "data": device_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="단말기 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/users", response_model=Dict[str, Any])
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """사용자 통계 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        user_stats = stats_service.get_user_stats()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_USER_STATISTICS",
            description="사용자 통계 조회"
        )
        
        return {
            "success": True,
            "data": user_stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 통계 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/performance", response_model=Dict[str, Any])
async def get_performance_metrics(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """성과 지표 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        performance_metrics = stats_service.get_performance_metrics()
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="VIEW_PERFORMANCE_METRICS",
            description="성과 지표 조회"
        )
        
        return {
            "success": True,
            "data": performance_metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="성과 지표 조회 중 오류가 발생했습니다."
        )

@router.get("/statistics/report", response_model=Dict[str, Any])
async def get_comprehensive_report(
    period: str = "month",  # week, month, quarter, year
    export_format: str = "json",  # json, csv, excel
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_statistics_access())
):
    """종합 리포트 조회 (통계 조회 권한 필요)"""
    from ...services.statistics_service import StatisticsService
    
    admin_service = AdminService(db)
    stats_service = StatisticsService(db)
    
    try:
        if period not in ["week", "month", "quarter", "year"]:
            period = "month"
        
        comprehensive_report = stats_service.get_comprehensive_report(period)
        
        # 활동 로그 기록
        admin_service.log_admin_activity(
            admin_id=current_admin.id,
            action="GENERATE_COMPREHENSIVE_REPORT",
            description=f"종합 리포트 생성 ({period})",
            request_data={"period": period, "export_format": export_format}
        )
        
        # TODO: CSV, Excel 내보내기 기능 구현 (필요시)
        if export_format in ["csv", "excel"]:
            return {
                "success": True,
                "message": f"{export_format.upper()} 내보내기는 추후 구현 예정입니다.",
                "data": comprehensive_report
            }
        
        return {
            "success": True,
            "data": comprehensive_report
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="종합 리포트 생성 중 오류가 발생했습니다."
        )

@router.get("/admins", response_model=AdminListResponse)
async def get_all_admins(
    skip: int = 0,
    limit: int = 100,
    role_filter: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """모든 관리자 조회 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        result = admin_service.get_admin_list(
            skip=skip,
            limit=limit,
            role_filter=role_filter,
            active_only=active_only
        )
        
        return AdminListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 목록 조회 중 오류가 발생했습니다."
        )

@router.post("/admins", response_model=Dict[str, Any])
async def create_admin(
    admin_data: AuthAdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """새 관리자 생성 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        new_admin = admin_service.create_admin(admin_data, current_admin.id)
        
        return {
            "success": True,
            "message": "관리자가 성공적으로 생성되었습니다.",
            "data": {
                "id": new_admin.id,
                "username": new_admin.username,
                "email": new_admin.email,
                "role": new_admin.role
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 생성 중 오류가 발생했습니다."
        )

@router.get("/admins/{admin_id}", response_model=Dict[str, Any])
async def get_admin_by_id(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """특정 관리자 조회 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    admin = admin_service.get_admin_by_id(admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다."
        )
    
    return {
        "success": True,
        "data": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role": admin.role,
            "full_name": admin.full_name,
            "department": admin.department,
            "phone": admin.phone,
            "is_active": admin.is_active,
            "last_login": admin.last_login,
            "login_count": admin.login_count,
            "created_at": admin.created_at
        }
    }

@router.put("/admins/{admin_id}", response_model=Dict[str, Any])
async def update_admin(
    admin_id: int,
    admin_data: AuthAdminUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """관리자 정보 수정 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        updated_admin = admin_service.update_admin(admin_id, admin_data, current_admin.id)
        
        return {
            "success": True,
            "message": "관리자 정보가 성공적으로 수정되었습니다.",
            "data": {
                "id": updated_admin.id,
                "username": updated_admin.username,
                "email": updated_admin.email,
                "role": updated_admin.role
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 정보 수정 중 오류가 발생했습니다."
        )

@router.delete("/admins/{admin_id}", response_model=Dict[str, Any])
async def deactivate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """관리자 비활성화 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        deactivated_admin = admin_service.deactivate_admin(admin_id, current_admin.id)
        
        return {
            "success": True,
            "message": "관리자가 성공적으로 비활성화되었습니다.",
            "data": {
                "id": deactivated_admin.id,
                "username": deactivated_admin.username,
                "is_active": deactivated_admin.is_active
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 비활성화 중 오류가 발생했습니다."
        )

@router.get("/permissions", response_model=AdminPermissionResponse)
async def get_current_admin_permissions(
    current_admin: Admin = Depends(require_admin_permissions(Permission.READ_USER))
):
    """현재 관리자의 권한 조회"""
    admin_service = AdminService(SessionLocal())
    permissions = admin_service.get_admin_permissions(current_admin)
    
    return AdminPermissionResponse(
        admin_id=current_admin.id,
        role=current_admin.role,
        permissions=permissions
    )

@router.get("/activity-logs", response_model=AdminActivityLogListResponse)
async def get_admin_activity_logs(
    admin_id: int = None,
    skip: int = 0,
    limit: int = 100,
    days: int = 30,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_system_admin())
):
    """관리자 활동 로그 조회 (시스템 관리자 권한 필요)"""
    admin_service = AdminService(db)
    
    try:
        result = admin_service.get_admin_activity_logs(
            admin_id=admin_id,
            skip=skip,
            limit=limit,
            days=days
        )
        
        return AdminActivityLogListResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="활동 로그 조회 중 오류가 발생했습니다."
        )

@router.post("/change-password", response_model=Dict[str, Any])
async def change_admin_password(
    password_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """관리자 비밀번호 변경"""
    admin_service = AdminService(db)
    
    try:
        admin_service.change_admin_password(
            admin_id=current_admin.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            changed_by_admin_id=current_admin.id
        )
        
        return {
            "success": True,
            "message": "비밀번호가 성공적으로 변경되었습니다."
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다."
        )

@router.get("/session", response_model=Dict[str, Any])
async def get_admin_session_info(
    current_admin: Admin = Depends(get_current_admin)
):
    """현재 관리자 세션 정보 조회"""
    admin_service = AdminService(SessionLocal())
    permissions = admin_service.get_admin_permissions(current_admin)
    
    return {
        "success": True,
        "data": {
            "admin_id": current_admin.id,
            "username": current_admin.username,
            "role": current_admin.role,
            "permissions": permissions,
            "last_login": current_admin.last_login,
            "is_active": current_admin.is_active
        }
    }