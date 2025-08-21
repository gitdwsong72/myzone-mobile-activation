import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.verification import VerificationCode
from app.services.sms_service import sms_service

logger = logging.getLogger(__name__)


class VerificationService:
    def __init__(self):
        self.code_expiry_minutes = 3  # 인증번호 유효시간 3분

    async def send_verification_code(self, db: Session, phone: str, purpose: str = "auth") -> Dict[str, Any]:
        """인증번호 발송"""
        try:
            # 기존 미사용 인증번호 무효화
            existing_codes = (
                db.query(VerificationCode)
                .filter(
                    VerificationCode.phone == phone,
                    VerificationCode.purpose == purpose,
                    VerificationCode.is_used == False,
                    VerificationCode.expires_at > datetime.now(),
                )
                .all()
            )

            for code in existing_codes:
                code.is_used = True

            # 새 인증번호 생성
            verification_code = sms_service.generate_verification_code()
            expires_at = datetime.now() + timedelta(minutes=self.code_expiry_minutes)

            # 데이터베이스에 저장
            db_verification = VerificationCode(phone=phone, code=verification_code, purpose=purpose, expires_at=expires_at)
            db.add(db_verification)
            db.commit()

            # SMS 발송
            sms_result = await sms_service.send_verification_sms(phone, verification_code)

            if sms_result["success"]:
                logger.info(f"인증번호 발송 성공: {phone}")
                return {
                    "success": True,
                    "message": "인증번호가 발송되었습니다.",
                    "expires_in": self.code_expiry_minutes * 60,  # 초 단위
                }
            else:
                # SMS 발송 실패 시 DB 레코드 삭제
                db.delete(db_verification)
                db.commit()
                return {"success": False, "message": "인증번호 발송에 실패했습니다.", "error": sms_result.get("error")}

        except Exception as e:
            logger.error(f"인증번호 발송 중 오류: {str(e)}")
            db.rollback()
            return {"success": False, "message": "인증번호 발송 중 오류가 발생했습니다.", "error": str(e)}

    def verify_code(self, db: Session, phone: str, code: str, purpose: str = "auth") -> Dict[str, Any]:
        """인증번호 검증"""
        try:
            # 인증번호 조회
            verification = (
                db.query(VerificationCode)
                .filter(
                    VerificationCode.phone == phone,
                    VerificationCode.code == code,
                    VerificationCode.purpose == purpose,
                    VerificationCode.is_used == False,
                    VerificationCode.expires_at > datetime.now(),
                )
                .first()
            )

            if not verification:
                return {"success": False, "message": "유효하지 않거나 만료된 인증번호입니다."}

            # 인증번호 사용 처리
            verification.is_used = True
            verification.used_at = datetime.now()
            db.commit()

            logger.info(f"인증번호 검증 성공: {phone}")
            return {"success": True, "message": "인증이 완료되었습니다."}

        except Exception as e:
            logger.error(f"인증번호 검증 중 오류: {str(e)}")
            db.rollback()
            return {"success": False, "message": "인증번호 검증 중 오류가 발생했습니다.", "error": str(e)}

    def cleanup_expired_codes(self, db: Session) -> int:
        """만료된 인증번호 정리"""
        try:
            expired_count = db.query(VerificationCode).filter(VerificationCode.expires_at < datetime.now()).delete()

            db.commit()
            logger.info(f"만료된 인증번호 {expired_count}개 정리 완료")
            return expired_count

        except Exception as e:
            logger.error(f"인증번호 정리 중 오류: {str(e)}")
            db.rollback()
            return 0


# 싱글톤 인스턴스
verification_service = VerificationService()
