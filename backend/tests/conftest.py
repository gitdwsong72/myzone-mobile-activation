"""
테스트 설정 및 픽스처 정의
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.core.config import settings
from app.models.user import User
from app.models.plan import Plan
from app.models.device import Device
from app.models.number import Number
from app.models.order import Order
from app.models.payment import Payment
from app.models.admin import Admin

# 테스트용 인메모리 SQLite 데이터베이스
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """테스트용 데이터베이스 세션"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """테스트 클라이언트"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """샘플 사용자 데이터"""
    return {
        "name": "홍길동",
        "phone": "010-1234-5678",
        "email": "hong@example.com",
        "birth_date": "1990-01-01",
        "gender": "M",
        "address": "서울시 강남구 테헤란로 123"
    }


@pytest.fixture
def sample_plan_data():
    """샘플 요금제 데이터"""
    return {
        "name": "5G 프리미엄",
        "description": "무제한 데이터 요금제",
        "monthly_fee": 55000,
        "data_limit": -1,  # 무제한
        "call_minutes": -1,  # 무제한
        "sms_count": -1,  # 무제한
        "category": "5G",
        "is_active": True
    }


@pytest.fixture
def sample_device_data():
    """샘플 단말기 데이터"""
    return {
        "brand": "Samsung",
        "model": "Galaxy S24",
        "color": "Black",
        "price": 1200000,
        "stock_quantity": 10,
        "specifications": "6.2인치, 256GB, 12GB RAM",
        "image_url": "/images/galaxy-s24-black.jpg",
        "is_active": True
    }


@pytest.fixture
def sample_number_data():
    """샘플 번호 데이터"""
    return {
        "number": "010-1111-2222",
        "category": "일반",
        "additional_fee": 0,
        "status": "available"
    }


@pytest.fixture
def sample_admin_data():
    """샘플 관리자 데이터"""
    return {
        "username": "admin",
        "email": "admin@myzone.com",
        "password": "admin123!",
        "role": "admin"
    }


@pytest.fixture
def created_user(db_session, sample_user_data):
    """생성된 사용자 픽스처"""
    user = User(**sample_user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def created_plan(db_session, sample_plan_data):
    """생성된 요금제 픽스처"""
    plan = Plan(**sample_plan_data)
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


@pytest.fixture
def created_device(db_session, sample_device_data):
    """생성된 단말기 픽스처"""
    device = Device(**sample_device_data)
    db_session.add(device)
    db_session.commit()
    db_session.refresh(device)
    return device


@pytest.fixture
def created_number(db_session, sample_number_data):
    """생성된 번호 픽스처"""
    number = Number(**sample_number_data)
    db_session.add(number)
    db_session.commit()
    db_session.refresh(number)
    return number


@pytest.fixture
def created_admin(db_session, sample_admin_data):
    """생성된 관리자 픽스처"""
    from app.core.security import get_password_hash
    admin_data = sample_admin_data.copy()
    admin_data["password_hash"] = get_password_hash(admin_data.pop("password"))
    admin = Admin(**admin_data)
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin