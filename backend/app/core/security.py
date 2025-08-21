from datetime import datetime, timedelta
from typing import Any, Optional, Union

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """액세스 토큰 생성"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """리프레시 토큰 생성"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """토큰 검증 및 subject 반환"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_sub: str = payload.get("sub")
        token_exp: int = payload.get("exp")
        token_type_claim: str = payload.get("type")

        if token_sub is None:
            return None

        if token_type_claim != token_type:
            return None

        # 토큰 만료 확인
        if datetime.utcnow() > datetime.fromtimestamp(token_exp):
            return None

        return token_sub
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return pwd_context.hash(password)


def create_token_pair(subject: Union[str, Any]) -> dict:
    """액세스 토큰과 리프레시 토큰 쌍 생성"""
    access_token = create_access_token(subject=subject)
    refresh_token = create_refresh_token(subject=subject)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
