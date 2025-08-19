from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import SessionLocal
from .security import verify_token
from ..models.user import User
from ..models.admin import Admin

# HTTP Bearer 토큰 스키마
security = HTTPBearer()

def get_db() -> Generator:
    """데이터베이스 세션 의존성"""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """현재 사용자 ID 반환"""
    token = credentials.credentials
    user_id = verify_token(token, "access")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return int(user_id)

def get_current_user(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> User:
    """현재 사용자 객체 반환"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )
    return user

def get_current_admin_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """현재 관리자 ID 반환"""
    token = credentials.credentials
    admin_id = verify_token(token, "access")
    
    if admin_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 관리자 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return int(admin_id)

def get_current_admin(
    db: Session = Depends(get_db),
    admin_id: int = Depends(get_current_admin_id)
) -> Admin:
    """현재 관리자 객체 반환"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="관리자를 찾을 수 없습니다."
        )
    return admin

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[int]:
    """선택적 사용자 인증 (토큰이 없어도 허용)"""
    if not credentials:
        return None
    
    token = credentials.credentials
    user_id = verify_token(token, "access")
    return int(user_id) if user_id else None