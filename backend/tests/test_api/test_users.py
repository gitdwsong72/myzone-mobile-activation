"""
사용자 API 테스트
"""
import pytest
from unittest.mock import patch

from app.core.security import create_access_token


class TestUsersAPI:
    """사용자 API 테스트 클래스"""
    
    def test_create_user_success(self, client, sample_user_data):
        """사용자 생성 성공 테스트"""
        # When
        response = client.post("/api/v1/users/", json=sample_user_data)
        
        # Then
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert data["phone"] == sample_user_data["phone"]
        assert data["email"] == sample_user_data["email"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_user_invalid_data(self, client):
        """잘못된 데이터로 사용자 생성 테스트"""
        # Given
        invalid_user_data = {
            "name": "",  # 빈 이름
            "phone": "invalid_phone",  # 잘못된 전화번호 형식
            "email": "invalid_email"  # 잘못된 이메일 형식
        }
        
        # When
        response = client.post("/api/v1/users/", json=invalid_user_data)
        
        # Then
        assert response.status_code == 422
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_create_user_duplicate_phone(self, client, created_user, sample_user_data):
        """중복 전화번호로 사용자 생성 테스트"""
        # Given
        duplicate_user_data = sample_user_data.copy()
        duplicate_user_data["phone"] = created_user.phone
        
        # When
        response = client.post("/api/v1/users/", json=duplicate_user_data)
        
        # Then
        assert response.status_code == 409
        data = response.json()
        assert data["error_code"] == "DUPLICATE_USER"
    
    def test_get_user_success(self, client, created_user, created_admin):
        """사용자 조회 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # When
        response = client.get(
            f"/api/v1/users/{created_user.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user.id
        assert data["name"] == created_user.name
        assert data["phone"] == created_user.phone
    
    def test_get_user_not_found(self, client, created_admin):
        """존재하지 않는 사용자 조회 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        non_existent_id = 999
        
        # When
        response = client.get(
            f"/api/v1/users/{non_existent_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_get_user_unauthorized(self, client, created_user):
        """인증 없이 사용자 조회 테스트"""
        # When
        response = client.get(f"/api/v1/users/{created_user.id}")
        
        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"
    
    def test_update_user_success(self, client, created_user, created_admin):
        """사용자 정보 수정 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        update_data = {
            "name": "김철수",
            "email": "kim@example.com",
            "address": "부산시 해운대구"
        }
        
        # When
        response = client.put(
            f"/api/v1/users/{created_user.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "김철수"
        assert data["email"] == "kim@example.com"
        assert data["address"] == "부산시 해운대구"
    
    def test_update_user_not_found(self, client, created_admin):
        """존재하지 않는 사용자 수정 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        non_existent_id = 999
        update_data = {"name": "김철수"}
        
        # When
        response = client.put(
            f"/api/v1/users/{non_existent_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_delete_user_success(self, client, created_user, created_admin):
        """사용자 삭제 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # When
        response = client.delete(
            f"/api/v1/users/{created_user.id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "User deleted successfully"
    
    def test_delete_user_not_found(self, client, created_admin):
        """존재하지 않는 사용자 삭제 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        non_existent_id = 999
        
        # When
        response = client.delete(
            f"/api/v1/users/{non_existent_id}",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "USER_NOT_FOUND"
    
    def test_list_users_success(self, client, created_admin):
        """사용자 목록 조회 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # When
        response = client.get(
            "/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_users_with_pagination(self, client, created_admin, db_session):
        """페이지네이션을 사용한 사용자 목록 조회 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # 테스트 사용자 5명 생성
        from app.models.user import User
        for i in range(5):
            user = User(
                name=f"사용자{i+1}",
                phone=f"010-1234-567{i}",
                email=f"user{i+1}@example.com",
                birth_date="1990-01-01",
                gender="M",
                address="서울시 강남구"
            )
            db_session.add(user)
        db_session.commit()
        
        # When
        response = client.get(
            "/api/v1/users/?skip=0&limit=3",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_search_users_by_name(self, client, created_admin, db_session):
        """이름으로 사용자 검색 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # 테스트 사용자 생성
        from app.models.user import User
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
        response = client.get(
            "/api/v1/users/search?name=길동",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("길동" in user["name"] for user in data)
    
    @patch('app.services.verification_service.VerificationService.send_sms')
    def test_send_verification_code_success(self, mock_send_sms, client, created_user):
        """본인인증 코드 발송 성공 테스트"""
        # Given
        mock_send_sms.return_value = True
        
        # When
        response = client.post(f"/api/v1/users/{created_user.id}/send-verification")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Verification code sent successfully"
        mock_send_sms.assert_called_once()
    
    @patch('app.services.verification_service.VerificationService.verify_code')
    def test_verify_user_phone_success(self, mock_verify_code, client, created_user):
        """사용자 전화번호 인증 성공 테스트"""
        # Given
        mock_verify_code.return_value = True
        verification_data = {"code": "123456"}
        
        # When
        response = client.post(
            f"/api/v1/users/{created_user.id}/verify-phone",
            json=verification_data
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
    
    def test_get_user_orders(self, client, created_user, created_admin):
        """사용자의 주문 목록 조회 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        
        # When
        response = client.get(
            f"/api/v1/users/{created_user.id}/orders",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)