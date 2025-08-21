from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import BaseModel


class AdminActivityLog(BaseModel):
    """관리자 활동 로그 모델"""

    __tablename__ = "admin_activity_logs"

    # 관리자 정보
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False, index=True, comment="관리자 ID")

    # 활동 정보
    action = Column(String(100), nullable=False, comment="수행한 작업")
    resource_type = Column(String(50), nullable=True, comment="대상 리소스 타입 (order, user, admin 등)")
    resource_id = Column(Integer, nullable=True, comment="대상 리소스 ID")

    # 요청 정보
    method = Column(String(10), nullable=True, comment="HTTP 메소드")
    endpoint = Column(String(255), nullable=True, comment="API 엔드포인트")
    ip_address = Column(String(45), nullable=True, comment="IP 주소")
    user_agent = Column(Text, nullable=True, comment="User Agent")

    # 상세 정보
    description = Column(Text, nullable=True, comment="활동 설명")
    request_data = Column(JSON, nullable=True, comment="요청 데이터")
    response_status = Column(Integer, nullable=True, comment="응답 상태 코드")

    # 결과 정보
    success = Column(String(10), default="true", nullable=False, comment="성공 여부")
    error_message = Column(Text, nullable=True, comment="오류 메시지")

    # 관계 설정
    admin = relationship("Admin", backref="activity_logs")

    def __repr__(self):
        return f"<AdminActivityLog(id={self.id}, admin_id={self.admin_id}, action='{self.action}')>"

    @classmethod
    def create_log(cls, admin_id: int, action: str, **kwargs):
        """활동 로그 생성 헬퍼 메소드"""
        return cls(
            admin_id=admin_id,
            action=action,
            resource_type=kwargs.get("resource_type"),
            resource_id=kwargs.get("resource_id"),
            method=kwargs.get("method"),
            endpoint=kwargs.get("endpoint"),
            ip_address=kwargs.get("ip_address"),
            user_agent=kwargs.get("user_agent"),
            description=kwargs.get("description"),
            request_data=kwargs.get("request_data"),
            response_status=kwargs.get("response_status"),
            success=kwargs.get("success", "true"),
            error_message=kwargs.get("error_message"),
        )
