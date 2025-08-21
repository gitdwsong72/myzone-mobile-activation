import hashlib
import json
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.plan import Plan
from ..schemas.plan import PlanCreate, PlanFilter, PlanUpdate
from .cache_service import cache_service, cached


class PlanService:
    """요금제 서비스"""

    def __init__(self, db: Session):
        self.db = db
        self.cache = cache_service

    def get_plans(self, filters: PlanFilter, page: int = 1, size: int = 20) -> tuple[List[Plan], int]:
        """요금제 목록 조회 (필터링 및 페이징 지원)"""
        query = self.db.query(Plan)

        # 필터 적용
        conditions = []

        if filters.category:
            conditions.append(Plan.category == filters.category)

        if filters.min_price is not None:
            conditions.append(Plan.monthly_fee >= filters.min_price)

        if filters.max_price is not None:
            conditions.append(Plan.monthly_fee <= filters.max_price)

        if filters.is_active is not None:
            conditions.append(Plan.is_active == filters.is_active)

        if filters.search:
            search_term = f"%{filters.search}%"
            conditions.append(or_(Plan.name.ilike(search_term), Plan.description.ilike(search_term)))

        if conditions:
            query = query.filter(and_(*conditions))

        # 전체 개수 조회
        total = query.count()

        # 정렬 및 페이징
        plans = query.order_by(Plan.display_order.asc(), Plan.id.asc()).offset((page - 1) * size).limit(size).all()

        return plans, total

    def get_plan_by_id(self, plan_id: int) -> Plan:
        """ID로 요금제 조회 (캐시 적용)"""
        # 캐시에서 조회
        cached_plan = self.cache.get_cached_plan(plan_id)
        if cached_plan:
            # 캐시된 데이터를 Plan 객체로 변환
            plan = Plan(**cached_plan)
            return plan

        # 캐시 미스 시 DB에서 조회
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="요금제를 찾을 수 없습니다.")

        # 결과 캐싱
        plan_dict = {
            "id": plan.id,
            "name": plan.name,
            "description": plan.description,
            "category": plan.category,
            "monthly_fee": float(plan.monthly_fee),
            "setup_fee": float(plan.setup_fee),
            "data_limit": plan.data_limit,
            "call_minutes": plan.call_minutes,
            "sms_count": plan.sms_count,
            "additional_services": plan.additional_services,
            "discount_rate": float(plan.discount_rate),
            "promotion_text": plan.promotion_text,
            "is_active": plan.is_active,
            "display_order": plan.display_order,
            "created_at": plan.created_at.isoformat() if plan.created_at else None,
            "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
        }
        self.cache.cache_plan(plan_id, plan_dict)

        return plan

    def get_active_plans(self) -> List[Plan]:
        """활성화된 요금제 목록 조회 (캐시 적용)"""
        # 캐시에서 조회
        cached_plans = self.cache.get_cached_plans_list("active")
        if cached_plans:
            return [Plan(**plan_data) for plan_data in cached_plans]

        # 캐시 미스 시 DB에서 조회
        plans = self.db.query(Plan).filter(Plan.is_active == True).order_by(Plan.display_order.asc(), Plan.id.asc()).all()

        # 결과 캐싱
        plans_data = []
        for plan in plans:
            plan_dict = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "category": plan.category,
                "monthly_fee": float(plan.monthly_fee),
                "setup_fee": float(plan.setup_fee),
                "data_limit": plan.data_limit,
                "call_minutes": plan.call_minutes,
                "sms_count": plan.sms_count,
                "additional_services": plan.additional_services,
                "discount_rate": float(plan.discount_rate),
                "promotion_text": plan.promotion_text,
                "is_active": plan.is_active,
                "display_order": plan.display_order,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
            }
            plans_data.append(plan_dict)

        self.cache.cache_plans_list("active", plans_data)
        return plans

    def get_plans_by_category(self, category: str) -> List[Plan]:
        """카테고리별 요금제 조회 (캐시 적용)"""
        # 캐시에서 조회
        cached_plans = self.cache.get_cached_plans_list(category)
        if cached_plans:
            return [Plan(**plan_data) for plan_data in cached_plans]

        # 캐시 미스 시 DB에서 조회
        plans = (
            self.db.query(Plan)
            .filter(and_(Plan.category == category, Plan.is_active == True))
            .order_by(Plan.display_order.asc(), Plan.id.asc())
            .all()
        )

        # 결과 캐싱
        plans_data = []
        for plan in plans:
            plan_dict = {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "category": plan.category,
                "monthly_fee": float(plan.monthly_fee),
                "setup_fee": float(plan.setup_fee),
                "data_limit": plan.data_limit,
                "call_minutes": plan.call_minutes,
                "sms_count": plan.sms_count,
                "additional_services": plan.additional_services,
                "discount_rate": float(plan.discount_rate),
                "promotion_text": plan.promotion_text,
                "is_active": plan.is_active,
                "display_order": plan.display_order,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None,
            }
            plans_data.append(plan_dict)

        self.cache.cache_plans_list(category, plans_data)
        return plans

    def get_available_categories(self) -> List[str]:
        """사용 가능한 카테고리 목록 조회"""
        categories = self.db.query(Plan.category).filter(Plan.is_active == True).distinct().all()
        return [category[0] for category in categories]

    def create_plan(self, plan_data: PlanCreate) -> Plan:
        """요금제 생성 (관리자용)"""
        plan = Plan(**plan_data.model_dump())
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)

        # 캐시 무효화
        self.cache.invalidate_plan_cache()

        return plan

    def update_plan(self, plan_id: int, plan_data: PlanUpdate) -> Plan:
        """요금제 수정 (관리자용)"""
        plan = self.get_plan_by_id(plan_id)

        update_data = plan_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(plan, field, value)

        self.db.commit()
        self.db.refresh(plan)

        # 캐시 무효화
        self.cache.invalidate_plan_cache(plan_id)

        return plan

    def delete_plan(self, plan_id: int) -> bool:
        """요금제 삭제 (관리자용) - 소프트 삭제"""
        plan = self.get_plan_by_id(plan_id)
        plan.is_active = False
        self.db.commit()

        # 캐시 무효화
        self.cache.invalidate_plan_cache(plan_id)

        return True

    def get_recommended_plans(self, limit: int = 3) -> List[Plan]:
        """추천 요금제 조회 (할인율이 높은 순)"""
        return (
            self.db.query(Plan)
            .filter(Plan.is_active == True)
            .order_by(Plan.discount_rate.desc(), Plan.display_order.asc())
            .limit(limit)
            .all()
        )
