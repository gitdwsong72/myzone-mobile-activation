import logging
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.order import Order
from app.models.user import User
from app.services.email_queue_service import email_queue_service
from app.services.email_service import email_service
from app.services.sms_service import sms_service

logger = logging.getLogger(__name__)


class NotificationService:
    """통합 알림 서비스"""

    def __init__(self):
        pass

    async def send_order_confirmation_notifications(
        self, db: Session, order: Order, user: Optional[User] = None
    ) -> Dict[str, Any]:
        """주문 확인 알림 발송 (SMS + 이메일)"""
        if not user:
            user = db.query(User).filter(User.id == order.user_id).first()

        if not user:
            logger.error(f"사용자를 찾을 수 없습니다: order_id={order.id}")
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        results = {"sms": {"success": False}, "email": {"success": False}}

        # SMS 발송
        try:
            sms_result = await sms_service.send_order_status_sms(
                phone=user.phone, order_number=order.order_number, status="접수완료"
            )
            results["sms"] = sms_result
        except Exception as e:
            logger.error(f"주문 확인 SMS 발송 실패: {str(e)}")
            results["sms"] = {"success": False, "error": str(e)}

        # 이메일 큐에 추가
        try:
            plan_name = order.plan.name if order.plan else "선택된 요금제"
            device_name = f"{order.device.brand} {order.device.model}" if order.device else "단말기 없음"
            phone_number = order.number.number if order.number else "번호 미선택"

            email_result = await email_queue_service.add_order_confirmation_to_queue(
                to_email=user.email,
                user_name=user.name,
                order_number=order.order_number,
                plan_name=plan_name,
                device_name=device_name,
                phone_number=phone_number,
                total_amount=f"{order.total_amount:,}",
                priority=1,
            )
            results["email"] = {"success": email_result}
        except Exception as e:
            logger.error(f"주문 확인 이메일 큐 추가 실패: {str(e)}")
            results["email"] = {"success": False, "error": str(e)}

        # 전체 성공 여부
        overall_success = results["sms"]["success"] or results["email"]["success"]

        logger.info(
            f"주문 확인 알림 발송 완료: order={order.order_number}, sms={results['sms']['success']}, email={results['email']['success']}"
        )

        return {"success": overall_success, "results": results}

    async def send_order_status_update_notifications(
        self, db: Session, order: Order, new_status: str, note: Optional[str] = None, user: Optional[User] = None
    ) -> Dict[str, Any]:
        """주문 상태 변경 알림 발송 (SMS + 이메일)"""
        if not user:
            user = db.query(User).filter(User.id == order.user_id).first()

        if not user:
            logger.error(f"사용자를 찾을 수 없습니다: order_id={order.id}")
            return {"success": False, "error": "사용자를 찾을 수 없습니다"}

        results = {"sms": {"success": False}, "email": {"success": False}}

        # SMS 상태 매핑
        sms_status_map = {"confirmed": "접수완료", "processing": "개통처리중", "completed": "개통완료", "cancelled": "반려"}

        # SMS 발송
        if new_status in sms_status_map:
            try:
                sms_result = await sms_service.send_order_status_sms(
                    phone=user.phone, order_number=order.order_number, status=sms_status_map[new_status]
                )
                results["sms"] = sms_result
            except Exception as e:
                logger.error(f"주문 상태 변경 SMS 발송 실패: {str(e)}")
                results["sms"] = {"success": False, "error": str(e)}

        # 이메일 큐에 추가
        try:
            email_result = await email_queue_service.add_order_status_update_to_queue(
                to_email=user.email,
                user_name=user.name,
                order_number=order.order_number,
                status=new_status,
                note=note,
                priority=1,
            )
            results["email"] = {"success": email_result}
        except Exception as e:
            logger.error(f"주문 상태 변경 이메일 큐 추가 실패: {str(e)}")
            results["email"] = {"success": False, "error": str(e)}

        # 전체 성공 여부
        overall_success = results["sms"]["success"] or results["email"]["success"]

        logger.info(
            f"주문 상태 변경 알림 발송 완료: order={order.order_number}, status={new_status}, sms={results['sms']['success']}, email={results['email']['success']}"
        )

        return {"success": overall_success, "results": results}

    async def send_welcome_notifications(self, user: User) -> Dict[str, Any]:
        """가입 환영 알림 발송 (SMS + 이메일)"""
        results = {"sms": {"success": False}, "email": {"success": False}}

        # 환영 SMS 발송
        try:
            sms_result = await sms_service.send_welcome_sms(phone=user.phone, name=user.name)
            results["sms"] = sms_result
        except Exception as e:
            logger.error(f"환영 SMS 발송 실패: {str(e)}")
            results["sms"] = {"success": False, "error": str(e)}

        # 환영 이메일 발송
        try:
            email_result = await email_service.send_welcome_email(to_email=user.email, user_name=user.name)
            results["email"] = email_result
        except Exception as e:
            logger.error(f"환영 이메일 발송 실패: {str(e)}")
            results["email"] = {"success": False, "error": str(e)}

        # 전체 성공 여부
        overall_success = results["sms"]["success"] or results["email"]["success"]

        logger.info(
            f"환영 알림 발송 완료: user={user.name}, sms={results['sms']['success']}, email={results['email']['success']}"
        )

        return {"success": overall_success, "results": results}

    async def send_verification_sms(self, db: Session, phone: str, purpose: str = "auth") -> Dict[str, Any]:
        """인증번호 SMS 발송"""
        from app.services.verification_service import verification_service

        try:
            result = await verification_service.send_verification_code(db=db, phone=phone, purpose=purpose)

            logger.info(f"인증번호 SMS 발송: phone={phone}, success={result['success']}")
            return result

        except Exception as e:
            logger.error(f"인증번호 SMS 발송 실패: {str(e)}")
            return {"success": False, "error": str(e), "message": "인증번호 발송 중 오류가 발생했습니다."}

    def verify_sms_code(self, db: Session, phone: str, code: str, purpose: str = "auth") -> Dict[str, Any]:
        """인증번호 검증"""
        from app.services.verification_service import verification_service

        try:
            result = verification_service.verify_code(db=db, phone=phone, code=code, purpose=purpose)

            logger.info(f"인증번호 검증: phone={phone}, success={result['success']}")
            return result

        except Exception as e:
            logger.error(f"인증번호 검증 실패: {str(e)}")
            return {"success": False, "error": str(e), "message": "인증번호 검증 중 오류가 발생했습니다."}


# 싱글톤 인스턴스
notification_service = NotificationService()
