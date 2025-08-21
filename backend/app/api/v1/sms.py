import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.sms_service import sms_service
from app.services.verification_service import verification_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SendVerificationRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    purpose: str = Field(default="auth", description="인증 목적", example="auth")


class VerifyCodeRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    code: str = Field(..., description="인증번호", example="123456")
    purpose: str = Field(default="auth", description="인증 목적", example="auth")


class SendSMSRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    message: str = Field(..., description="메시지 내용", max_length=90)


@router.post("/send-verification", summary="인증번호 발송")
async def send_verification_code(request: SendVerificationRequest, db: Session = Depends(get_db)):
    """
    휴대폰 번호로 인증번호를 발송합니다.

    - **phone**: 인증번호를 받을 휴대폰 번호
    - **purpose**: 인증 목적 (auth, password_reset 등)
    """
    try:
        # 휴대폰 번호 형식 검증
        phone = request.phone.replace("-", "").replace(" ", "")
        if not phone.startswith("010") or len(phone) != 11:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바른 휴대폰 번호 형식이 아닙니다.")

        result = await verification_service.send_verification_code(db=db, phone=phone, purpose=request.purpose)

        if result["success"]:
            return {"message": result["message"], "expires_in": result["expires_in"]}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증번호 발송 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인증번호 발송 중 오류가 발생했습니다.")


@router.post("/verify-code", summary="인증번호 검증")
async def verify_verification_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    인증번호를 검증합니다.

    - **phone**: 인증번호를 받은 휴대폰 번호
    - **code**: 입력한 인증번호
    - **purpose**: 인증 목적
    """
    try:
        # 휴대폰 번호 형식 정리
        phone = request.phone.replace("-", "").replace(" ", "")

        result = verification_service.verify_code(db=db, phone=phone, code=request.code, purpose=request.purpose)

        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증번호 검증 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인증번호 검증 중 오류가 발생했습니다.")


@router.post("/send", summary="SMS 직접 발송")
async def send_sms_direct(request: SendSMSRequest):
    """
    SMS를 직접 발송합니다. (관리자용)

    - **phone**: 수신자 휴대폰 번호
    - **message**: 발송할 메시지 내용
    """
    try:
        # 휴대폰 번호 형식 검증
        phone = request.phone.replace("-", "").replace(" ", "")
        if not phone.startswith("010") or len(phone) != 11:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바른 휴대폰 번호 형식이 아닙니다.")

        result = await sms_service.send_sms(phone, request.message)

        if result["success"]:
            return {"message": "SMS가 발송되었습니다.", "message_id": result.get("message_id")}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SMS 발송 실패: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS 발송 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SMS 발송 중 오류가 발생했습니다.")
