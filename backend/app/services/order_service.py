from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status
from decimal import Decimal

from ..models.order import Order
from ..models.order_status_history import OrderStatusHistory
from ..models.user import User
from ..models.plan import Plan
from ..models.device import Device
from ..models.number import Number
from ..models.payment import Payment
from ..schemas.order import (
    OrderCreate, 
    OrderUpdate, 
    OrderFilter,
    OrderStatusUpdate,
    OrderDashboard,
    OrderStatusStats
)
from ..services.notification_service import notification_service


class OrderService:
    """주문 서비스"""
    
    # 주문 상태 정의
    ORDER_STATUSES = {
        "pending": "접수 대기",
        "confirmed": "접수 완료",
        "processing": "처리 중",
        "completed": "완료",
        "cancelled": "취소"
    }
    
    # 상태 전환 규칙
    STATUS_TRANSITIONS = {
        "pending": ["confirmed", "cancelled"],
        "confirmed": ["processing", "cancelled"],
        "processing": ["completed", "cancelled"],
        "completed": [],
        "cancelled": []
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_orders(
        self, 
        filters: OrderFilter,
        page: int = 1,
        size: int = 20,
        include_relations: bool = True
    ) -> tuple[List[Order], int]:
        """주문 목록 조회 (필터링 및 페이징 지원)"""
        query = self.db.query(Order)
        
        if include_relations:
            query = query.options(
                joinedload(Order.user),
                joinedload(Order.plan),
                joinedload(Order.device),
                joinedload(Order.number),
                joinedload(Order.payment),
                joinedload(Order.status_history)
            )
        
        # 필터 적용
        conditions = []
        
        if filters.status:
            conditions.append(Order.status == filters.status)
        
        if filters.user_id:
            conditions.append(Order.user_id == filters.user_id)
        
        if filters.plan_id:
            conditions.append(Order.plan_id == filters.plan_id)
        
        if filters.device_id:
            conditions.append(Order.device_id == filters.device_id)
        
        if filters.is_paid is not None:
            if filters.is_paid:
                query = query.join(Payment).filter(Payment.status == "completed")
            else:
                query = query.outerjoin(Payment).filter(
                    or_(Payment.id.is_(None), Payment.status != "completed")
                )
        
        if filters.date_from:
            conditions.append(Order.created_at >= filters.date_from)
        
        if filters.date_to:
            conditions.append(Order.created_at <= filters.date_to)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.join(User)
            conditions.append(
                or_(
                    Order.order_number.ilike(search_term),
                    User.name.ilike(search_term)
                )
            )
        
        if conditions:
            query = query.filter(and_(*conditions))
        
        # 전체 개수 조회
        total = query.count()
        
        # 정렬 및 페이징 (최신 주문 우선)
        orders = (
            query
            .order_by(desc(Order.created_at))
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )
        
        return orders, total
    
    def get_order_by_id(self, order_id: int, include_relations: bool = True) -> Order:
        """ID로 주문 조회"""
        query = self.db.query(Order)
        
        if include_relations:
            query = query.options(
                joinedload(Order.user),
                joinedload(Order.plan),
                joinedload(Order.device),
                joinedload(Order.number),
                joinedload(Order.payment),
                joinedload(Order.status_history)
            )
        
        order = query.filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="주문을 찾을 수 없습니다."
            )
        return order
    
    def get_order_by_number(self, order_number: str, include_relations: bool = True) -> Order:
        """주문번호로 주문 조회"""
        query = self.db.query(Order)
        
        if include_relations:
            query = query.options(
                joinedload(Order.user),
                joinedload(Order.plan),
                joinedload(Order.device),
                joinedload(Order.number),
                joinedload(Order.payment),
                joinedload(Order.status_history)
            )
        
        order = query.filter(Order.order_number == order_number).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="주문을 찾을 수 없습니다."
            )
        return order
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """주문 생성"""
        # 관련 데이터 검증
        user = self.db.query(User).filter(User.id == order_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다."
            )
        
        plan = self.db.query(Plan).filter(Plan.id == order_data.plan_id).first()
        if not plan or not plan.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="요금제를 찾을 수 없습니다."
            )
        
        device = None
        if order_data.device_id:
            device = self.db.query(Device).filter(Device.id == order_data.device_id).first()
            if not device or not device.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="단말기를 찾을 수 없습니다."
                )
        
        number = None
        if order_data.number_id:
            number = self.db.query(Number).filter(Number.id == order_data.number_id).first()
            if not number or not number.is_available:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="선택한 번호를 사용할 수 없습니다."
                )
        
        # 주문 생성
        order = Order(**order_data.model_dump())
        
        # 금액 계산
        order.plan_fee = plan.discounted_price
        order.setup_fee = plan.setup_fee
        order.device_fee = device.final_price if device else 0
        order.number_fee = number.additional_fee if number else 0
        order.calculate_total_amount()
        
        self.db.add(order)
        self.db.flush()  # ID 생성을 위해 flush
        
        # 상태 이력 생성
        self._add_status_history(order.id, "pending", None, "주문이 생성되었습니다.", is_automatic=True)
        
        # 번호 예약 (있는 경우)
        if number:
            number.reserve(order.order_number, 30)
        
        self.db.commit()
        self.db.refresh(order)
        
        # 주문 확인 알림 발송 (SMS + 이메일)
        try:
            await notification_service.send_order_confirmation_notifications(
                db=self.db,
                order=order,
                user=user
            )
        except Exception as e:
            # 알림 발송 실패는 주문 생성에 영향을 주지 않음
            logger.error(f"주문 확인 알림 발송 실패: {e}")
        
        return order
    
    def update_order(self, order_id: int, order_data: OrderUpdate) -> Order:
        """주문 수정"""
        order = self.get_order_by_id(order_id, include_relations=False)
        
        # 수정 가능한 상태인지 확인
        if order.status not in ["pending", "confirmed"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 상태에서는 주문을 수정할 수 없습니다."
            )
        
        # 결제 완료된 주문은 수정 불가
        if order.is_paid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="결제 완료된 주문은 수정할 수 없습니다."
            )
        
        update_data = order_data.model_dump(exclude_unset=True)
        
        # 단말기 변경 시 금액 재계산
        if 'device_id' in update_data:
            if update_data['device_id']:
                device = self.db.query(Device).filter(Device.id == update_data['device_id']).first()
                if not device or not device.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="단말기를 찾을 수 없습니다."
                    )
                order.device_fee = device.final_price
            else:
                order.device_fee = 0
        
        # 번호 변경 시 금액 재계산 및 예약 처리
        if 'number_id' in update_data:
            # 기존 번호 예약 해제
            if order.number_id:
                old_number = self.db.query(Number).filter(Number.id == order.number_id).first()
                if old_number and old_number.reserved_by_order_id == order.order_number:
                    old_number.release()
            
            # 새 번호 예약
            if update_data['number_id']:
                new_number = self.db.query(Number).filter(Number.id == update_data['number_id']).first()
                if not new_number or not new_number.is_available:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="선택한 번호를 사용할 수 없습니다."
                    )
                new_number.reserve(order.order_number, 30)
                order.number_fee = new_number.additional_fee
            else:
                order.number_fee = 0
        
        # 필드 업데이트
        for field, value in update_data.items():
            setattr(order, field, value)
        
        # 총 금액 재계산
        order.calculate_total_amount()
        
        self.db.commit()
        self.db.refresh(order)
        return order
    
    async def update_order_status(self, order_id: int, status_update: OrderStatusUpdate, admin_id: Optional[int] = None) -> Order:
        """주문 상태 변경"""
        order = self.get_order_by_id(order_id, include_relations=False)
        
        new_status = status_update.status
        current_status = order.status
        
        # 상태 전환 가능성 확인
        if new_status not in self.STATUS_TRANSITIONS.get(current_status, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"'{current_status}'에서 '{new_status}'로 상태를 변경할 수 없습니다."
            )
        
        # 상태 변경
        order.status = new_status
        
        # 상태 이력 추가
        self._add_status_history(
            order_id, 
            new_status, 
            current_status, 
            status_update.note,
            admin_id=admin_id,
            is_automatic=False
        )
        
        # 상태별 추가 처리
        if new_status == "completed":
            # 번호 할당
            if order.number_id:
                number = self.db.query(Number).filter(Number.id == order.number_id).first()
                if number:
                    number.assign()
        elif new_status == "cancelled":
            # 번호 예약 해제
            if order.number_id:
                number = self.db.query(Number).filter(Number.id == order.number_id).first()
                if number and number.reserved_by_order_id == order.order_number:
                    number.release()
        
        self.db.commit()
        self.db.refresh(order)
        
        # 상태 변경 알림 발송 (SMS + 이메일)
        try:
            await notification_service.send_order_status_update_notifications(
                db=self.db,
                order=order,
                new_status=new_status,
                note=status_update.note
            )
        except Exception as e:
            # 알림 발송 실패는 상태 변경에 영향을 주지 않음
            logger.error(f"주문 상태 변경 알림 발송 실패: {e}")
        
        return order
    
    async def cancel_order(self, order_id: int, reason: Optional[str] = None, admin_id: Optional[int] = None) -> Order:
        """주문 취소"""
        order = self.get_order_by_id(order_id, include_relations=False)
        
        if not order.can_cancel:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="취소할 수 없는 주문입니다."
            )
        
        status_update = OrderStatusUpdate(
            status="cancelled",
            note=reason or "주문이 취소되었습니다."
        )
        
        return await self.update_order_status(order_id, status_update, admin_id)
    
    def get_user_orders(self, user_id: int, page: int = 1, size: int = 20) -> tuple[List[Order], int]:
        """사용자별 주문 목록 조회"""
        filters = OrderFilter(user_id=user_id)
        return self.get_orders(filters, page, size)
    
    def get_dashboard_stats(self) -> OrderDashboard:
        """주문 대시보드 통계"""
        today = date.today()
        
        # 전체 주문 수
        total_orders = self.db.query(Order).count()
        
        # 상태별 주문 수
        pending_orders = self.db.query(Order).filter(Order.status == "pending").count()
        processing_orders = self.db.query(Order).filter(Order.status == "processing").count()
        completed_orders = self.db.query(Order).filter(Order.status == "completed").count()
        cancelled_orders = self.db.query(Order).filter(Order.status == "cancelled").count()
        
        # 오늘 주문 수
        today_orders = (
            self.db.query(Order)
            .filter(func.date(Order.created_at) == today)
            .count()
        )
        
        # 총 매출 (완료된 주문)
        total_revenue = (
            self.db.query(func.sum(Order.total_amount))
            .filter(Order.status == "completed")
            .scalar() or Decimal('0')
        )
        
        # 상태별 통계
        status_stats = []
        for status, count in [
            ("pending", pending_orders),
            ("processing", processing_orders),
            ("completed", completed_orders),
            ("cancelled", cancelled_orders)
        ]:
            percentage = (count / total_orders * 100) if total_orders > 0 else 0
            status_stats.append(OrderStatusStats(
                status=status,
                count=count,
                percentage=round(percentage, 2)
            ))
        
        return OrderDashboard(
            total_orders=total_orders,
            pending_orders=pending_orders,
            processing_orders=processing_orders,
            completed_orders=completed_orders,
            cancelled_orders=cancelled_orders,
            today_orders=today_orders,
            total_revenue=total_revenue,
            status_stats=status_stats
        )
    
    def _add_status_history(
        self, 
        order_id: int, 
        status: str, 
        previous_status: Optional[str], 
        note: Optional[str] = None,
        admin_id: Optional[int] = None,
        is_automatic: bool = False
    ):
        """상태 이력 추가"""
        history = OrderStatusHistory(
            order_id=order_id,
            status=status,
            previous_status=previous_status,
            note=note,
            admin_id=admin_id,
            is_automatic="true" if is_automatic else "false"
        )
        self.db.add(history)
        self.db.flush()