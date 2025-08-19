"""
사용자 서비스 테스트
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.exceptions import UserNotFoundError, DuplicateUserError


class TestUserService:
    """사용자 서비스 테스트 클래스"""
    
    def test_create_user_success(self, db_session, sample_user_data):
        """사용자 생성 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        user_data = UserCreate(**sample_user_data)
        
        # When
        result = user_service.create_user(user_data)
        
        # Then
        assert result.name == sample_user_data["name"]
        assert result.phone == sample_user_data["phone"]
        assert result.email == sample_user_data["email"]
        assert result.id is not None
        assert result.created_at is not None
    
    def test_create_user_duplicate_phone(self, db_session, sample_user_data, created_user):
        """중복 전화번호로 사용자 생성 실패 테스트"""
        # Given
        user_service = UserService(db_session)
        user_data = UserCreate(**sample_user_data)
        
        # When & Then
        with pytest.raises(DuplicateUserError):
            user_service.create_user(user_data)
    
    def test_get_user_by_id_success(self, db_session, created_user):
        """ID로 사용자 조회 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        
        # When
        result = user_service.get_user_by_id(created_user.id)
        
        # Then
        assert result.id == created_user.id
        assert result.name == created_user.name
        assert result.phone == created_user.phone
    
    def test_get_user_by_id_not_found(self, db_session):
        """존재하지 않는 사용자 조회 테스트"""
        # Given
        user_service = UserService(db_session)
        non_existent_id = 999
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            user_service.get_user_by_id(non_existent_id)
    
    def test_get_user_by_phone_success(self, db_session, created_user):
        """전화번호로 사용자 조회 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        
        # When
        result = user_service.get_user_by_phone(created_user.phone)
        
        # Then
        assert result.id == created_user.id
        assert result.phone == created_user.phone
    
    def test_get_user_by_phone_not_found(self, db_session):
        """존재하지 않는 전화번호로 사용자 조회 테스트"""
        # Given
        user_service = UserService(db_session)
        non_existent_phone = "010-9999-9999"
        
        # When
        result = user_service.get_user_by_phone(non_existent_phone)
        
        # Then
        assert result is None
    
    def test_update_user_success(self, db_session, created_user):
        """사용자 정보 수정 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        update_data = UserUpdate(
            name="김철수",
            email="kim@example.com",
            address="부산시 해운대구 센텀로 456"
        )
        
        # When
        result = user_service.update_user(created_user.id, update_data)
        
        # Then
        assert result.name == "김철수"
        assert result.email == "kim@example.com"
        assert result.address == "부산시 해운대구 센텀로 456"
        assert result.phone == created_user.phone  # 변경되지 않은 필드
    
    def test_update_user_not_found(self, db_session):
        """존재하지 않는 사용자 수정 테스트"""
        # Given
        user_service = UserService(db_session)
        non_existent_id = 999
        update_data = UserUpdate(name="김철수")
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            user_service.update_user(non_existent_id, update_data)
    
    def test_delete_user_success(self, db_session, created_user):
        """사용자 삭제 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        user_id = created_user.id
        
        # When
        result = user_service.delete_user(user_id)
        
        # Then
        assert result is True
        with pytest.raises(UserNotFoundError):
            user_service.get_user_by_id(user_id)
    
    def test_delete_user_not_found(self, db_session):
        """존재하지 않는 사용자 삭제 테스트"""
        # Given
        user_service = UserService(db_session)
        non_existent_id = 999
        
        # When & Then
        with pytest.raises(UserNotFoundError):
            user_service.delete_user(non_existent_id)
    
    @patch('app.services.verification_service.VerificationService.send_sms')
    def test_send_verification_code_success(self, mock_send_sms, db_session, created_user):
        """본인인증 코드 발송 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        mock_send_sms.return_value = True
        
        # When
        result = user_service.send_verification_code(created_user.phone)
        
        # Then
        assert result is True
        mock_send_sms.assert_called_once()
    
    @patch('app.services.verification_service.VerificationService.verify_code')
    def test_verify_phone_success(self, mock_verify_code, db_session, created_user):
        """전화번호 인증 성공 테스트"""
        # Given
        user_service = UserService(db_session)
        mock_verify_code.return_value = True
        verification_code = "123456"
        
        # When
        result = user_service.verify_phone(created_user.phone, verification_code)
        
        # Then
        assert result is True
        mock_verify_code.assert_called_once_with(created_user.phone, verification_code)
    
    def test_list_users_with_pagination(self, db_session):
        """사용자 목록 조회 (페이지네이션) 테스트"""
        # Given
        user_service = UserService(db_session)
        
        # 테스트 사용자 3명 생성
        for i in range(3):
            user_data = {
                "name": f"사용자{i+1}",
                "phone": f"010-1234-567{i}",
                "email": f"user{i+1}@example.com",
                "birth_date": "1990-01-01",
                "gender": "M",
                "address": "서울시 강남구"
            }
            user = User(**user_data)
            db_session.add(user)
        db_session.commit()
        
        # When
        result = user_service.list_users(skip=0, limit=2)
        
        # Then
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)
    
    def test_search_users_by_name(self, db_session):
        """이름으로 사용자 검색 테스트"""
        # Given
        user_service = UserService(db_session)
        
        # 테스트 사용자 생성
        users_data = [
            {"name": "홍길동", "phone": "010-1111-1111", "email": "hong@example.com"},
            {"name": "김길동", "phone": "010-2222-2222", "email": "kim@example.com"},
            {"name": "이철수", "phone": "010-3333-3333", "email": "lee@example.com"}
        ]
        
        for user_data in users_data:
            user_data.update({
                "birth_date": "1990-01-01",
                "gender": "M",
                "address": "서울시 강남구"
            })
            user = User(**user_data)
            db_session.add(user)
        db_session.commit()
        
        # When
        result = user_service.search_users_by_name("길동")
        
        # Then
        assert len(result) == 2
        assert all("길동" in user.name for user in result)