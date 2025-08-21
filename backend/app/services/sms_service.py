import json
import logging
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)


class SMSService:
    def __init__(self):
        self.api_key = settings.SMS_API_KEY
        self.api_url = settings.SMS_API_URL
        self.sender = settings.SMS_SENDER

    async def send_sms(self, phone: str, message: str) -> Dict[str, Any]:
        """SMS 발송"""
        try:
            if not self.api_key:
                logger.warning("SMS API 키가 설정되지 않았습니다. 개발 모드에서는 로그로 대체합니다.")
                logger.info(f"SMS 발송 (개발모드): {phone} -> {message}")
                return {"success": True, "message_id": f"dev_{datetime.now().timestamp()}", "status": "sent"}

            headers = {"Authorization": f"HMAC-SHA256 apiKey={self.api_key}", "Content-Type": "application/json"}

            payload = {"message": {"to": phone, "from": self.sender, "text": message}}

            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=30.0)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"SMS 발송 성공: {phone}")
                    return {"success": True, "message_id": result.get("messageId"), "status": "sent"}
                else:
                    logger.error(f"SMS 발송 실패: {response.status_code} - {response.text}")
                    return {"success": False, "error": f"SMS 발송 실패: {response.status_code}", "status": "failed"}

        except Exception as e:
            logger.error(f"SMS 발송 중 오류 발생: {str(e)}")
            return {"success": False, "error": str(e), "status": "error"}

    def generate_verification_code(self, length: int = 6) -> str:
        """인증번호 생성"""
        return "".join(random.choices(string.digits, k=length))

    async def send_verification_sms(self, phone: str, code: str) -> Dict[str, Any]:
        """본인인증 SMS 발송"""
        message = f"[MyZone] 본인인증 번호는 [{code}]입니다. 3분 이내에 입력해주세요."

        result = await self.send_sms(phone, message)

        if result["success"]:
            logger.info(f"본인인증 SMS 발송 완료: {phone}")
        else:
            logger.error(f"본인인증 SMS 발송 실패: {phone} - {result.get('error')}")

        return result

    async def send_order_status_sms(self, phone: str, order_number: str, status: str) -> Dict[str, Any]:
        """주문 상태 변경 알림 SMS 발송"""
        status_messages = {
            "접수완료": f"[MyZone] 개통신청이 접수되었습니다. 신청번호: {order_number}",
            "심사중": f"[MyZone] 개통신청 심사가 진행중입니다. 신청번호: {order_number}",
            "개통처리중": f"[MyZone] 개통 처리가 시작되었습니다. 신청번호: {order_number}",
            "개통완료": f"[MyZone] 개통이 완료되었습니다! 신청번호: {order_number}. 서비스 이용을 시작하세요.",
            "반려": f"[MyZone] 개통신청이 반려되었습니다. 신청번호: {order_number}. 자세한 내용은 고객센터로 문의하세요.",
        }

        message = status_messages.get(status, f"[MyZone] 주문 상태가 변경되었습니다. 신청번호: {order_number}")

        result = await self.send_sms(phone, message)

        if result["success"]:
            logger.info(f"주문 상태 알림 SMS 발송 완료: {phone} - {status}")
        else:
            logger.error(f"주문 상태 알림 SMS 발송 실패: {phone} - {result.get('error')}")

        return result

    async def send_welcome_sms(self, phone: str, name: str) -> Dict[str, Any]:
        """가입 환영 SMS 발송"""
        message = f"[MyZone] {name}님, MyZone 가입을 환영합니다! 최고의 모바일 서비스를 경험하세요."

        result = await self.send_sms(phone, message)

        if result["success"]:
            logger.info(f"환영 SMS 발송 완료: {phone}")
        else:
            logger.error(f"환영 SMS 발송 실패: {phone} - {result.get('error')}")

        return result


# 싱글톤 인스턴스
sms_service = SMSService()
