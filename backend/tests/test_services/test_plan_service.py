"""
요금제 서비스 테스트
"""
import pytest
from decimal import Decimal

from app.services.plan_service import PlanService
from app.models.plan import Plan
from app.schemas.plan import PlanCreate, PlanUpdate
from app.core.exceptions import PlanNotFoundError


class TestPlanService:
    """요금제 서비스 테스트 클래스"""
    
    def test_create_plan_success(self, db_session, sample_plan_data):
        """요금제 생성 성공 테스트"""
        # Given
        plan_service = PlanService(db_session)
        plan_data = PlanCreate(**sample_plan_data)
        
        # When
        result = plan_service.create_plan(plan_data)
        
        # Then
        assert result.name == sample_plan_data["name"]
        assert result.monthly_fee == sample_plan_data["monthly_fee"]
        assert result.data_limit == sample_plan_data["data_limit"]
        assert result.is_active is True
        assert result.id is not None
    
    def test_get_plan_by_id_success(self, db_session, created_plan):
        """ID로 요금제 조회 성공 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # When
        result = plan_service.get_plan_by_id(created_plan.id)
        
        # Then
        assert result.id == created_plan.id
        assert result.name == created_plan.name
        assert result.monthly_fee == created_plan.monthly_fee
    
    def test_get_plan_by_id_not_found(self, db_session):
        """존재하지 않는 요금제 조회 테스트"""
        # Given
        plan_service = PlanService(db_session)
        non_existent_id = 999
        
        # When & Then
        with pytest.raises(PlanNotFoundError):
            plan_service.get_plan_by_id(non_existent_id)
    
    def test_get_active_plans(self, db_session):
        """활성 요금제 목록 조회 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # 활성/비활성 요금제 생성
        active_plan = Plan(
            name="활성 요금제",
            description="활성 요금제입니다",
            monthly_fee=30000,
            data_limit=10,
            call_minutes=300,
            sms_count=100,
            category="LTE",
            is_active=True
        )
        inactive_plan = Plan(
            name="비활성 요금제",
            description="비활성 요금제입니다",
            monthly_fee=20000,
            data_limit=5,
            call_minutes=200,
            sms_count=50,
            category="LTE",
            is_active=False
        )
        
        db_session.add_all([active_plan, inactive_plan])
        db_session.commit()
        
        # When
        result = plan_service.get_active_plans()
        
        # Then
        assert len(result) == 1
        assert result[0].name == "활성 요금제"
        assert result[0].is_active is True
    
    def test_get_plans_by_category(self, db_session):
        """카테고리별 요금제 조회 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # 다양한 카테고리 요금제 생성
        plans_data = [
            {"name": "5G 프리미엄", "category": "5G", "monthly_fee": 55000},
            {"name": "5G 스탠다드", "category": "5G", "monthly_fee": 45000},
            {"name": "LTE 프리미엄", "category": "LTE", "monthly_fee": 35000}
        ]
        
        for plan_data in plans_data:
            plan_data.update({
                "description": f"{plan_data['name']} 요금제",
                "data_limit": 10,
                "call_minutes": 300,
                "sms_count": 100,
                "is_active": True
            })
            plan = Plan(**plan_data)
            db_session.add(plan)
        db_session.commit()
        
        # When
        result = plan_service.get_plans_by_category("5G")
        
        # Then
        assert len(result) == 2
        assert all(plan.category == "5G" for plan in result)
    
    def test_update_plan_success(self, db_session, created_plan):
        """요금제 수정 성공 테스트"""
        # Given
        plan_service = PlanService(db_session)
        update_data = PlanUpdate(
            name="수정된 요금제",
            monthly_fee=60000,
            description="수정된 설명"
        )
        
        # When
        result = plan_service.update_plan(created_plan.id, update_data)
        
        # Then
        assert result.name == "수정된 요금제"
        assert result.monthly_fee == 60000
        assert result.description == "수정된 설명"
        assert result.data_limit == created_plan.data_limit  # 변경되지 않은 필드
    
    def test_update_plan_not_found(self, db_session):
        """존재하지 않는 요금제 수정 테스트"""
        # Given
        plan_service = PlanService(db_session)
        non_existent_id = 999
        update_data = PlanUpdate(name="수정된 요금제")
        
        # When & Then
        with pytest.raises(PlanNotFoundError):
            plan_service.update_plan(non_existent_id, update_data)
    
    def test_deactivate_plan_success(self, db_session, created_plan):
        """요금제 비활성화 성공 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # When
        result = plan_service.deactivate_plan(created_plan.id)
        
        # Then
        assert result.is_active is False
    
    def test_get_popular_plans(self, db_session):
        """인기 요금제 조회 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # 테스트 요금제들 생성
        plans_data = [
            {"name": "인기 요금제 1", "monthly_fee": 30000, "popularity_score": 95},
            {"name": "인기 요금제 2", "monthly_fee": 40000, "popularity_score": 90},
            {"name": "일반 요금제", "monthly_fee": 25000, "popularity_score": 70}
        ]
        
        for plan_data in plans_data:
            plan_data.update({
                "description": f"{plan_data['name']} 설명",
                "data_limit": 10,
                "call_minutes": 300,
                "sms_count": 100,
                "category": "LTE",
                "is_active": True
            })
            plan = Plan(**plan_data)
            db_session.add(plan)
        db_session.commit()
        
        # When
        result = plan_service.get_popular_plans(limit=2)
        
        # Then
        assert len(result) == 2
        assert result[0].popularity_score >= result[1].popularity_score
    
    def test_search_plans_by_price_range(self, db_session):
        """가격대별 요금제 검색 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # 다양한 가격대 요금제 생성
        plans_data = [
            {"name": "저가 요금제", "monthly_fee": 20000},
            {"name": "중가 요금제", "monthly_fee": 35000},
            {"name": "고가 요금제", "monthly_fee": 55000}
        ]
        
        for plan_data in plans_data:
            plan_data.update({
                "description": f"{plan_data['name']} 설명",
                "data_limit": 10,
                "call_minutes": 300,
                "sms_count": 100,
                "category": "LTE",
                "is_active": True
            })
            plan = Plan(**plan_data)
            db_session.add(plan)
        db_session.commit()
        
        # When
        result = plan_service.search_plans_by_price_range(min_price=30000, max_price=50000)
        
        # Then
        assert len(result) == 1
        assert result[0].name == "중가 요금제"
        assert 30000 <= result[0].monthly_fee <= 50000
    
    def test_compare_plans(self, db_session):
        """요금제 비교 테스트"""
        # Given
        plan_service = PlanService(db_session)
        
        # 비교할 요금제들 생성
        plan1 = Plan(
            name="요금제 A",
            description="요금제 A 설명",
            monthly_fee=30000,
            data_limit=10,
            call_minutes=300,
            sms_count=100,
            category="LTE",
            is_active=True
        )
        plan2 = Plan(
            name="요금제 B",
            description="요금제 B 설명",
            monthly_fee=45000,
            data_limit=20,
            call_minutes=500,
            sms_count=200,
            category="5G",
            is_active=True
        )
        
        db_session.add_all([plan1, plan2])
        db_session.commit()
        
        # When
        result = plan_service.compare_plans([plan1.id, plan2.id])
        
        # Then
        assert len(result) == 2
        assert result[0]["name"] == "요금제 A"
        assert result[1]["name"] == "요금제 B"
        assert "monthly_fee" in result[0]
        assert "data_limit" in result[0]