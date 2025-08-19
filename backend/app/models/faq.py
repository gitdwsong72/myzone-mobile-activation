from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base


class FAQ(Base):
    """FAQ 모델"""
    __tablename__ = "faqs"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True, comment="카테고리")
    question = Column(Text, nullable=False, comment="질문")
    answer = Column(Text, nullable=False, comment="답변")
    is_active = Column(Boolean, default=True, comment="활성화 여부")
    view_count = Column(Integer, default=0, comment="조회수")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<FAQ(id={self.id}, category='{self.category}', question='{self.question[:50]}...')>"


class Inquiry(Base):
    """1:1 문의 모델"""
    __tablename__ = "inquiries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="문의자 이름")
    email = Column(String(255), nullable=False, comment="이메일")
    phone = Column(String(20), comment="연락처")
    order_number = Column(String(50), comment="신청번호")
    category = Column(String(50), nullable=False, comment="문의 유형")
    subject = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="문의 내용")
    status = Column(String(20), default="pending", comment="처리 상태")
    admin_reply = Column(Text, comment="관리자 답변")
    replied_at = Column(DateTime(timezone=True), comment="답변 일시")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Inquiry(id={self.id}, name='{self.name}', subject='{self.subject}')>"