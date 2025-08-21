"""
주문 서비스 테스트
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.core.exceptions import InvalidOrderStatusError, OrderNotFoundError
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate
from app.services.order_service import OrderService


class TestOrderService:
    """주문 서비스 테스트 클래스"""

    def test_create_order_success(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 생성 성공 테스트"""
        # Given
        order_service = OrderService(db_session)
        order_data = OrderCreate(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            delivery_address="서울시 강남구 테헤란로 123",
        )

        # When
        result = order_service.create_order(order_data)

        # Then
        assert result.user_id == created_user.id
        assert result.plan_id == created_plan.id
        assert result.device_id == created_device.id
        assert result.number_id == created_number.id
        assert result.status == OrderStatus.PENDING
        assert result.order_number is not None
        assert len(result.order_number) == 12  # 주문번호 길이 확인

    def test_get_order_by_id_success(self, db_session, created_user, created_plan, created_device, created_number):
        """ID로 주문 조회 성공 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When
        result = order_service.get_order_by_id(order.id)

        # Then
        assert result.id == order.id
        assert result.order_number == order.order_number
        assert result.status == OrderStatus.PENDING

    def test_get_order_by_id_not_found(self, db_session):
        """존재하지 않는 주문 조회 테스트"""
        # Given
        order_service = OrderService(db_session)
        non_existent_id = 999

        # When & Then
        with pytest.raises(OrderNotFoundError):
            order_service.get_order_by_id(non_existent_id)

    def test_get_order_by_number_success(self, db_session, created_user, created_plan, created_device, created_number):
        """주문번호로 주문 조회 성공 테스트"""
        # Given
        order_service = OrderService(db_session)
        order_number = "ORD123456789"
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number=order_number,
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()

        # When
        result = order_service.get_order_by_number(order_number)

        # Then
        assert result.order_number == order_number
        assert result.status == OrderStatus.PENDING

    def test_update_order_status_success(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 상태 변경 성공 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When
        result = order_service.update_order_status(order.id, OrderStatus.PROCESSING, "심사 시작")

        # Then
        assert result.status == OrderStatus.PROCESSING
        # 상태 이력이 기록되었는지 확인
        status_history = order_service.get_order_status_history(order.id)
        assert len(status_history) > 0
        assert status_history[-1].status == OrderStatus.PROCESSING
        assert status_history[-1].note == "심사 시작"

    def test_update_order_status_invalid_transition(
        self, db_session, created_user, created_plan, created_device, created_number
    ):
        """잘못된 주문 상태 변경 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.COMPLETED,  # 이미 완료된 주문
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When & Then
        with pytest.raises(InvalidOrderStatusError):
            order_service.update_order_status(order.id, OrderStatus.PENDING, "되돌리기 시도")

    def test_calculate_total_amount(self, db_session, created_plan, created_device, created_number):
        """주문 총액 계산 테스트"""
        # Given
        order_service = OrderService(db_session)

        # When
        result = order_service.calculate_total_amount(
            plan_id=created_plan.id, device_id=created_device.id, number_id=created_number.id
        )

        # Then
        expected_total = created_plan.monthly_fee + created_device.price + created_number.additional_fee + 10000  # 개통비
        assert result == expected_total

    def test_get_orders_by_user(self, db_session, created_user, created_plan, created_device, created_number):
        """사용자별 주문 목록 조회 테스트"""
        # Given
        order_service = OrderService(db_session)

        # 사용자의 주문 2개 생성
        for i in range(2):
            order = Order(
                user_id=created_user.id,
                plan_id=created_plan.id,
                device_id=created_device.id,
                number_id=created_number.id,
                order_number=f"ORD12345678{i}",
                status=OrderStatus.PENDING,
                total_amount=Decimal("1255000"),
                delivery_address="서울시 강남구",
            )
            db_session.add(order)
        db_session.commit()

        # When
        result = order_service.get_orders_by_user(created_user.id)

        # Then
        assert len(result) == 2
        assert all(order.user_id == created_user.id for order in result)

    def test_get_orders_by_status(self, db_session, created_user, created_plan, created_device, created_number):
        """상태별 주문 목록 조회 테스트"""
        # Given
        order_service = OrderService(db_session)

        # 다양한 상태의 주문 생성
        statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING, OrderStatus.COMPLETED]
        for i, status in enumerate(statuses):
            order = Order(
                user_id=created_user.id,
                plan_id=created_plan.id,
                device_id=created_device.id,
                number_id=created_number.id,
                order_number=f"ORD12345678{i}",
                status=status,
                total_amount=Decimal("1255000"),
                delivery_address="서울시 강남구",
            )
            db_session.add(order)
        db_session.commit()

        # When
        result = order_service.get_orders_by_status(OrderStatus.PENDING)

        # Then
        assert len(result) == 1
        assert result[0].status == OrderStatus.PENDING

    @patch("app.services.notification_service.NotificationService.send_order_status_notification")
    def test_process_order_workflow(
        self, mock_notification, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """주문 워크플로우 처리 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When - 주문 처리 워크플로우 실행
        order_service.process_order_workflow(order.id, created_admin.id)

        # Then
        updated_order = order_service.get_order_by_id(order.id)
        assert updated_order.status == OrderStatus.PROCESSING
        mock_notification.assert_called_once()

    def test_cancel_order_success(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 취소 성공 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.PENDING,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When
        result = order_service.cancel_order(order.id, "고객 요청")

        # Then
        assert result.status == OrderStatus.CANCELLED

    def test_cancel_order_invalid_status(self, db_session, created_user, created_plan, created_device, created_number):
        """취소 불가능한 상태의 주문 취소 테스트"""
        # Given
        order_service = OrderService(db_session)
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.COMPLETED,  # 이미 완료된 주문
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # When & Then
        with pytest.raises(InvalidOrderStatusError):
            order_service.cancel_order(order.id, "고객 요청")

    def test_get_order_statistics(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 통계 조회 테스트"""
        # Given
        order_service = OrderService(db_session)

        # 다양한 상태의 주문 생성
        statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING, OrderStatus.COMPLETED, OrderStatus.CANCELLED]
        for i, status in enumerate(statuses):
            order = Order(
                user_id=created_user.id,
                plan_id=created_plan.id,
                device_id=created_device.id,
                number_id=created_number.id,
                order_number=f"ORD12345678{i}",
                status=status,
                total_amount=Decimal("1255000"),
                delivery_address="서울시 강남구",
            )
            db_session.add(order)
        db_session.commit()

        # When
        result = order_service.get_order_statistics()

        # Then
        assert result["total_orders"] == 4
        assert result["pending_orders"] == 1
        assert result["processing_orders"] == 1
        assert result["completed_orders"] == 1
        assert result["cancelled_orders"] == 1
