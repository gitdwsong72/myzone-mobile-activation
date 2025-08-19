"""
사용자 모델 테스트
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from app.models.user import User


class TestUserModel:
    """사용자 모델 테스트 클래스"""
    
    def test_create_user_success(self, db_session, sample_user_data):
        """사용자 모델 생성 성공 테스트"""
        # Given
        user = User(**sample_user_data)
        
        # When
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Then
        assert user.id is not None
        assert user.name == sample_user_data["name"]
        assert user.phone == sample_user_data["phone"]
        assert user.email == sample_user_data["email"]
        assert user.created_at is not None
        assert user.updated_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_phone_unique_constraint(self, db_session, sample_user_data):
        """사용자 전화번호 유니크 제약 조건 테스트"""
        # Given
        user1 = User(**sample_user_data)
        user2_data = sample_user_data.copy()
        user2_data["name"] = "김철수"
        user2_data["email"] = "kim@example.com"
        user2 = User(**user2_data)  # 같은 전화번호
        
        # When
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_email_unique_constraint(self, db_session, sample_user_data):
        """사용자 이메일 유니크 제약 조건 테스트"""
        # Given
        user1 = User(**sample_user_data)
        user2_data = sample_user_data.copy()
        user2_data["name"] = "김철수"
        user2_data["phone"] = "010-9999-9999"
        user2 = User(**user2_data)  # 같은 이메일
        
        # When
        db_session.add(user1)
        db_session.commit()
        
        db_session.add(user2)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_required_fields(self, db_session):
        """사용자 필수 필드 테스트"""
        # Given
        user = User()  # 필수 필드 없이 생성
        
        # When
        db_session.add(user)
        
        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_string_representation(self, sample_user_data):
        """사용자 모델 문자열 표현 테스트"""
        # Given
        user = User(**sample_user_data)
        
        # When
        str_repr = str(user)
        
        # Then
        assert sample_user_data["name"] in str_repr
        assert sample_user_data["phone"] in str_repr
    
    def test_user_age_property(self, db_session, sample_user_data):
        """사용자 나이 계산 프로퍼티 테스트"""
        # Given
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        # When
        age = user.age
        
        # Then
        # 1990년생이므로 현재 연도에서 1990을 뺀 값
        current_year = datetime.now().year
        expected_age = current_year - 1990
        assert age == expected_age
    
    def test_user_full_address_property(self, db_session, sample_user_data):
        """사용자 전체 주소 프로퍼티 테스트"""
        # Given
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        # When
        full_address = user.full_address
        
        # Then
        assert full_address == sample_user_data["address"]
    
    def test_user_is_adult_property(self, db_session, sample_user_data):
        """사용자 성인 여부 프로퍼티 테스트"""
        # Given
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        # When
        is_adult = user.is_adult
        
        # Then
        assert is_adult is True  # 1990년생은 성인
    
    def test_user_phone_format_validation(self, db_session):
        """사용자 전화번호 형식 검증 테스트"""
        # Given
        invalid_user_data = {
            "name": "홍길동",
            "phone": "invalid_phone",  # 잘못된 형식
            "email": "hong@example.com",
            "birth_date": "1990-01-01",
            "gender": "M",
            "address": "서울시 강남구"
        }
        user = User(**invalid_user_data)
        
        # When & Then
        # 모델 레벨에서 검증이 실패해야 함
        with pytest.raises(ValueError):
            user.validate_phone()
    
    def test_user_email_format_validation(self, db_session):
        """사용자 이메일 형식 검증 테스트"""
        # Given
        invalid_user_data = {
            "name": "홍길동",
            "phone": "010-1234-5678",
            "email": "invalid_email",  # 잘못된 형식
            "birth_date": "1990-01-01",
            "gender": "M",
            "address": "서울시 강남구"
        }
        user = User(**invalid_user_data)
        
        # When & Then
        # 모델 레벨에서 검증이 실패해야 함
        with pytest.raises(ValueError):
            user.validate_email()
    
    def test_user_update_timestamp(self, db_session, created_user):
        """사용자 수정 시 타임스탬프 업데이트 테스트"""
        # Given
        original_updated_at = created_user.updated_at
        
        # When
        created_user.name = "수정된 이름"
        db_session.commit()
        db_session.refresh(created_user)
        
        # Then
        assert created_user.updated_at > original_updated_at
    
    def test_user_soft_delete(self, db_session, created_user):
        """사용자 소프트 삭제 테스트"""
        # Given
        user_id = created_user.id
        
        # When
        created_user.soft_delete()
        db_session.commit()
        
        # Then
        assert created_user.is_deleted is True
        assert created_user.deleted_at is not None
    
    def test_user_relationships(self, db_session, created_user, created_plan, created_device, created_number):
        """사용자 관계 테스트"""
        # Given
        from app.models.order import Order, OrderStatus
        from decimal import Decimal
        
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구"
        )
        db_session.add(order)
        db_session.commit()
        
        # When
        user_orders = created_user.orders
        
        # Then
        assert len(user_orders) == 1
        assert user_orders[0].order_number == "ORD123456789"
    
    def test_user_privacy_methods(self, db_session, created_user):
        """사용자 개인정보 처리 메서드 테스트"""
        # When
        masked_phone = created_user.get_masked_phone()
        masked_email = created_user.get_masked_email()
        
        # Then
        assert "***" in masked_phone
        assert "***" in masked_email
        assert len(masked_phone) == len(created_user.phone)
    
    def test_user_search_methods(self, db_session):
        """사용자 검색 메서드 테스트"""
        # Given
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
        search_results = User.search_by_name(db_session, "길동")
        
        # Then
        assert len(search_results) == 2
        assert all("길동" in user.name for user in search_results)