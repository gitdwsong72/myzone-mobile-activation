import asyncio
import logging
import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

from jinja2 import Environment, FileSystemLoader, Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM

        # Jinja2 템플릿 환경 설정
        template_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        if os.path.exists(template_dir):
            self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        else:
            self.jinja_env = None
            logger.warning(f"이메일 템플릿 디렉토리를 찾을 수 없습니다: {template_dir}")

        # 스레드 풀 실행기 (비동기 이메일 발송용)
        self.executor = ThreadPoolExecutor(max_workers=5)

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """동기 이메일 발송"""
        try:
            if not self.smtp_user or not self.smtp_password:
                logger.warning("SMTP 설정이 없습니다. 개발 모드에서는 로그로 대체합니다.")
                logger.info(f"이메일 발송 (개발모드): {to_email} -> {subject}")
                return {"success": True, "message_id": f"dev_{datetime.now().timestamp()}", "status": "sent"}

            # 이메일 메시지 생성
            msg = MIMEMultipart("alternative")
            msg["From"] = self.email_from
            msg["To"] = to_email
            msg["Subject"] = subject

            # 텍스트 버전 추가
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                msg.attach(text_part)

            # HTML 버전 추가
            html_part = MIMEText(html_content, "html", "utf-8")
            msg.attach(html_part)

            # 첨부파일 추가
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as attachment:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(file_path)}")
                            msg.attach(part)

            # SMTP 서버 연결 및 발송
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"이메일 발송 성공: {to_email}")
            return {"success": True, "message_id": f"email_{datetime.now().timestamp()}", "status": "sent"}

        except Exception as e:
            logger.error(f"이메일 발송 실패: {to_email} - {str(e)}")
            return {"success": False, "error": str(e), "status": "failed"}

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """비동기 이메일 발송"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor, self._send_email_sync, to_email, subject, html_content, text_content, attachments
        )
        return result

    def render_template(self, template_name: str, **kwargs) -> str:
        """템플릿 렌더링"""
        if not self.jinja_env:
            # 템플릿 엔진이 없으면 기본 HTML 반환
            return self._get_default_template(template_name, **kwargs)

        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            logger.error(f"템플릿 렌더링 실패: {template_name} - {str(e)}")
            return self._get_default_template(template_name, **kwargs)

    def _get_default_template(self, template_name: str, **kwargs) -> str:
        """기본 템플릿 (템플릿 파일이 없을 때 사용)"""
        if template_name == "order_confirmation.html":
            return f"""
            <html>
            <body>
                <h2>주문 확인</h2>
                <p>안녕하세요 {kwargs.get('user_name', '')}님,</p>
                <p>주문번호 <strong>{kwargs.get('order_number', '')}</strong>가 접수되었습니다.</p>
                <p>주문 내역:</p>
                <ul>
                    <li>요금제: {kwargs.get('plan_name', '')}</li>
                    <li>단말기: {kwargs.get('device_name', '')}</li>
                    <li>전화번호: {kwargs.get('phone_number', '')}</li>
                    <li>총 금액: {kwargs.get('total_amount', '')}원</li>
                </ul>
                <p>감사합니다.</p>
                <p>MyZone 고객센터</p>
            </body>
            </html>
            """
        elif template_name == "order_status_update.html":
            return f"""
            <html>
            <body>
                <h2>주문 상태 변경 알림</h2>
                <p>안녕하세요 {kwargs.get('user_name', '')}님,</p>
                <p>주문번호 <strong>{kwargs.get('order_number', '')}</strong>의 상태가 변경되었습니다.</p>
                <p>현재 상태: <strong>{kwargs.get('status', '')}</strong></p>
                {f"<p>메모: {kwargs.get('note', '')}</p>" if kwargs.get('note') else ""}
                <p>감사합니다.</p>
                <p>MyZone 고객센터</p>
            </body>
            </html>
            """
        elif template_name == "welcome.html":
            return f"""
            <html>
            <body>
                <h2>MyZone에 오신 것을 환영합니다!</h2>
                <p>안녕하세요 {kwargs.get('user_name', '')}님,</p>
                <p>MyZone 가입을 환영합니다!</p>
                <p>최고의 모바일 서비스를 경험하세요.</p>
                <p>감사합니다.</p>
                <p>MyZone 팀</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>MyZone 알림</h2>
                <p>안녕하세요,</p>
                <p>MyZone에서 알림을 보내드립니다.</p>
                <p>감사합니다.</p>
                <p>MyZone 고객센터</p>
            </body>
            </html>
            """

    async def send_order_confirmation_email(
        self,
        to_email: str,
        user_name: str,
        order_number: str,
        plan_name: str,
        device_name: str,
        phone_number: str,
        total_amount: str,
    ) -> Dict[str, Any]:
        """주문 확인 이메일 발송"""
        subject = f"[MyZone] 주문 확인 - {order_number}"

        html_content = self.render_template(
            "order_confirmation.html",
            user_name=user_name,
            order_number=order_number,
            plan_name=plan_name,
            device_name=device_name,
            phone_number=phone_number,
            total_amount=total_amount,
        )

        result = await self.send_email(to_email, subject, html_content)

        if result["success"]:
            logger.info(f"주문 확인 이메일 발송 완료: {to_email}")
        else:
            logger.error(f"주문 확인 이메일 발송 실패: {to_email} - {result.get('error')}")

        return result

    async def send_order_status_update_email(
        self, to_email: str, user_name: str, order_number: str, status: str, note: Optional[str] = None
    ) -> Dict[str, Any]:
        """주문 상태 변경 이메일 발송"""
        status_names = {
            "confirmed": "접수 완료",
            "processing": "개통 처리 중",
            "completed": "개통 완료",
            "cancelled": "주문 취소",
        }

        status_display = status_names.get(status, status)
        subject = f"[MyZone] 주문 상태 변경 - {order_number}"

        html_content = self.render_template(
            "order_status_update.html", user_name=user_name, order_number=order_number, status=status_display, note=note
        )

        result = await self.send_email(to_email, subject, html_content)

        if result["success"]:
            logger.info(f"주문 상태 변경 이메일 발송 완료: {to_email} - {status}")
        else:
            logger.error(f"주문 상태 변경 이메일 발송 실패: {to_email} - {result.get('error')}")

        return result

    async def send_welcome_email(self, to_email: str, user_name: str) -> Dict[str, Any]:
        """환영 이메일 발송"""
        subject = "[MyZone] 가입을 환영합니다!"

        html_content = self.render_template("welcome.html", user_name=user_name)

        result = await self.send_email(to_email, subject, html_content)

        if result["success"]:
            logger.info(f"환영 이메일 발송 완료: {to_email}")
        else:
            logger.error(f"환영 이메일 발송 실패: {to_email} - {result.get('error')}")

        return result


# 싱글톤 인스턴스
email_service = EmailService()
