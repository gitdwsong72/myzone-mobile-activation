"""
사용자 관리 서비스
"""

import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from fastapi import Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..core.encryption import decrypt_personal_data, encrypt_personal_data, encryption_service
from ..core.security import get_password_hash, verify_password
from ..models.order import Order
from ..models.user import User
from ..schemas.user import (
    AddressSearchRequest,
    UserCreate,
    UserMaskedResponse,
    UserResponse,
    UserUpdate,
    UserVerificationRequest,
)

logger = logging.getLogger(__name__)


class UserService:
    """사용자 관리 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """
        새 사용자 생성

        Args:
            user_data: 사용자 생성 데이터

        Returns:
            생성된 사용자 객체
        """
        # 중복 확인
        existing_user = self.db.query(User).filter(or_(User.phone == user_data.phone, User.email == user_data.email)).first()

        if existing_user:
            if existing_user.phone == user_data.phone:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 전화번호입니다.")
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 등록된 이메일 주소입니다.")

        # 사용자 생성 (암호화는 모델에서 자동 처리)
        db_user = User(
            name=user_data.name,
            phone=user_data.phone,
            email=user_data.email,
            birth_date=user_data.birth_date,
            gender=user_data.gender,
            address=user_data.address,
            verification_method=user_data.verification_method,
            is_verified=False,
            is_active=True,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        logger.info(f"새 사용자 생성: {db_user.id}")
        return db_user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        ID로 사용자 조회 (복호화는 모델에서 자동 처리)

        Args:
            user_id: 사용자 ID

        Returns:
            사용자 객체 또는 None
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        전화번호로 사용자 조회

        Args:
            phone: 전화번호

        Returns:
            사용자 객체 또는 None
        """
        return self.db.query(User).filter(User.phone == phone).first()

    def update_user(self, user_id: int, update_data: UserUpdate) -> User:
        """
        사용자 정보 수정

        Args:
            user_id: 사용자 ID
            update_data: 수정할 데이터

        Returns:
            수정된 사용자 객체
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        # 수정 가능한 필드만 업데이트 (암호화는 모델에서 자동 처리)
        update_dict = update_data.dict(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"사용자 정보 수정: {user_id}")
        return user

    def delete_user(self, user_id: int, reason: Optional[str] = None) -> bool:
        """
        사용자 계정 삭제 (GDPR 준수)

        Args:
            user_id: 사용자 ID
            reason: 삭제 사유

        Returns:
            삭제 성공 여부
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        # 진행 중인 주문 확인
        active_orders = (
            self.db.query(Order)
            .filter(and_(Order.user_id == user_id, Order.status.in_(["pending", "processing", "confirmed"])))
            .count()
        )

        if active_orders > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="진행 중인 주문이 있어 계정을 삭제할 수 없습니다."
            )

        # GDPR 준수: 개인정보 완전 삭제
        user.name = "[삭제된 사용자]"
        user.email = None
        user.address = "[삭제됨]"
        user.is_active = False
        user.updated_at = datetime.utcnow()

        self.db.commit()

        logger.info(f"사용자 계정 삭제: {user_id}, 사유: {reason}")
        return True

    def get_masked_user_info(self, user: User) -> Dict[str, Any]:
        """
        마스킹된 사용자 정보 반환

        Args:
            user: 사용자 객체

        Returns:
            마스킹된 사용자 정보
        """
        return {
            "id": user.id,
            "name": encryption_service.mask_name(user.name),
            "phone": encryption_service.mask_phone_number(user.phone),
            "email": encryption_service.mask_email(user.email) if user.email else None,
            "birth_date": user.birth_date,
            "gender": user.gender,
            "address": self._mask_address(user.address),
            "is_verified": user.is_verified,
            "is_active": user.is_active,
            "created_at": user.created_at,
        }

    def search_address(self, search_request: AddressSearchRequest) -> Dict[str, Any]:
        """
        주소 검색 API 연동

        Args:
            search_request: 주소 검색 요청

        Returns:
            주소 검색 결과
        """
        try:
            # 카카오 주소 검색 API 사용 (예시)
            api_key = os.getenv("KAKAO_API_KEY")
            if not api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="주소 검색 서비스가 설정되지 않았습니다."
                )

            url = "https://dapi.kakao.com/v2/local/search/address.json"
            headers = {"Authorization": f"KakaoAK {api_key}"}
            params = {"query": search_request.keyword, "page": search_request.page, "size": search_request.size}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # 응답 데이터 변환
            addresses = []
            for item in data.get("documents", []):
                addresses.append(
                    {
                        "zipcode": item.get("address", {}).get("zip_code", ""),
                        "address": item.get("address_name", ""),
                        "detail": item.get("address", {}).get("region_3depth_name", ""),
                    }
                )

            return {
                "addresses": addresses,
                "total": data.get("meta", {}).get("total_count", 0),
                "page": search_request.page,
                "size": search_request.size,
            }

        except requests.RequestException as e:
            logger.error(f"주소 검색 API 오류: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="주소 검색 서비스에 일시적인 문제가 발생했습니다."
            )

    def request_verification(self, user_id: int, verification_request: UserVerificationRequest) -> Dict[str, Any]:
        """
        본인인증 요청

        Args:
            user_id: 사용자 ID
            verification_request: 인증 요청 데이터

        Returns:
            인증 요청 결과
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        # 인증 ID 생성
        verification_id = f"verify_{uuid.uuid4().hex[:8]}"
        expires_at = datetime.utcnow() + timedelta(minutes=5)

        if verification_request.method == "SMS":
            # SMS 인증 처리 (실제 구현에서는 SMS 서비스 연동)
            return {
                "success": True,
                "message": "인증번호가 발송되었습니다.",
                "verification_id": verification_id,
                "expires_at": expires_at,
            }
        elif verification_request.method == "CERTIFICATE":
            # 공인인증서 인증 처리
            return {
                "success": True,
                "message": "공인인증서 인증을 진행해주세요.",
                "verification_id": verification_id,
                "expires_at": expires_at,
            }
        else:
            # 간편인증 처리
            return {
                "success": True,
                "message": "간편인증을 진행해주세요.",
                "verification_id": verification_id,
                "expires_at": expires_at,
            }

    def confirm_verification(self, user_id: int, verification_id: str, code: str) -> bool:
        """
        본인인증 확인

        Args:
            user_id: 사용자 ID
            verification_id: 인증 ID
            code: 인증번호

        Returns:
            인증 성공 여부
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")

        # 실제 구현에서는 Redis 등에 저장된 인증 정보와 비교
        # 여기서는 간단한 예시로 처리
        if code == "123456":  # 테스트용 코드
            user.is_verified = True
            user.verification_method = "SMS"
            user.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"사용자 본인인증 완료: {user_id}")
            return True
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="인증번호가 올바르지 않습니다.")

    def _mask_address(self, address: str) -> str:
        """주소 마스킹 처리"""
        if not address:
            return ""

        # 상세 주소 부분만 마스킹 (예: 서울특별시 강남구 테헤란로 ****)
        parts = address.split()
        if len(parts) > 3:
            return " ".join(parts[:3]) + " " + "****"
        else:
            return encryption_service.mask_sensitive_data(address, visible_chars=10)


from ..core.deps import get_db


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """사용자 서비스 의존성 주입"""
    return UserService(db)
