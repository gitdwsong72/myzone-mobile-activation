import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..core.security import create_token_pair, get_password_hash, verify_password, verify_token
from ..models.admin import Admin
from ..models.user import User
from ..schemas.auth import (
    AdminLogin,
    ChangePasswordRequest,
    RefreshTokenRequest,
    SMSVerificationConfirm,
    SMSVerificationRequest,
    UserLogin,
)
from ..services.verification_service import verification_service


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """사용자 인증"""
        user = self.db.query(User).filter(User.phone == login_data.phone).first()
        if not user:
            return None

        if not verify_password(login_data.password, user.password_hash):
            return None

        return user

    def authenticate_admin(self, login_data: AdminLogin) -> Optional[Admin]:
        """관리자 인증"""
        admin = self.db.query(Admin).filter(Admin.username == login_data.username).first()
        if not admin:
            return None

        if not verify_password(login_data.password, admin.password_hash):
            return None

        # 마지막 로그인 시간 업데이트
        admin.last_login = datetime.utcnow()
        self.db.commit()

        return admin

    def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """사용자 로그인"""
        user = self.authenticate_user(login_data)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="전화번호 또는 비밀번호가 올바르지 않습니다.")

        tokens = create_token_pair(subject=user.id)
        return {"user": {"id": user.id, "name": user.name, "phone": user.phone, "email": user.email}, **tokens}

    def login_admin(self, login_data: AdminLogin) -> Dict[str, Any]:
        """관리자 로그인"""
        admin = self.authenticate_admin(login_data)
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="사용자명 또는 비밀번호가 올바르지 않습니다.")

        tokens = create_token_pair(subject=admin.id)
        return {"admin": {"id": admin.id, "username": admin.username, "email": admin.email, "role": admin.role}, **tokens}

    def refresh_token(self, refresh_request: RefreshTokenRequest) -> Dict[str, Any]:
        """토큰 갱신"""
        user_id = verify_token(refresh_request.refresh_token, "refresh")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 리프레시 토큰입니다.")

        # 사용자 존재 확인
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            # 관리자 확인
            admin = self.db.query(Admin).filter(Admin.id == int(user_id)).first()
            if not admin:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        tokens = create_token_pair(subject=user_id)
        return tokens

    def change_password(self, user_id: int, change_request: ChangePasswordRequest) -> bool:
        """비밀번호 변경"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        if not verify_password(change_request.current_password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="현재 비밀번호가 올바르지 않습니다.")

        user.password_hash = get_password_hash(change_request.new_password)
        self.db.commit()
        return True

    def generate_verification_code(self) -> str:
        """인증 코드 생성"""
        return "".join(random.choices(string.digits, k=6))

    async def send_sms_verification(self, request: SMSVerificationRequest) -> Dict[str, Any]:
        """SMS 인증 코드 발송"""
        result = await verification_service.send_verification_code(db=self.db, phone=request.phone, purpose="auth")
        return result

    def verify_sms_code(self, request: SMSVerificationConfirm) -> Dict[str, Any]:
        """SMS 인증 코드 확인"""
        result = verification_service.verify_code(
            db=self.db, phone=request.phone, code=request.verification_code, purpose="auth"
        )
        return result

    def logout_user(self, user_id: int) -> bool:
        """사용자 로그아웃 (토큰 무효화)"""
        # JWT는 stateless이므로 실제 무효화는 클라이언트에서 토큰 삭제
        # 필요시 Redis에 블랙리스트 토큰 저장
        return True
