import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.services.email_queue_service import email_queue_service
from app.services.notification_service import notification_service

logger = logging.getLogger(__name__)

router = APIRouter()


class SendEmailRequest(BaseModel):
    to_email: EmailStr = Field(..., description="수신자 이메일")
    subject: str = Field(..., description="제목", max_length=500)
    html_content: str = Field(..., description="HTML 내용")
    text_content: Optional[str] = Field(None, description="텍스트 내용")
    priority: int = Field(default=0, description="우선순위 (0: 낮음, 1: 보통, 2: 높음)")


class SendBulkEmailRequest(BaseModel):
    to_emails: List[EmailStr] = Field(..., description="수신자 이메일 목록")
    subject: str = Field(..., description="제목", max_length=500)
    html_content: str = Field(..., description="HTML 내용")
    text_content: Optional[str] = Field(None, description="텍스트 내용")
    priority: int = Field(default=0, description="우선순위")


class SendSMSRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    message: str = Field(..., description="메시지 내용", max_length=90)


class SendVerificationRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    purpose: str = Field(default="auth", description="인증 목적")


class VerifyCodeRequest(BaseModel):
    phone: str = Field(..., description="휴대폰 번호", example="010-1234-5678")
    code: str = Field(..., description="인증번호", example="123456")
    purpose: str = Field(default="auth", description="인증 목적")


@router.post("/email/send", summary="이메일 발송")
async def send_email(
    request: SendEmailRequest, background_tasks: BackgroundTasks, current_admin: Admin = Depends(get_current_admin)
):
    """
    이메일을 큐에 추가하여 발송합니다. (관리자 전용)

    - **to_email**: 수신자 이메일 주소
    - **subject**: 이메일 제목
    - **html_content**: HTML 형식의 이메일 내용
    - **text_content**: 텍스트 형식의 이메일 내용 (선택사항)
    - **priority**: 우선순위 (0: 낮음, 1: 보통, 2: 높음)
    """
    try:
        result = await email_queue_service.add_to_queue(
            to_email=request.to_email,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content,
            priority=request.priority,
        )

        if result:
            return {
                "message": "이메일이 발송 큐에 추가되었습니다.",
                "to_email": request.to_email,
                "priority": request.priority,
            }
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="이메일 큐 추가에 실패했습니다.")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"이메일 발송 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="이메일 발송 중 오류가 발생했습니다.")


@router.post("/email/send-bulk", summary="대량 이메일 발송")
async def send_bulk_email(
    request: SendBulkEmailRequest, background_tasks: BackgroundTasks, current_admin: Admin = Depends(get_current_admin)
):
    """
    여러 수신자에게 동일한 이메일을 발송합니다. (관리자 전용)

    - **to_emails**: 수신자 이메일 주소 목록
    - **subject**: 이메일 제목
    - **html_content**: HTML 형식의 이메일 내용
    - **text_content**: 텍스트 형식의 이메일 내용 (선택사항)
    - **priority**: 우선순위
    """
    try:
        success_count = 0
        failed_emails = []

        for email in request.to_emails:
            try:
                result = await email_queue_service.add_to_queue(
                    to_email=email,
                    subject=request.subject,
                    html_content=request.html_content,
                    text_content=request.text_content,
                    priority=request.priority,
                )

                if result:
                    success_count += 1
                else:
                    failed_emails.append(email)

            except Exception as e:
                logger.error(f"대량 이메일 큐 추가 실패: {email} - {str(e)}")
                failed_emails.append(email)

        return {
            "message": f"{success_count}개의 이메일이 발송 큐에 추가되었습니다.",
            "success_count": success_count,
            "total_count": len(request.to_emails),
            "failed_emails": failed_emails,
        }

    except Exception as e:
        logger.error(f"대량 이메일 발송 API 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="대량 이메일 발송 중 오류가 발생했습니다."
        )


@router.post("/sms/send", summary="SMS 발송")
async def send_sms(request: SendSMSRequest, current_admin: Admin = Depends(get_current_admin)):
    """
    SMS를 발송합니다. (관리자 전용)

    - **phone**: 수신자 휴대폰 번호
    - **message**: 발송할 메시지 내용
    """
    try:
        from app.services.sms_service import sms_service

        # 휴대폰 번호 형식 검증
        phone = request.phone.replace("-", "").replace(" ", "")
        if not phone.startswith("010") or len(phone) != 11:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="올바른 휴대폰 번호 형식이 아닙니다.")

        result = await sms_service.send_sms(phone, request.message)

        if result["success"]:
            return {"message": "SMS가 발송되었습니다.", "phone": phone, "message_id": result.get("message_id")}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"SMS 발송 실패: {result.get('error')}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SMS 발송 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="SMS 발송 중 오류가 발생했습니다.")


@router.post("/verification/send", summary="인증번호 발송")
async def send_verification(request: SendVerificationRequest, db: Session = Depends(get_db)):
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

        result = await notification_service.send_verification_sms(db=db, phone=phone, purpose=request.purpose)

        if result["success"]:
            return {"message": result["message"], "expires_in": result.get("expires_in")}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증번호 발송 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인증번호 발송 중 오류가 발생했습니다.")


@router.post("/verification/verify", summary="인증번호 검증")
async def verify_code(request: VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    인증번호를 검증합니다.

    - **phone**: 인증번호를 받은 휴대폰 번호
    - **code**: 입력한 인증번호
    - **purpose**: 인증 목적
    """
    try:
        # 휴대폰 번호 형식 정리
        phone = request.phone.replace("-", "").replace(" ", "")

        result = notification_service.verify_sms_code(db=db, phone=phone, code=request.code, purpose=request.purpose)

        if result["success"]:
            return {"message": result["message"]}
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인증번호 검증 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="인증번호 검증 중 오류가 발생했습니다.")


@router.get("/queue/status", summary="이메일 큐 상태 조회")
async def get_queue_status(current_admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)):
    """
    이메일 큐 상태를 조회합니다. (관리자 전용)
    """
    try:
        # 데이터베이스 큐 상태 조회
        from app.services.email_queue_service import EmailQueue, EmailStatus

        pending_count = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.PENDING).count()
        processing_count = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.PROCESSING).count()
        sent_count = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.SENT).count()
        failed_count = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.FAILED).count()
        retry_count = db.query(EmailQueue).filter(EmailQueue.status == EmailStatus.RETRY).count()

        return {
            "queue_status": {
                "pending": pending_count,
                "processing": processing_count,
                "sent": sent_count,
                "failed": failed_count,
                "retry": retry_count,
                "total": pending_count + processing_count + sent_count + failed_count + retry_count,
            },
            "is_processing": email_queue_service.is_processing,
        }

    except Exception as e:
        logger.error(f"큐 상태 조회 API 오류: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="큐 상태 조회 중 오류가 발생했습니다.")
