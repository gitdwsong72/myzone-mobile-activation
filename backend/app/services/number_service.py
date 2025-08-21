import hashlib
import re
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from ..models.number import Number
from ..schemas.number import (
    CategoryInfo,
    NumberCreate,
    NumberFilter,
    NumberPatternAnalysis,
    NumberReservationRequest,
    NumberSearchRequest,
    NumberUpdate,
)
from .cache_service import cache_service


class NumberService:
    """전화번호 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_service

    def get_numbers(self, filters: NumberFilter, page: int = 1, size: int = 20) -> tuple[List[Number], int]:
        """전화번호 목록 조회 (필터링 및 페이징 지원)"""
        query = self.db.query(Number)

        # 만료된 예약 정리
        self._cleanup_expired_reservations()

        # 필터 적용
        conditions = []

        if filters.category:
            conditions.append(Number.category == filters.category)

        if filters.status:
            conditions.append(Number.status == filters.status)

        if filters.is_premium is not None:
            conditions.append(Number.is_premium == filters.is_premium)

        if filters.pattern_type:
            conditions.append(Number.pattern_type == filters.pattern_type)

        if filters.min_fee is not None:
            conditions.append(Number.additional_fee >= filters.min_fee)

        if filters.max_fee is not None:
            conditions.append(Number.additional_fee <= filters.max_fee)

        if filters.search:
            # 번호 끝자리 또는 패턴 검색
            search_pattern = f"%{filters.search}%"
            conditions.append(Number.number.ilike(search_pattern))

        if conditions:
            query = query.filter(and_(*conditions))

        # 전체 개수 조회
        total = query.count()

        # 정렬 및 페이징 (프리미엄 우선, 추가 요금 낮은 순)
        numbers = (
            query.order_by(Number.is_premium.desc(), Number.additional_fee.asc(), Number.number.asc())
            .offset((page - 1) * size)
            .limit(size)
            .all()
        )

        return numbers, total

    def get_number_by_id(self, number_id: int) -> Number:
        """ID로 전화번호 조회"""
        number = self.db.query(Number).filter(Number.id == number_id).first()
        if not number:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="전화번호를 찾을 수 없습니다.")
        return number

    def get_available_numbers(self, category: Optional[str] = None, limit: int = 20) -> List[Number]:
        """사용 가능한 번호 목록 조회 (캐시 적용)"""
        cache_key = category or "all"

        # 캐시에서 조회
        cached_numbers = self.cache.get_cached_available_numbers(cache_key)
        if cached_numbers:
            # 제한된 개수만 반환
            limited_numbers = cached_numbers[:limit]
            return [Number(**number_data) for number_data in limited_numbers]

        # 캐시 미스 시 DB에서 조회
        self._cleanup_expired_reservations()

        query = self.db.query(Number).filter(Number.status == "available")

        if category:
            query = query.filter(Number.category == category)

        numbers = (
            query.order_by(Number.is_premium.desc(), Number.additional_fee.asc()).limit(100).all()  # 캐시용으로 더 많이 조회
        )

        # 결과 캐싱
        numbers_data = []
        for number in numbers:
            number_dict = {
                "id": number.id,
                "number": number.number,
                "category": number.category,
                "additional_fee": float(number.additional_fee),
                "status": number.status,
                "reserved_until": number.reserved_until.isoformat() if number.reserved_until else None,
                "reserved_by_order_id": number.reserved_by_order_id,
                "is_premium": number.is_premium,
                "pattern_type": number.pattern_type,
                "created_at": number.created_at.isoformat() if number.created_at else None,
                "updated_at": number.updated_at.isoformat() if number.updated_at else None,
            }
            numbers_data.append(number_dict)

        # 짧은 TTL로 캐싱 (번호 상태가 자주 변경됨)
        self.cache.cache_available_numbers(cache_key, numbers_data, ttl=300)  # 5분

        return numbers[:limit]

    def search_numbers(self, search_request: NumberSearchRequest) -> List[Number]:
        """번호 패턴 검색 (캐시 적용)"""
        # 검색 쿼리를 캐시 키로 사용
        search_query = f"{search_request.pattern}:{search_request.category or 'all'}:{search_request.limit}"

        # 캐시에서 조회
        cached_results = self.cache.get_cached_number_search(search_query)
        if cached_results:
            return [Number(**number_data) for number_data in cached_results]

        # 캐시 미스 시 DB에서 검색
        self._cleanup_expired_reservations()

        query = self.db.query(Number).filter(Number.status == "available")

        if search_request.category:
            query = query.filter(Number.category == search_request.category)

        # 패턴 검색
        pattern = search_request.pattern
        if pattern.isdigit():
            # 숫자만 입력된 경우 끝자리 검색
            search_pattern = f"%{pattern}"
            query = query.filter(Number.number.like(search_pattern))
        else:
            # 특정 패턴 검색
            search_pattern = f"%{pattern}%"
            query = query.filter(Number.number.ilike(search_pattern))

        numbers = query.order_by(Number.is_premium.desc(), Number.additional_fee.asc()).limit(search_request.limit).all()

        # 결과 캐싱
        numbers_data = []
        for number in numbers:
            number_dict = {
                "id": number.id,
                "number": number.number,
                "category": number.category,
                "additional_fee": float(number.additional_fee),
                "status": number.status,
                "reserved_until": number.reserved_until.isoformat() if number.reserved_until else None,
                "reserved_by_order_id": number.reserved_by_order_id,
                "is_premium": number.is_premium,
                "pattern_type": number.pattern_type,
                "created_at": number.created_at.isoformat() if number.created_at else None,
                "updated_at": number.updated_at.isoformat() if number.updated_at else None,
            }
            numbers_data.append(number_dict)

        # 검색 결과 캐싱 (10분)
        self.cache.cache_number_search(search_query, numbers_data, ttl=600)

        return numbers

    def get_categories(self) -> List[CategoryInfo]:
        """사용 가능한 카테고리 정보 조회"""
        categories_data = (
            self.db.query(
                Number.category,
                func.count(Number.id).label("count"),
                func.min(Number.additional_fee).label("min_fee"),
                func.max(Number.additional_fee).label("max_fee"),
            )
            .filter(Number.status == "available")
            .group_by(Number.category)
            .all()
        )

        category_descriptions = {
            "일반": "일반적인 전화번호",
            "연속": "연속된 숫자가 포함된 번호",
            "특별": "특별한 의미가 있는 번호",
            "프리미엄": "프리미엄 번호",
        }

        return [
            CategoryInfo(
                category=category,
                count=count,
                min_fee=min_fee,
                max_fee=max_fee,
                description=category_descriptions.get(category, ""),
            )
            for category, count, min_fee, max_fee in categories_data
        ]

    def reserve_number(self, number_id: int, reservation_request: NumberReservationRequest) -> Number:
        """번호 예약"""
        number = self.get_number_by_id(number_id)

        if not number.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 예약되었거나 사용 중인 번호입니다.")

        try:
            number.reserve(reservation_request.order_id, reservation_request.minutes)
            self.db.commit()
            self.db.refresh(number)

            # 번호 상태 변경으로 인한 캐시 무효화
            self.cache.invalidate_number_cache()

            return number
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    def release_reservation(self, number_id: int, order_id: str) -> Number:
        """번호 예약 해제"""
        number = self.get_number_by_id(number_id)

        if number.reserved_by_order_id != order_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="해당 주문으로 예약된 번호가 아닙니다.")

        number.release()
        self.db.commit()
        self.db.refresh(number)

        # 번호 상태 변경으로 인한 캐시 무효화
        self.cache.invalidate_number_cache()

        return number

    def assign_number(self, number_id: int) -> Number:
        """번호 할당 (개통 완료)"""
        number = self.get_number_by_id(number_id)
        number.assign()
        self.db.commit()
        self.db.refresh(number)
        return number

    def analyze_number_pattern(self, number_str: str) -> NumberPatternAnalysis:
        """번호 패턴 분석"""
        # 번호에서 숫자만 추출
        digits = re.sub(r"[^0-9]", "", number_str)
        last_8_digits = digits[-8:]  # 뒤 8자리만 분석

        pattern_type = "일반"
        score = 0
        is_premium = False
        description = "일반적인 번호입니다."

        # 연속 숫자 검사
        consecutive_count = self._find_consecutive_digits(last_8_digits)
        if consecutive_count >= 4:
            pattern_type = "연속"
            score += consecutive_count * 10
            is_premium = True
            description = f"{consecutive_count}개의 연속 숫자가 포함된 번호입니다."

        # 반복 숫자 검사
        repeat_count = self._find_repeated_digits(last_8_digits)
        if repeat_count >= 3:
            pattern_type = "반복"
            score += repeat_count * 8
            is_premium = True
            description = f"{repeat_count}개의 반복 숫자가 포함된 번호입니다."

        # 대칭 패턴 검사
        if self._is_palindrome(last_8_digits):
            pattern_type = "대칭"
            score += 50
            is_premium = True
            description = "대칭 패턴의 번호입니다."

        # 특별한 숫자 조합 검사
        special_patterns = [
            "1234",
            "5678",
            "9876",
            "0000",
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
        ]
        for pattern in special_patterns:
            if pattern in last_8_digits:
                pattern_type = "특별"
                score += 30
                is_premium = True
                description = f"특별한 패턴 '{pattern}'이 포함된 번호입니다."
                break

        return NumberPatternAnalysis(
            number=number_str, pattern_type=pattern_type, is_premium=is_premium, score=score, description=description
        )

    def create_number(self, number_data: NumberCreate) -> Number:
        """전화번호 생성 (관리자용)"""
        # 중복 번호 확인
        existing = self.db.query(Number).filter(Number.number == number_data.number).first()
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="이미 존재하는 전화번호입니다.")

        # 패턴 분석
        analysis = self.analyze_number_pattern(number_data.number)

        number = Number(**number_data.model_dump())
        number.pattern_type = analysis.pattern_type
        number.is_premium = analysis.is_premium

        self.db.add(number)
        self.db.commit()
        self.db.refresh(number)
        return number

    def update_number(self, number_id: int, number_data: NumberUpdate) -> Number:
        """전화번호 수정 (관리자용)"""
        number = self.get_number_by_id(number_id)

        update_data = number_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(number, field, value)

        self.db.commit()
        self.db.refresh(number)
        return number

    def delete_number(self, number_id: int) -> bool:
        """전화번호 삭제 (관리자용)"""
        number = self.get_number_by_id(number_id)

        if number.status != "available":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="예약되었거나 사용 중인 번호는 삭제할 수 없습니다."
            )

        self.db.delete(number)
        self.db.commit()
        return True

    def _cleanup_expired_reservations(self):
        """만료된 예약 정리"""
        expired_numbers = (
            self.db.query(Number).filter(and_(Number.status == "reserved", Number.reserved_until < datetime.utcnow())).all()
        )

        for number in expired_numbers:
            number.release()

        if expired_numbers:
            self.db.commit()

    def _find_consecutive_digits(self, digits: str) -> int:
        """연속 숫자 찾기"""
        max_consecutive = 0
        current_consecutive = 1

        for i in range(1, len(digits)):
            if int(digits[i]) == int(digits[i - 1]) + 1:
                current_consecutive += 1
            else:
                max_consecutive = max(max_consecutive, current_consecutive)
                current_consecutive = 1

        return max(max_consecutive, current_consecutive)

    def _find_repeated_digits(self, digits: str) -> int:
        """반복 숫자 찾기"""
        max_repeat = 0
        current_repeat = 1

        for i in range(1, len(digits)):
            if digits[i] == digits[i - 1]:
                current_repeat += 1
            else:
                max_repeat = max(max_repeat, current_repeat)
                current_repeat = 1

        return max(max_repeat, current_repeat)

    def _is_palindrome(self, digits: str) -> bool:
        """대칭 패턴 확인"""
        return digits == digits[::-1]
