from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from decimal import Decimal
import uuid
import hashlib
import hmac
import json
import httpx

from ..models.payment import Payment
from ..models.order import Order
from ..schemas.payment import PaymentCreate, PaymentUpdate


class PaymentService:
    """결제 서비스"""
    
    # 결제 방법 정의
    PAYMENT_METHODS = {
        "card": "신용카드",
        "bank_transfer": "계좌이체",
        "kakao_pay": "카카오페이",
        "naver_pay": "네이버페이",
        "toss_pay": "토스페이"
    }
    
    # 결제 상태 정의
    PAYMENT_STATUSES = {
        "pending": "결제 대기",
        "processing": "결제 처리 중",
        "completed": "결제 완료",
        "failed": "결제 실패",
        "cancelled": "결제 취소",
        "refunded": "환불 완료"
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_payment_by_id(self, payment_id: int) -> Payment:
        """ID로 결제 조회"""
        payment = self.db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="결제 정보를 찾을 수 없습니다."
            )
        return payment
    
    def get_payment_by_order_id(self, order_id: int) -> Optional[Payment]:
        """주문 ID로 결제 조회"""
        return self.db.query(Payment).filter(Payment.order_id == order_id).first()
    
    def get_payment_by_transaction_id(self, transaction_id: str) -> Optional[Payment]:
        """거래 ID로 결제 조회"""
        return self.db.query(Payment).filter(Payment.transaction_id == transaction_id).first()
    
    def create_payment(self, payment_data: PaymentCreate) -> Payment:
        """결제 생성"""
        # 주문 존재 확인
        order = self.db.query(Order).filter(Order.id == payment_data.order_id).first()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="주문을 찾을 수 없습니다."
            )
        
        # 이미 결제가 있는지 확인
        existing_payment = self.get_payment_by_order_id(payment_data.order_id)
        if existing_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 결제가 진행 중이거나 완료된 주문입니다."
            )
        
        # 결제 금액 검증
        if payment_data.amount != order.total_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="결제 금액이 주문 금액과 일치하지 않습니다."
            )
        
        # 결제 생성
        payment = Payment(**payment_data.model_dump())
        payment.transaction_id = self._generate_transaction_id()
        
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def process_payment(self, payment_id: int, pg_data: Dict[str, Any]) -> Payment:
        """결제 처리"""
        payment = self.get_payment_by_id(payment_id)
        
        if payment.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="처리할 수 없는 결제 상태입니다."
            )
        
        # 결제 상태를 처리 중으로 변경
        payment.status = "processing"
        self.db.commit()
        
        try:
            # PG사별 결제 처리
            if payment.payment_method == "card":
                result = self._process_card_payment(payment, pg_data)
            elif payment.payment_method == "kakao_pay":
                result = self._process_kakao_pay(payment, pg_data)
            elif payment.payment_method == "naver_pay":
                result = self._process_naver_pay(payment, pg_data)
            elif payment.payment_method == "bank_transfer":
                result = self._process_bank_transfer(payment, pg_data)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="지원하지 않는 결제 방법입니다."
                )
            
            if result["success"]:
                # 결제 성공
                payment.status = "completed"
                payment.paid_at = datetime.utcnow()
                payment.pg_transaction_id = result.get("pg_transaction_id")
                payment.receipt_url = result.get("receipt_url")
                
                # 카드 결제인 경우 카드 정보 저장
                if payment.payment_method == "card" and "card_info" in result:
                    card_info = result["card_info"]
                    payment.card_company = card_info.get("company")
                    payment.card_number_masked = card_info.get("number_masked")
                    payment.installment_months = card_info.get("installment_months", 0)
                
                # 주문 상태 업데이트
                order = payment.order
                if order.status == "pending":
                    order.status = "confirmed"
                
            else:
                # 결제 실패
                payment.status = "failed"
                payment.failed_at = datetime.utcnow()
                payment.failure_reason = result.get("error_message", "결제 처리 중 오류가 발생했습니다.")
            
            self.db.commit()
            self.db.refresh(payment)
            return payment
            
        except Exception as e:
            # 결제 처리 중 예외 발생
            payment.status = "failed"
            payment.failed_at = datetime.utcnow()
            payment.failure_reason = str(e)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="결제 처리 중 오류가 발생했습니다."
            )
    
    def cancel_payment(self, payment_id: int, reason: str) -> Payment:
        """결제 취소"""
        payment = self.get_payment_by_id(payment_id)
        
        if payment.status not in ["pending", "processing"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="취소할 수 없는 결제 상태입니다."
            )
        
        payment.status = "cancelled"
        payment.cancelled_at = datetime.utcnow()
        payment.cancel_reason = reason
        
        self.db.commit()
        self.db.refresh(payment)
        return payment
    
    def refund_payment(self, payment_id: int, refund_amount: Decimal, reason: str) -> Payment:
        """결제 환불"""
        payment = self.get_payment_by_id(payment_id)
        
        if not payment.is_refundable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="환불할 수 없는 결제입니다."
            )
        
        if refund_amount > payment.remaining_refund_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="환불 가능 금액을 초과했습니다."
            )
        
        try:
            # PG사 환불 처리
            refund_result = self._process_refund(payment, refund_amount, reason)
            
            if refund_result["success"]:
                payment.refund_amount += refund_amount
                payment.refund_reason = reason
                payment.refunded_at = datetime.utcnow()
                
                # 전액 환불인 경우 상태 변경
                if payment.refund_amount >= payment.amount:
                    payment.status = "refunded"
                
                self.db.commit()
                self.db.refresh(payment)
                return payment
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=refund_result.get("error_message", "환불 처리 중 오류가 발생했습니다.")
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="환불 처리 중 오류가 발생했습니다."
            )
    
    def verify_payment(self, payment_id: int, verification_data: Dict[str, Any]) -> bool:
        """결제 검증"""
        payment = self.get_payment_by_id(payment_id)
        
        # PG사별 검증 로직
        if payment.pg_provider == "toss":
            return self._verify_toss_payment(payment, verification_data)
        elif payment.pg_provider == "iamport":
            return self._verify_iamport_payment(payment, verification_data)
        else:
            # 기본 검증 로직
            return self._verify_default_payment(payment, verification_data)
    
    def get_payment_statistics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """결제 통계"""
        query = self.db.query(Payment)
        
        if date_from:
            query = query.filter(Payment.created_at >= date_from)
        if date_to:
            query = query.filter(Payment.created_at <= date_to)
        
        # 전체 결제 수
        total_payments = query.count()
        
        # 성공한 결제 수와 금액
        completed_payments = query.filter(Payment.status == "completed")
        completed_count = completed_payments.count()
        total_amount = completed_payments.with_entities(func.sum(Payment.amount)).scalar() or Decimal('0')
        
        # 실패한 결제 수
        failed_count = query.filter(Payment.status == "failed").count()
        
        # 결제 방법별 통계
        method_stats = (
            query.filter(Payment.status == "completed")
            .with_entities(
                Payment.payment_method,
                func.count(Payment.id).label('count'),
                func.sum(Payment.amount).label('amount')
            )
            .group_by(Payment.payment_method)
            .all()
        )
        
        return {
            "total_payments": total_payments,
            "completed_count": completed_count,
            "failed_count": failed_count,
            "success_rate": (completed_count / total_payments * 100) if total_payments > 0 else 0,
            "total_amount": total_amount,
            "method_stats": [
                {
                    "method": method,
                    "count": count,
                    "amount": amount
                }
                for method, count, amount in method_stats
            ]
        }
    
    def _generate_transaction_id(self) -> str:
        """거래 ID 생성"""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        return f"PAY{timestamp}{unique_id}"
    
    def _process_card_payment(self, payment: Payment, pg_data: Dict[str, Any]) -> Dict[str, Any]:
        """신용카드 결제 처리"""
        # 실제 PG사 API 호출 로직
        # 여기서는 시뮬레이션
        
        # 카드 정보 검증
        card_number = pg_data.get("card_number", "")
        expiry_date = pg_data.get("expiry_date", "")
        cvc = pg_data.get("cvc", "")
        
        if not all([card_number, expiry_date, cvc]):
            return {"success": False, "error_message": "카드 정보가 불완전합니다."}
        
        # 시뮬레이션: 90% 성공률
        import random
        if random.random() < 0.9:
            return {
                "success": True,
                "pg_transaction_id": f"CARD_{uuid.uuid4().hex[:12]}",
                "receipt_url": f"https://receipt.example.com/{payment.transaction_id}",
                "card_info": {
                    "company": "신한카드",
                    "number_masked": f"****-****-****-{card_number[-4:]}",
                    "installment_months": pg_data.get("installment_months", 0)
                }
            }
        else:
            return {"success": False, "error_message": "카드사 승인이 거절되었습니다."}
    
    def _process_kakao_pay(self, payment: Payment, pg_data: Dict[str, Any]) -> Dict[str, Any]:
        """카카오페이 결제 처리"""
        # 카카오페이 API 호출 시뮬레이션
        return {
            "success": True,
            "pg_transaction_id": f"KAKAO_{uuid.uuid4().hex[:12]}",
            "receipt_url": f"https://receipt.kakaopay.com/{payment.transaction_id}"
        }
    
    def _process_naver_pay(self, payment: Payment, pg_data: Dict[str, Any]) -> Dict[str, Any]:
        """네이버페이 결제 처리"""
        # 네이버페이 API 호출 시뮬레이션
        return {
            "success": True,
            "pg_transaction_id": f"NAVER_{uuid.uuid4().hex[:12]}",
            "receipt_url": f"https://receipt.naverpay.com/{payment.transaction_id}"
        }
    
    def _process_bank_transfer(self, payment: Payment, pg_data: Dict[str, Any]) -> Dict[str, Any]:
        """계좌이체 결제 처리"""
        # 계좌이체 API 호출 시뮬레이션
        return {
            "success": True,
            "pg_transaction_id": f"BANK_{uuid.uuid4().hex[:12]}",
            "receipt_url": f"https://receipt.bank.com/{payment.transaction_id}"
        }
    
    def _process_refund(self, payment: Payment, refund_amount: Decimal, reason: str) -> Dict[str, Any]:
        """환불 처리"""
        # PG사 환불 API 호출 시뮬레이션
        return {
            "success": True,
            "refund_transaction_id": f"REFUND_{uuid.uuid4().hex[:12]}"
        }
    
    def _verify_toss_payment(self, payment: Payment, verification_data: Dict[str, Any]) -> bool:
        """토스 결제 검증"""
        # 토스 결제 검증 로직
        return True
    
    def _verify_iamport_payment(self, payment: Payment, verification_data: Dict[str, Any]) -> bool:
        """아임포트 결제 검증"""
        # 아임포트 결제 검증 로직
        return True
    
    def _verify_default_payment(self, payment: Payment, verification_data: Dict[str, Any]) -> bool:
        """기본 결제 검증"""
        # 기본 검증 로직
        return True