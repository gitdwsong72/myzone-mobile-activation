from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ...core.deps import get_db, get_current_user, get_current_admin
from ...services.auth_service import AuthService
from ...schemas.auth import (
    UserLogin,
    AdminLogin,
    RefreshTokenRequest,
    ChangePasswordRequest,
    SMSVerificationRequest,
    SMSVerificationConfirm,
    Token,
    AuthResponse
)
from ...models.user import User
from ...models.admin import Admin

router = APIRouter()

@router.post("/login/user", response_model=Dict[str, Any])
async def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """사용자 로그인"""
    auth_service = AuthService(db)
    try:
        result = auth_service.login_user(login_data)
        return {
            "success": True,
            "message": "로그인이 완료되었습니다.",
            "data": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/login/admin", response_model=Dict[str, Any])
async def login_admin(
    login_data: AdminLogin,
    db: Session = Depends(get_db)
):
    """관리자 로그인"""
    auth_service = AuthService(db)
    try:
        result = auth_service.login_admin(login_data)
        return {
            "success": True,
            "message": "관리자 로그인이 완료되었습니다.",
            "data": result
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 로그인 처리 중 오류가 발생했습니다."
        )

@router.post("/logout", response_model=AuthResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 로그아웃"""
    auth_service = AuthService(db)
    try:
        auth_service.logout_user(current_user.id)
        return AuthResponse(
            success=True,
            message="로그아웃이 완료되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그아웃 처리 중 오류가 발생했습니다."
        )

@router.post("/logout/admin", response_model=AuthResponse)
async def logout_admin(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """관리자 로그아웃"""
    auth_service = AuthService(db)
    try:
        auth_service.logout_user(current_admin.id)
        return AuthResponse(
            success=True,
            message="관리자 로그아웃이 완료되었습니다."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="관리자 로그아웃 처리 중 오류가 발생했습니다."
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """토큰 갱신"""
    auth_service = AuthService(db)
    try:
        result = auth_service.refresh_token(refresh_request)
        return Token(**result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다."
        )

@router.post("/change-password", response_model=AuthResponse)
async def change_password(
    change_request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """비밀번호 변경"""
    auth_service = AuthService(db)
    try:
        auth_service.change_password(current_user.id, change_request)
        return AuthResponse(
            success=True,
            message="비밀번호가 성공적으로 변경되었습니다."
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다."
        )

@router.post("/verify/sms/send", response_model=AuthResponse)
async def send_sms_verification(
    request: SMSVerificationRequest,
    db: Session = Depends(get_db)
):
    """SMS 인증 코드 발송"""
    auth_service = AuthService(db)
    try:
        result = await auth_service.send_sms_verification(request)
        return AuthResponse(
            success=result["success"],
            message=result["message"],
            data={"expires_in": result.get("expires_in")}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SMS 발송 중 오류가 발생했습니다."
        )

@router.post("/verify/sms/confirm", response_model=AuthResponse)
async def confirm_sms_verification(
    request: SMSVerificationConfirm,
    db: Session = Depends(get_db)
):
    """SMS 인증 코드 확인"""
    auth_service = AuthService(db)
    try:
        result = auth_service.verify_sms_code(request)
        if result["success"]:
            return AuthResponse(
                success=True,
                message=result["message"]
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["message"]
            )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="인증 확인 중 오류가 발생했습니다."
        )

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """현재 사용자 정보 조회"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "name": current_user.name,
            "phone": current_user.phone,
            "email": current_user.email,
            "created_at": current_user.created_at
        }
    }

@router.get("/me/admin", response_model=Dict[str, Any])
async def get_current_admin_info(
    current_admin: Admin = Depends(get_current_admin)
):
    """현재 관리자 정보 조회"""
    return {
        "success": True,
        "data": {
            "id": current_admin.id,
            "username": current_admin.username,
            "email": current_admin.email,
            "role": current_admin.role,
            "last_login": current_admin.last_login,
            "created_at": current_admin.created_at
        }
    }