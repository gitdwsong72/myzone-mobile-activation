from datetime import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class TimestampMixin:
    """타임스탬프 필드를 제공하는 믹스인 클래스"""

    @declared_attr
    def created_at(cls):
        return Column(DateTime, default=datetime.utcnow, nullable=False)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BaseModel(Base, TimestampMixin):
    """모든 모델의 기본 클래스"""

    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
