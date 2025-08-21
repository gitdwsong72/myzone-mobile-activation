"""
인증 API 테스트
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token


class TestAuthAPI:
    """인증 API 테스트 클래스"""

    def test_login_success(self, client, created_admin):
        """로그인 성공 테스트"""
        # Given
        login_data = {"username": created_admin.username, "password": "admin123!"}

        # When
        response = client.post("/api/v1/auth/login", data=login_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == created_admin.username

    def test_login_invalid_credentials(self, client, created_admin):
        """잘못된 인증 정보로 로그인 테스트"""
        # Given
        login_data = {"username": created_admin.username, "password": "wrong_password"}

        # When
        response = client.post("/api/v1/auth/login", data=login_data)

        # Then
        assert response.status_code == 401
        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_login_user_not_found(self, client):
        """존재하지 않는 사용자 로그인 테스트"""
        # Given
        login_data = {"username": "nonexistent", "password": "password123"}

        # When
        response = client.post("/api/v1/auth/login", data=login_data)

        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_CREDENTIALS"

    def test_refresh_token_success(self, client, created_admin):
        """토큰 갱신 성공 테스트"""
        # Given
        # 먼저 로그인하여 refresh_token 획득
        login_data = {"username": created_admin.username, "password": "admin123!"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        refresh_token = login_response.json()["refresh_token"]

        # When
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client):
        """잘못된 refresh token으로 갱신 테스트"""
        # Given
        invalid_refresh_token = "invalid_token"

        # When
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": invalid_refresh_token})

        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_TOKEN"

    def test_logout_success(self, client, created_admin):
        """로그아웃 성공 테스트"""
        # Given
        # 먼저 로그인하여 access_token 획득
        login_data = {"username": created_admin.username, "password": "admin123!"}
        login_response = client.post("/api/v1/auth/login", data=login_data)
        access_token = login_response.json()["access_token"]

        # When
        response = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"

    def test_logout_without_token(self, client):
        """토큰 없이 로그아웃 테스트"""
        # When
        response = client.post("/api/v1/auth/logout")

        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"

    def test_get_current_user_success(self, client, created_admin):
        """현재 사용자 정보 조회 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})

        # When
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == created_admin.username
        assert data["email"] == created_admin.email
        assert data["role"] == created_admin.role

    def test_get_current_user_invalid_token(self, client):
        """잘못된 토큰으로 사용자 정보 조회 테스트"""
        # Given
        invalid_token = "invalid_token"

        # When
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {invalid_token}"})

        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "INVALID_TOKEN"

    def test_get_current_user_expired_token(self, client):
        """만료된 토큰으로 사용자 정보 조회 테스트"""
        # Given
        # 만료된 토큰 생성 (과거 시간으로 설정)
        from datetime import datetime, timedelta

        expired_token = create_access_token(data={"sub": "testuser"}, expires_delta=timedelta(minutes=-1))  # 1분 전에 만료

        # When
        response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

        # Then
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "TOKEN_EXPIRED"

    @patch("app.services.verification_service.VerificationService.send_sms")
    def test_send_verification_code_success(self, mock_send_sms, client):
        """본인인증 코드 발송 성공 테스트"""
        # Given
        mock_send_sms.return_value = True
        phone_data = {"phone": "010-1234-5678"}

        # When
        response = client.post("/api/v1/auth/send-verification", json=phone_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Verification code sent successfully"
        mock_send_sms.assert_called_once()

    @patch("app.services.verification_service.VerificationService.verify_code")
    def test_verify_phone_success(self, mock_verify_code, client):
        """전화번호 인증 성공 테스트"""
        # Given
        mock_verify_code.return_value = True
        verification_data = {"phone": "010-1234-5678", "code": "123456"}

        # When
        response = client.post("/api/v1/auth/verify-phone", json=verification_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
        mock_verify_code.assert_called_once_with("010-1234-5678", "123456")

    @patch("app.services.verification_service.VerificationService.verify_code")
    def test_verify_phone_invalid_code(self, mock_verify_code, client):
        """잘못된 인증 코드로 전화번호 인증 테스트"""
        # Given
        mock_verify_code.return_value = False
        verification_data = {"phone": "010-1234-5678", "code": "wrong_code"}

        # When
        response = client.post("/api/v1/auth/verify-phone", json=verification_data)

        # Then
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_VERIFICATION_CODE"

    def test_change_password_success(self, client, created_admin):
        """비밀번호 변경 성공 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        password_data = {
            "current_password": "admin123!",
            "new_password": "newpassword123!",
            "confirm_password": "newpassword123!",
        }

        # When
        response = client.post(
            "/api/v1/auth/change-password", json=password_data, headers={"Authorization": f"Bearer {access_token}"}
        )

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password changed successfully"

    def test_change_password_wrong_current(self, client, created_admin):
        """잘못된 현재 비밀번호로 변경 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        password_data = {
            "current_password": "wrong_password",
            "new_password": "newpassword123!",
            "confirm_password": "newpassword123!",
        }

        # When
        response = client.post(
            "/api/v1/auth/change-password", json=password_data, headers={"Authorization": f"Bearer {access_token}"}
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "INVALID_CURRENT_PASSWORD"

    def test_change_password_mismatch(self, client, created_admin):
        """새 비밀번호 확인 불일치 테스트"""
        # Given
        access_token = create_access_token(data={"sub": created_admin.username})
        password_data = {
            "current_password": "admin123!",
            "new_password": "newpassword123!",
            "confirm_password": "different_password",
        }

        # When
        response = client.post(
            "/api/v1/auth/change-password", json=password_data, headers={"Authorization": f"Bearer {access_token}"}
        )

        # Then
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "PASSWORD_MISMATCH"
