"""
GDPR 준수 개인정보 처리 모듈
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
import json
import os

from ..models.user import User
from ..models.order import Order
from ..models.payment import Payment
from ..models.order_status_history import OrderStatusHistory
from ..core.encryption import encryption_service, decrypt_personal_data

logger = logging.getLogger(__name__)


class GDPRService:
    """GDPR 준수 개인정보 처리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """
        사용자 개인정보 내보내기 (GDPR Article 20 - Right to data portability)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            사용자의 모든 개인정보
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 사용자 기본 정보 (복호화)
        try:
            decrypted_name = decrypt_personal_data(user.name)
            decrypted_address = decrypt_personal_data(user.address)
        except Exception as e:
            logger.error(f"개인정보 복호화 실패: {e}")
            decrypted_name = "[복호화 실패]"
            decrypted_address = "[복호화 실패]"
        
        user_data = {
            "personal_info": {
                "id": user.id,
                "name": decrypted_name,
                "phone": user.phone,
                "email": user.email,
                "birth_date": user.birth_date.isoformat() if user.birth_date else None,
                "gender": user.gender,
                "address": decrypted_address,
                "is_verified": user.is_verified,
                "verification_method": user.verification_method,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        }
        
        # 주문 정보
        orders = self.db.query(Order).filter(Order.user_id == user_id).all()
        user_data["orders"] = []
        
        for order in orders:
            order_info = {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "total_amount": float(order.total_amount) if order.total_amount else 0,
                "delivery_address": order.delivery_address,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None
            }
            
            # 결제 정보
            payments = self.db.query(Payment).filter(Payment.order_id == order.id).all()
            order_info["payments"] = [
                {
                    "id": payment.id,
                    "payment_method": payment.payment_method,
                    "amount": float(payment.amount) if payment.amount else 0,
                    "status": payment.status,
                    "transaction_id": payment.transaction_id,
                    "paid_at": payment.paid_at.isoformat() if payment.paid_at else None
                }
                for payment in payments
            ]
            
            # 주문 상태 이력
            status_history = self.db.query(OrderStatusHistory).filter(
                OrderStatusHistory.order_id == order.id
            ).all()
            order_info["status_history"] = [
                {
                    "id": history.id,
                    "status": history.status,
                    "note": history.note,
                    "created_at": history.created_at.isoformat() if history.created_at else None
                }
                for history in status_history
            ]
            
            user_data["orders"].append(order_info)
        
        # 데이터 처리 로그
        user_data["data_processing_log"] = {
            "export_date": datetime.utcnow().isoformat(),
            "export_reason": "GDPR Article 20 - Right to data portability",
            "data_retention_period": "주문 완료 후 5년",
            "legal_basis": "계약 이행 및 법적 의무 준수"
        }
        
        logger.info(f"사용자 개인정보 내보내기 완료: {user_id}")
        return user_data
    
    def anonymize_user_data(self, user_id: int, reason: str = "사용자 요청") -> bool:
        """
        사용자 개인정보 익명화 (GDPR Article 17 - Right to erasure)
        
        Args:
            user_id: 사용자 ID
            reason: 익명화 사유
            
        Returns:
            익명화 성공 여부
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 진행 중인 주문 확인
        active_orders = self.db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.status.in_(["pending", "processing", "confirmed"])
            )
        ).count()
        
        if active_orders > 0:
            raise ValueError("진행 중인 주문이 있어 개인정보를 익명화할 수 없습니다.")
        
        # 개인정보 익명화
        anonymous_id = f"anonymous_{user_id}_{int(datetime.utcnow().timestamp())}"
        
        user.name = "[익명화된 사용자]"
        user.phone = f"000-0000-{user_id % 10000:04d}"  # 고유성 유지를 위한 ID 기반 번호
        user.email = f"{anonymous_id}@anonymized.local"
        user.address = "[익명화됨]"
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # 주문의 배송 주소도 익명화
        orders = self.db.query(Order).filter(Order.user_id == user_id).all()
        for order in orders:
            order.delivery_address = "[익명화된 주소]"
        
        self.db.commit()
        
        # 익명화 로그 기록
        self._log_gdpr_action(user_id, "anonymization", reason)
        
        logger.info(f"사용자 개인정보 익명화 완료: {user_id}, 사유: {reason}")
        return True
    
    def delete_user_data(self, user_id: int, reason: str = "사용자 요청") -> bool:
        """
        사용자 개인정보 완전 삭제 (GDPR Article 17 - Right to erasure)
        
        Args:
            user_id: 사용자 ID
            reason: 삭제 사유
            
        Returns:
            삭제 성공 여부
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        # 법적 보존 의무 확인 (주문 완료 후 5년)
        recent_orders = self.db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.created_at > datetime.utcnow() - timedelta(days=5*365),
                Order.status == "completed"
            )
        ).count()
        
        if recent_orders > 0:
            # 법적 보존 의무가 있는 경우 익명화만 수행
            return self.anonymize_user_data(user_id, f"{reason} (법적 보존 의무로 익명화)")
        
        # 완전 삭제 가능한 경우
        try:
            # 관련 데이터 삭제 (CASCADE로 처리되지만 명시적으로 확인)
            self.db.query(OrderStatusHistory).filter(
                OrderStatusHistory.order_id.in_(
                    self.db.query(Order.id).filter(Order.user_id == user_id)
                )
            ).delete(synchronize_session=False)
            
            self.db.query(Payment).filter(
                Payment.order_id.in_(
                    self.db.query(Order.id).filter(Order.user_id == user_id)
                )
            ).delete(synchronize_session=False)
            
            self.db.query(Order).filter(Order.user_id == user_id).delete()
            self.db.query(User).filter(User.id == user_id).delete()
            
            self.db.commit()
            
            # 삭제 로그 기록 (별도 테이블에)
            self._log_gdpr_action(user_id, "deletion", reason)
            
            logger.info(f"사용자 개인정보 완전 삭제 완료: {user_id}, 사유: {reason}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"사용자 개인정보 삭제 실패: {user_id}, 오류: {e}")
            raise
    
    def get_data_processing_info(self, user_id: int) -> Dict[str, Any]:
        """
        개인정보 처리 현황 조회 (GDPR Article 13, 14 - Information to be provided)
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            개인정보 처리 현황
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("사용자를 찾을 수 없습니다.")
        
        return {
            "data_controller": {
                "name": "MyZone 통신서비스",
                "contact": "privacy@myzone.com",
                "dpo_contact": "dpo@myzone.com"
            },
            "processing_purposes": [
                "휴대폰 개통 서비스 제공",
                "고객 지원 및 문의 처리",
                "법적 의무 준수",
                "서비스 개선 및 통계 분석"
            ],
            "legal_basis": [
                "계약 이행 (GDPR Article 6(1)(b))",
                "법적 의무 준수 (GDPR Article 6(1)(c))",
                "정당한 이익 (GDPR Article 6(1)(f))"
            ],
            "data_categories": [
                "신원 정보 (이름, 생년월일, 성별)",
                "연락처 정보 (전화번호, 이메일, 주소)",
                "거래 정보 (주문, 결제 내역)",
                "기술 정보 (IP 주소, 쿠키)"
            ],
            "retention_period": {
                "personal_info": "서비스 이용 종료 후 즉시 삭제 또는 익명화",
                "transaction_records": "거래 완료 후 5년 (전자상거래법)",
                "marketing_consent": "동의 철회 시 즉시 삭제"
            },
            "rights": [
                "정보 접근권 (Article 15)",
                "정정권 (Article 16)",
                "삭제권 (Article 17)",
                "처리 제한권 (Article 18)",
                "데이터 이동권 (Article 20)",
                "이의제기권 (Article 21)"
            ],
            "data_transfers": {
                "third_countries": "없음",
                "safeguards": "EU 적정성 결정 또는 표준 계약 조항"
            },
            "automated_decision_making": {
                "exists": False,
                "description": "자동화된 의사결정 없음"
            }
        }
    
    def _log_gdpr_action(self, user_id: int, action: str, reason: str):
        """GDPR 관련 작업 로그 기록"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "action": action,
            "reason": reason,
            "ip_address": "system",  # 실제 구현에서는 요청 IP 기록
            "user_agent": "system"
        }
        
        # 로그 파일에 기록 (실제 구현에서는 별도 로그 시스템 사용)
        log_file = os.path.join("logs", "gdpr_actions.log")
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


from ..core.deps import get_db
from fastapi import Depends

def get_gdpr_service(db: Session = Depends(get_db)) -> GDPRService:
    """GDPR 서비스 의존성 주입"""
    return GDPRService(db)