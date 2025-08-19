from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.orm import Session
from decimal import Decimal

from ...core.database import get_db
from ...core.deps import get_current_user, get_current_admin_user
from ...services.payment_service import PaymentService
from ...services.order_service import OrderService
from ...schemas.payment import PaymentResponse, PaymentCreate, PaymentUpdate
from ...models.user import User
from ...models.admin import Admin

router = APIRouter()


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    """결제 서비스 의존성"""
    return PaymentService(db)


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """주문 서비스 의존성"""
    return OrderService(db)


@router.post("/", response_model=PaymentResponse)
async def create_payment(
    payment_data: PaymentCreate,
    payment_service: PaymentService = Depends(get_payment_service),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    결제 생성
    
    주문에 대한 결제를 생성합니다. 본인의 주문에 대해서만 결제를 생성할 수 있습니다.
    """
    # 주문 소유권 확인
    order = order_service.get_order_by_id(payment_data.order_id, include_relations=False)
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return payment_service.create_payment(payment_data)


@router.post("/{payment_id}/process")
async def process_payment(
    payment_id: int,
    pg_data: Dict[str, Any] = Body(..., description="PG사 결제 데이터"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """
    결제 처리
    
    생성된 결제를 실제로 처리합니다. PG사 연동 데이터를 받아 결제를 진행합니다.
    
    **PG 데이터 예시:**
    ```json
    {
        "card_number": "1234-5678-9012-3456",
        "expiry_date": "12/25",
        "cvc": "123",
        "installment_months": 0,
        "cardholder_name": "홍길동"
    }
    ```
    """
    payment = payment_service.get_payment_by_id(payment_id)
    
    # 주문 소유권 확인
    if payment.order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    processed_payment = payment_service.process_payment(payment_id, pg_data)
    
    return {
        "payment_id": processed_payment.id,
        "status": processed_payment.status,
        "transaction_id": processed_payment.transaction_id,
        "paid_at": processed_payment.paid_at,
        "receipt_url": processed_payment.receipt_url,
        "message": "결제가 성공적으로 처리되었습니다." if processed_payment.is_completed else "결제 처리에 실패했습니다."
    }


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """
    결제 정보 조회
    """
    payment = payment_service.get_payment_by_id(payment_id)
    
    # 주문 소유권 확인
    if payment.order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    return payment


@router.get("/order/{order_id}", response_model=PaymentResponse)
async def get_payment_by_order(
    order_id: int,
    payment_service: PaymentService = Depends(get_payment_service),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    주문 ID로 결제 정보 조회
    """
    # 주문 소유권 확인
    order = order_service.get_order_by_id(order_id, include_relations=False)
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    payment = payment_service.get_payment_by_order_id(order_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="결제 정보를 찾을 수 없습니다."
        )
    
    return payment


@router.post("/{payment_id}/cancel")
async def cancel_payment(
    payment_id: int,
    reason: str = Body(..., description="취소 사유"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """
    결제 취소
    
    결제 대기 또는 처리 중인 결제를 취소합니다.
    """
    payment = payment_service.get_payment_by_id(payment_id)
    
    # 주문 소유권 확인
    if payment.order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    cancelled_payment = payment_service.cancel_payment(payment_id, reason)
    
    return {
        "payment_id": cancelled_payment.id,
        "status": cancelled_payment.status,
        "cancelled_at": cancelled_payment.cancelled_at,
        "cancel_reason": cancelled_payment.cancel_reason,
        "message": "결제가 취소되었습니다."
    }


@router.post("/{payment_id}/verify")
async def verify_payment(
    payment_id: int,
    verification_data: Dict[str, Any] = Body(..., description="검증 데이터"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """
    결제 검증
    
    PG사로부터 받은 결제 결과를 검증합니다.
    """
    payment = payment_service.get_payment_by_id(payment_id)
    
    # 주문 소유권 확인
    if payment.order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다."
        )
    
    is_valid = payment_service.verify_payment(payment_id, verification_data)
    
    return {
        "payment_id": payment_id,
        "is_valid": is_valid,
        "message": "결제 검증이 완료되었습니다." if is_valid else "결제 검증에 실패했습니다."
    }


# 관리자 전용 엔드포인트
@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: int,
    refund_amount: Decimal = Body(..., description="환불 금액"),
    reason: str = Body(..., description="환불 사유"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """
    결제 환불 (관리자 전용)
    
    완료된 결제에 대해 전체 또는 부분 환불을 처리합니다.
    """
    refunded_payment = payment_service.refund_payment(payment_id, refund_amount, reason)
    
    return {
        "payment_id": refunded_payment.id,
        "status": refunded_payment.status,
        "refund_amount": refund_amount,
        "total_refund_amount": refunded_payment.refund_amount,
        "remaining_refund_amount": refunded_payment.remaining_refund_amount,
        "refunded_at": refunded_payment.refunded_at,
        "message": "환불이 처리되었습니다."
    }


@router.get("/admin/statistics")
async def get_payment_statistics(
    date_from: Optional[datetime] = Query(None, description="시작 날짜"),
    date_to: Optional[datetime] = Query(None, description="종료 날짜"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_admin: Admin = Depends(get_current_admin_user)
):
    """
    결제 통계 조회 (관리자 전용)
    
    지정된 기간의 결제 통계를 조회합니다.
    """
    return payment_service.get_payment_statistics(date_from, date_to)


@router.get("/methods")
async def get_payment_methods():
    """
    사용 가능한 결제 방법 목록 조회
    """
    return {
        "methods": [
            {
                "code": "card",
                "name": "신용카드",
                "description": "신용카드 및 체크카드",
                "icon": "credit-card"
            },
            {
                "code": "bank_transfer",
                "name": "계좌이체",
                "description": "실시간 계좌이체",
                "icon": "bank"
            },
            {
                "code": "kakao_pay",
                "name": "카카오페이",
                "description": "카카오페이 간편결제",
                "icon": "kakao"
            },
            {
                "code": "naver_pay",
                "name": "네이버페이",
                "description": "네이버페이 간편결제",
                "icon": "naver"
            },
            {
                "code": "toss_pay",
                "name": "토스페이",
                "description": "토스 간편결제",
                "icon": "toss"
            }
        ]
    }


@router.get("/installments")
async def get_installment_options():
    """
    할부 옵션 조회
    """
    return {
        "options": [
            {"months": 0, "name": "일시불", "fee_rate": 0},
            {"months": 2, "name": "2개월", "fee_rate": 0},
            {"months": 3, "name": "3개월", "fee_rate": 0},
            {"months": 6, "name": "6개월", "fee_rate": 2.5},
            {"months": 12, "name": "12개월", "fee_rate": 5.0},
            {"months": 24, "name": "24개월", "fee_rate": 7.5},
            {"months": 36, "name": "36개월", "fee_rate": 10.0}
        ]
    }


# 웹훅 엔드포인트 (PG사 콜백)
@router.post("/webhook/{pg_provider}")
async def payment_webhook(
    pg_provider: str,
    webhook_data: Dict[str, Any] = Body(...),
    payment_service: PaymentService = Depends(get_payment_service)
):
    """
    결제 웹훅 (PG사 콜백)
    
    PG사에서 결제 결과를 알려주는 웹훅 엔드포인트입니다.
    """
    try:
        # 웹훅 데이터에서 거래 ID 추출
        transaction_id = webhook_data.get("transaction_id") or webhook_data.get("merchant_uid")
        if not transaction_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="거래 ID가 없습니다."
            )
        
        # 결제 정보 조회
        payment = payment_service.get_payment_by_transaction_id(transaction_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="결제 정보를 찾을 수 없습니다."
            )
        
        # 웹훅 데이터 검증 및 처리
        webhook_status = webhook_data.get("status")
        if webhook_status == "paid":
            if payment.status != "completed":
                payment.status = "completed"
                payment.paid_at = datetime.utcnow()
                payment_service.db.commit()
        elif webhook_status == "failed":
            if payment.status not in ["failed", "completed"]:
                payment.status = "failed"
                payment.failed_at = datetime.utcnow()
                payment.failure_reason = webhook_data.get("fail_reason", "결제 실패")
                payment_service.db.commit()
        
        return {"status": "success", "message": "웹훅 처리 완료"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}