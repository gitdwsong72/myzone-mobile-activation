"""
사용자 암호화 기능 테스트
"""
import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.core.encryption import encryption_service
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user_service import UserService
from app.core.gdpr import GDPRService


class TestUserEncryption:
    """사용자 암호화 기능 테스트"""
    
    def test_encrypt_decrypt_data(self):
        """데이터 암호화/복호화 테스트"""
        original_data = "홍길동"
        
        # 암호화
        encrypted_data = encryption_service.encrypt(original_data)
        assert encrypted_data != original_data
        assert len(encrypted_data) > len(original_data)
        
        # 복호화
        decrypted_data = encryption_service.decrypt(encrypted_data)
        assert decrypted_data == original_data
    
    def test_mask_sensitive_data(self):
        """민감정보 마스킹 테스트"""
        # 이름 마스킹
        name = "홍길동"
        masked_name = encryption_service.mask_name(name)
        assert masked_name == "홍*동"
        
        # 전화번호 마스킹
        phone = "010-1234-5678"
        masked_phone = encryption_service.mask_phone_number(phone)
        assert masked_phone == "010-****-5678"
        
        # 이메일 마스킹
        email = "user@example.com"
        masked_email = encryption_service.mask_email(email)
        assert masked_email == "us***@example.com"
    
    def test_user_creation_with_encryption(self, db_session: Session):
        """암호화된 사용자 생성 테스트"""
        user_service = UserService(db_session)
        
        user_data = UserCreate(
            name="홍길동",
            phone="010-1234-5678",
            email="hong@example.com",
            birth_date="1990-01-01",
            gender="M",
            address="서울특별시 강남구 테헤란로 123"
        )
        
        # 사용자 생성
        user = user_service.create_user(user_data)
        
        # 데이터베이스에서 직접 조회 (암호화된 상태)
        db_user = db_session.query(User).filter(User.id == user.id).first()
        
        # 이름과 주소는 암호화되어 저장됨
        assert db_user.name != user_data.name  # 암호화됨
        assert db_user.address != user_data.address  # 암호화됨
        
        # 전화번호와 이메일은 암호화되지 않음 (검색을 위해)
        assert db_user.phone == user_data.phone
        assert db_user.email == user_data.email
        
        # 모델을 통해 조회하면 자동 복호화됨
        assert user.name == user_data.name
        assert user.address == user_data.address
    
    def test_user_masked_info(self, db_session: Session):
        """사용자 마스킹 정보 테스트"""
        user_service = UserService(db_session)
        
        user_data = UserCreate(
            name="홍길동",
            phone="010-1234-5678",
            email="hong@example.com",
            birth_date="1990-01-01",
            gender="M",
            address="서울특별시 강남구 테헤란로 123"
        )
        
        user = user_service.create_user(user_data)
        masked_info = user_service.get_masked_user_info(user)
        
        # 마스킹된 정보 확인
        assert masked_info["name"] == "홍*동"
        assert masked_info["phone"] == "010-****-5678"
        assert masked_info["email"] == "ho***@example.com"
        assert "****" in masked_info["address"]


class TestGDPRCompliance:
    """GDPR 준수 기능 테스트"""
    
    def test_export_user_data(self, db_session: Session):
        """사용자 데이터 내보내기 테스트"""
        user_service = UserService(db_session)
        gdpr_service = GDPRService(db_session)
        
        # 테스트 사용자 생성
        user_data = UserCreate(
            name="홍길동",
            phone="010-1234-5678",
            email="hong@example.com",
            birth_date="1990-01-01",
            gender="M",
            address="서울특별시 강남구 테헤란로 123"
        )
        
        user = user_service.create_user(user_data)
        
        # 데이터 내보내기
        exported_data = gdpr_service.export_user_data(user.id)
        
        # 내보낸 데이터 검증
        assert exported_data["personal_info"]["name"] == user_data.name
        assert exported_data["personal_info"]["phone"] == user_data.phone
        assert exported_data["personal_info"]["email"] == user_data.email
        assert "data_processing_log" in exported_data
    
    def test_anonymize_user_data(self, db_session: Session):
        """사용자 데이터 익명화 테스트"""
        user_service = UserService(db_session)
        gdpr_service = GDPRService(db_session)
        
        # 테스트 사용자 생성
        user_data = UserCreate(
            name="홍길동",
            phone="010-1234-5678",
            email="hong@example.com",
            birth_date="1990-01-01",
            gender="M",
            address="서울특별시 강남구 테헤란로 123"
        )
        
        user = user_service.create_user(user_data)
        original_id = user.id
        
        # 데이터 익명화
        success = gdpr_service.anonymize_user_data(user.id, "사용자 요청")
        assert success
        
        # 익명화된 데이터 확인
        anonymized_user = user_service.get_user_by_id(original_id)
        assert anonymized_user.name == "[익명화된 사용자]"
        assert anonymized_user.address == "[익명화됨]"
        assert not anonymized_user.is_active
        assert "anonymized.local" in anonymized_user.email
    
    def test_get_privacy_processing_info(self, db_session: Session):
        """개인정보 처리 현황 조회 테스트"""
        user_service = UserService(db_session)
        gdpr_service = GDPRService(db_session)
        
        # 테스트 사용자 생성
        user_data = UserCreate(
            name="홍길동",
            phone="010-1234-5678",
            email="hong@example.com",
            birth_date="1990-01-01",
            gender="M",
            address="서울특별시 강남구 테헤란로 123"
        )
        
        user = user_service.create_user(user_data)
        
        # 개인정보 처리 현황 조회
        processing_info = gdpr_service.get_data_processing_info(user.id)
        
        # 필수 정보 확인
        assert "data_controller" in processing_info
        assert "processing_purposes" in processing_info
        assert "legal_basis" in processing_info
        assert "data_categories" in processing_info
        assert "retention_period" in processing_info
        assert "rights" in processing_info


class TestUserAPI:
    """사용자 API 테스트"""
    
    def test_create_user_api(self, client: TestClient):
        """사용자 생성 API 테스트"""
        user_data = {
            "name": "홍길동",
            "phone": "010-1234-5678",
            "email": "hong@example.com",
            "birth_date": "1990-01-01",
            "gender": "M",
            "address": "서울특별시 강남구 테헤란로 123"
        }
        
        response = client.post("/api/v1/users/", json=user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["phone"] == user_data["phone"]
        assert data["data"]["email"] == user_data["email"]
    
    def test_get_masked_profile_api(self, client: TestClient, auth_headers: dict):
        """마스킹된 프로필 조회 API 테스트"""
        response = client.get("/api/v1/users/me/masked", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 마스킹된 데이터 확인
        user_data = data["data"]
        assert "*" in user_data["name"]
        assert "****" in user_data["phone"]
    
    def test_export_data_api(self, client: TestClient, auth_headers: dict):
        """데이터 내보내기 API 테스트"""
        response = client.get("/api/v1/users/me/data-export", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "personal_info" in data["data"]
        assert "data_processing_log" in data["data"]
    
    def test_privacy_info_api(self, client: TestClient, auth_headers: dict):
        """개인정보 처리 현황 API 테스트"""
        response = client.get("/api/v1/users/me/privacy-info", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data_controller" in data["data"]
        assert "processing_purposes" in data["data"]