import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import redis
from enum import Enum

from app.core.config import settings
from app.services.email_service import email_service

logger = logging.getLogger(__name__)

# 이메일 큐 상태
class EmailStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"

# 이메일 큐 모델 (간단한 구현을 위해 별도 테이블 사용)
Base = declarative_base()

class EmailQueue(Base):
    __tablename__ = "email_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    to_email = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text, nullable=False)
    text_content = Column(Text, nullable=True)
    template_name = Column(String(100), nullable=True)
    template_data = Column(Text, nullable=True)  # JSON 형태
    status = Column(String(20), default=EmailStatus.PENDING)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    error_message = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class EmailQueueService:
    def __init__(self):
        self.redis_client = None
        self.db_session = None
        self.is_processing = False
        
        # Redis 연결 시도
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_client.ping()
            logger.info("Redis 연결 성공")
        except Exception as e:
            logger.warning(f"Redis 연결 실패, 데이터베이스 큐 사용: {e}")
    
    def _get_db_session(self):
        """데이터베이스 세션 생성"""
        if not self.db_session:
            engine = create_engine(settings.DATABASE_URL)
            Base.metadata.create_all(bind=engine)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            self.db_session = SessionLocal()
        return self.db_session
    
    async def add_to_queue(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        template_name: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        scheduled_at: Optional[datetime] = None,
        priority: int = 0
    ) -> bool:
        """이메일을 큐에 추가"""
        try:
            email_data = {
                "to_email": to_email,
                "subject": subject,
                "html_content": html_content,
                "text_content": text_content,
                "template_name": template_name,
                "template_data": template_data,
                "scheduled_at": scheduled_at.isoformat() if scheduled_at else datetime.utcnow().isoformat(),
                "priority": priority,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if self.redis_client:
                # Redis 큐 사용
                queue_key = f"email_queue:priority_{priority}"
                await self._add_to_redis_queue(queue_key, email_data)
            else:
                # 데이터베이스 큐 사용
                await self._add_to_db_queue(email_data)
            
            logger.info(f"이메일 큐 추가 완료: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"이메일 큐 추가 실패: {to_email} - {str(e)}")
            return False
    
    async def _add_to_redis_queue(self, queue_key: str, email_data: Dict[str, Any]):
        """Redis 큐에 이메일 추가"""
        email_json = json.dumps(email_data, ensure_ascii=False)
        self.redis_client.lpush(queue_key, email_json)
    
    async def _add_to_db_queue(self, email_data: Dict[str, Any]):
        """데이터베이스 큐에 이메일 추가"""
        db = self._get_db_session()
        
        email_queue = EmailQueue(
            to_email=email_data["to_email"],
            subject=email_data["subject"],
            html_content=email_data["html_content"],
            text_content=email_data.get("text_content"),
            template_name=email_data.get("template_name"),
            template_data=json.dumps(email_data.get("template_data")) if email_data.get("template_data") else None,
            scheduled_at=datetime.fromisoformat(email_data["scheduled_at"])
        )
        
        db.add(email_queue)
        db.commit()
    
    async def process_queue(self):
        """큐 처리 시작"""
        if self.is_processing:
            logger.info("이미 큐 처리가 진행 중입니다.")
            return
        
        self.is_processing = True
        logger.info("이메일 큐 처리 시작")
        
        try:
            while self.is_processing:
                if self.redis_client:
                    await self._process_redis_queue()
                else:
                    await self._process_db_queue()
                
                # 1초 대기
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"큐 처리 중 오류: {str(e)}")
        finally:
            self.is_processing = False
            logger.info("이메일 큐 처리 종료")
    
    async def _process_redis_queue(self):
        """Redis 큐 처리"""
        # 우선순위별로 큐 확인 (높은 우선순위부터)
        for priority in [2, 1, 0]:
            queue_key = f"email_queue:priority_{priority}"
            
            # 큐에서 이메일 가져오기
            email_json = self.redis_client.rpop(queue_key)
            if email_json:
                try:
                    email_data = json.loads(email_json)
                    await self._send_queued_email(email_data)
                    break  # 하나 처리 후 다음 루프로
                except Exception as e:
                    logger.error(f"Redis 큐 이메일 처리 실패: {str(e)}")
                    # 실패한 이메일을 재시도 큐로 이동
                    retry_queue_key = f"email_queue:retry"
                    self.redis_client.lpush(retry_queue_key, email_json)
    
    async def _process_db_queue(self):
        """데이터베이스 큐 처리"""
        db = self._get_db_session()
        
        # 처리 대기 중인 이메일 조회 (예약 시간이 지난 것만)
        pending_emails = db.query(EmailQueue).filter(
            EmailQueue.status == EmailStatus.PENDING,
            EmailQueue.scheduled_at <= datetime.utcnow()
        ).limit(10).all()
        
        for email_queue in pending_emails:
            try:
                # 상태를 처리 중으로 변경
                email_queue.status = EmailStatus.PROCESSING
                db.commit()
                
                # 이메일 발송
                email_data = {
                    "to_email": email_queue.to_email,
                    "subject": email_queue.subject,
                    "html_content": email_queue.html_content,
                    "text_content": email_queue.text_content,
                    "template_name": email_queue.template_name,
                    "template_data": json.loads(email_queue.template_data) if email_queue.template_data else None
                }
                
                result = await self._send_queued_email(email_data)
                
                if result:
                    email_queue.status = EmailStatus.SENT
                    email_queue.sent_at = datetime.utcnow()
                else:
                    # 재시도 처리
                    email_queue.retry_count += 1
                    if email_queue.retry_count >= email_queue.max_retries:
                        email_queue.status = EmailStatus.FAILED
                    else:
                        email_queue.status = EmailStatus.RETRY
                        email_queue.scheduled_at = datetime.utcnow() + timedelta(minutes=5 * email_queue.retry_count)
                
                db.commit()
                
            except Exception as e:
                logger.error(f"DB 큐 이메일 처리 실패: {str(e)}")
                email_queue.status = EmailStatus.FAILED
                email_queue.error_message = str(e)
                db.commit()
    
    async def _send_queued_email(self, email_data: Dict[str, Any]) -> bool:
        """큐에서 가져온 이메일 발송"""
        try:
            result = await email_service.send_email(
                to_email=email_data["to_email"],
                subject=email_data["subject"],
                html_content=email_data["html_content"],
                text_content=email_data.get("text_content")
            )
            
            return result["success"]
            
        except Exception as e:
            logger.error(f"큐 이메일 발송 실패: {str(e)}")
            return False
    
    def stop_processing(self):
        """큐 처리 중지"""
        self.is_processing = False
        logger.info("이메일 큐 처리 중지 요청")
    
    async def add_order_confirmation_to_queue(
        self,
        to_email: str,
        user_name: str,
        order_number: str,
        plan_name: str,
        device_name: str,
        phone_number: str,
        total_amount: str,
        priority: int = 1
    ) -> bool:
        """주문 확인 이메일을 큐에 추가"""
        subject = f"[MyZone] 주문 확인 - {order_number}"
        
        html_content = email_service.render_template(
            "order_confirmation.html",
            user_name=user_name,
            order_number=order_number,
            plan_name=plan_name,
            device_name=device_name,
            phone_number=phone_number,
            total_amount=total_amount
        )
        
        return await self.add_to_queue(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            template_name="order_confirmation.html",
            template_data={
                "user_name": user_name,
                "order_number": order_number,
                "plan_name": plan_name,
                "device_name": device_name,
                "phone_number": phone_number,
                "total_amount": total_amount
            },
            priority=priority
        )
    
    async def add_order_status_update_to_queue(
        self,
        to_email: str,
        user_name: str,
        order_number: str,
        status: str,
        note: Optional[str] = None,
        priority: int = 1
    ) -> bool:
        """주문 상태 변경 이메일을 큐에 추가"""
        status_names = {
            "confirmed": "접수 완료",
            "processing": "개통 처리 중",
            "completed": "개통 완료",
            "cancelled": "주문 취소"
        }
        
        status_display = status_names.get(status, status)
        subject = f"[MyZone] 주문 상태 변경 - {order_number}"
        
        html_content = email_service.render_template(
            "order_status_update.html",
            user_name=user_name,
            order_number=order_number,
            status=status_display,
            note=note
        )
        
        return await self.add_to_queue(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            template_name="order_status_update.html",
            template_data={
                "user_name": user_name,
                "order_number": order_number,
                "status": status_display,
                "note": note
            },
            priority=priority
        )

# 싱글톤 인스턴스
email_queue_service = EmailQueueService()