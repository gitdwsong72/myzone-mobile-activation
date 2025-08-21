from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from ...core.deps import get_db, get_current_user
from ...core.permissions import (
    require_user_permissions,
    check_resource_ownership,
    Permission
)
from ...models.user import User
from ...models.order import Order
from ...schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserMaskedResponse,
    AddressSearchRequest, AddressSearchResponse,
    UserVerificationRequest, UserVerificationResponse,
    UserVerificationConfirmRequest, UserDeletionRequest
)
from ...services.user_service import get_user_service, UserService
from ...core.gdpr import get_gdpr_service, GDPRService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=Dict[str, Any])
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """내 프로필 조회"""
    return {
        "success": True,
        "data": {
            "id": current_user.id,
            "name": current_user.name,
            "phone": current_user.phone,
            "email": current_user.email,
            "birth_date": current_user.birth_date,
            "gender": current_user.gender,
            "address": current_user.address,
            "is_verified": current_user.is_verified,
            "verification_method": current_user.verification_method,
            "created_at": current_user.created_at
        }
    }



@router.get("/me/orders", response_model=Dict[str, Any])
async def get_my_orders(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_user_permissions(Permission.READ_ORDER)),
    db: Session = Depends(get_db)
):
    """내 주문 목록 조회"""
    orders = (
        db.query(Order)
        .filter(Order.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    total = db.query(Order).filter(Order.user_id == current_user.id).count()
    
    return {
        "success": True,
        "data": {
            "orders": [
                {
                    "id": order.id,
                    "order_number": order.order_number,
                    "status": order.status,
                    "total_amount": float(order.total_amount),
                    "delivery_address": order.delivery_address,
                    "created_at": order.created_at,
                    "updated_at": order.updated_at
                }
                for order in orders
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }

@router.get("/me/orders/{order_id}", response_model=Dict[str, Any])
async def get_my_order_detail(
    order_id: int,
    current_user: User = Depends(require_user_permissions(Permission.READ_ORDER)),
    db: Session = Depends(get_db)
):
    """내 주문 상세 조회"""
    order = db.query(Order).filter(Order.id == order_id).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주문을 찾을 수 없습니다."
        )
    
    # 리소스 소유권 확인
    check_resource_ownership(order.user_id, current_user.id)
    
    return {
        "success": True,
        "data": {
            "id": order.id,
            "order_number": order.order_number,
            "status": order.status,
            "total_amount": float(order.total_amount),
            "delivery_address": order.delivery_address,
            "created_at": order.created_at,
            "updated_at": order.updated_at,
            # TODO: 관련 데이터 (plan, device, number) 포함
        }
    }

@router.post("/", response_model=Dict[str, Any])
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    db: Session = Depends(get_db)
):
    """새 사용자 등록"""
    try:
        user = user_service.create_user(user_data)
        return {
            "success": True,
            "message": "사용자가 성공적으로 등록되었습니다.",
            "data": {
                "id": user.id,
                "phone": user.phone,
                "email": user.email,
                "is_verified": user.is_verified
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 등록 중 오류가 발생했습니다."
        )

@router.put("/me", response_model=Dict[str, Any])
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(require_user_permissions(Permission.WRITE_USER)),
    user_service: UserService = Depends(get_user_service)
):
    """내 프로필 수정"""
    try:
        updated_user = user_service.update_user(current_user.id, update_data)
        
        return {
            "success": True,
            "message": "프로필이 업데이트되었습니다.",
            "data": {
                "id": updated_user.id,
                "name": updated_user.name,
                "email": updated_user.email,
                "address": updated_user.address,
                "updated_at": updated_user.updated_at
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프로필 수정 중 오류가 발생했습니다."
        )

@router.get("/me/masked", response_model=Dict[str, Any])
async def get_my_masked_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """마스킹된 내 프로필 조회 (민감정보 보호)"""
    masked_info = user_service.get_masked_user_info(current_user)
    
    return {
        "success": True,
        "data": masked_info
    }

@router.post("/address/search", response_model=AddressSearchResponse)
async def search_address(
    search_request: AddressSearchRequest,
    user_service: UserService = Depends(get_user_service)
):
    """주소 검색"""
    try:
        result = user_service.search_address(search_request)
        return {
            "success": True,
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="주소 검색 중 오류가 발생했습니다."
        )

@router.post("/verification/request", response_model=UserVerificationResponse)
async def request_verification(
    verification_request: UserVerificationRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """본인인증 요청"""
    try:
        result = user_service.request_verification(current_user.id, verification_request)
        return UserVerificationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="본인인증 요청 중 오류가 발생했습니다."
        )

@router.post("/verification/confirm", response_model=Dict[str, Any])
async def confirm_verification(
    confirm_request: UserVerificationConfirmRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """본인인증 확인"""
    try:
        success = user_service.confirm_verification(
            current_user.id,
            confirm_request.verification_id,
            confirm_request.code
        )
        
        if success:
            return {
                "success": True,
                "message": "본인인증이 완료되었습니다."
            }
        else:
            return {
                "success": False,
                "message": "본인인증에 실패했습니다."
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="본인인증 확인 중 오류가 발생했습니다."
        )

@router.delete("/me", response_model=Dict[str, Any])
async def delete_my_account(
    deletion_request: UserDeletionRequest,
    current_user: User = Depends(require_user_permissions(Permission.DELETE_USER)),
    user_service: UserService = Depends(get_user_service)
):
    """계정 삭제 (GDPR 준수)"""
    try:
        success = user_service.delete_user(current_user.id, deletion_request.reason)
        
        if success:
            return {
                "success": True,
                "message": "계정이 삭제되었습니다."
            }
        else:
            return {
                "success": False,
                "message": "계정 삭제에 실패했습니다."
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="계정 삭제 중 오류가 발생했습니다."
        )

@router.get("/me/data-export", response_model=Dict[str, Any])
async def export_my_data(
    current_user: User = Depends(get_current_user),
    gdpr_service: GDPRService = Depends(get_gdpr_service)
):
    """내 개인정보 내보내기 (GDPR Article 20)"""
    try:
        user_data = gdpr_service.export_user_data(current_user.id)
        return {
            "success": True,
            "message": "개인정보 내보내기가 완료되었습니다.",
            "data": user_data
        }
    except Exception as e:
        logger.error(f"개인정보 내보내기 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개인정보 내보내기 중 오류가 발생했습니다."
        )

@router.get("/me/privacy-info", response_model=Dict[str, Any])
async def get_privacy_processing_info(
    current_user: User = Depends(get_current_user),
    gdpr_service: GDPRService = Depends(get_gdpr_service)
):
    """개인정보 처리 현황 조회 (GDPR Article 13, 14)"""
    try:
        processing_info = gdpr_service.get_data_processing_info(current_user.id)
        return {
            "success": True,
            "data": processing_info
        }
    except Exception as e:
        logger.error(f"개인정보 처리 현황 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개인정보 처리 현황 조회 중 오류가 발생했습니다."
        )

@router.post("/me/anonymize", response_model=Dict[str, Any])
async def anonymize_my_data(
    deletion_request: UserDeletionRequest,
    current_user: User = Depends(require_user_permissions(Permission.DELETE_USER)),
    gdpr_service: GDPRService = Depends(get_gdpr_service)
):
    """내 개인정보 익명화 (GDPR Article 17)"""
    try:
        success = gdpr_service.anonymize_user_data(
            current_user.id, 
            deletion_request.reason or "사용자 요청"
        )
        
        if success:
            return {
                "success": True,
                "message": "개인정보가 익명화되었습니다."
            }
        else:
            return {
                "success": False,
                "message": "개인정보 익명화에 실패했습니다."
            }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"개인정보 익명화 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="개인정보 익명화 중 오류가 발생했습니다."
        )