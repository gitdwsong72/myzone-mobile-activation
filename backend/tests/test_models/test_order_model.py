"""
주문 모델 테스트
"""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.order import Order, OrderStatus
from app.models.order_status_history import OrderStatusHistory


class TestOrderModel:
    """주문 모델 테스트 클래스"""

    def test_create_order_success(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 모델 생성 성공 테스트"""
        # Given
        order_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "order_number": "ORD123456789",
            "status": OrderStatus.PENDING,
            "total_amount": Decimal("1255000"),
            "delivery_address": "서울시 강남구 테헤란로 123",
        }
        order = Order(**order_data)

        # When
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)

        # Then
        assert order.id is not None
        assert order.order_number == "ORD123456789"
        assert order.status == OrderStatus.PENDING
        assert order.total_amount == Decimal("1255000")
        assert order.created_at is not None
        assert order.updated_at is not None

    def test_order_number_unique_constraint(self, db_session, created_user, created_plan, created_device, created_number):
        """주문번호 유니크 제약 조건 테스트"""
        # Given
        order1_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "order_number": "ORD123456789",
            "status": OrderStatus.PENDING,
            "total_amount": Decimal("1255000"),
            "delivery_address": "서울시 강남구",
        }
        order2_data = order1_data.copy()

        order1 = Order(**order1_data)
        order2 = Order(**order2_data)  # 같은 주문번호

        # When
        db_session.add(order1)
        db_session.commit()

        db_session.add(order2)

        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_order_required_fields(self, db_session):
        """주문 필수 필드 테스트"""
        # Given
        order = Order()  # 필수 필드 없이 생성

        # When
        db_session.add(order)

        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_order_foreign_key_constraints(self, db_session):
        """주문 외래키 제약 조건 테스트"""
        # Given
        order_data = {
            "user_id": 999,  # 존재하지 않는 사용자 ID
            "plan_id": 999,  # 존재하지 않는 요금제 ID
            "device_id": 999,  # 존재하지 않는 단말기 ID
            "number_id": 999,  # 존재하지 않는 번호 ID
            "order_number": "ORD123456789",
            "status": OrderStatus.PENDING,
            "total_amount": Decimal("1255000"),
            "delivery_address": "서울시 강남구",
        }
        order = Order(**order_data)

        # When
        db_session.add(order)

        # Then
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_order_status_enum(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 상태 열거형 테스트"""
        # Given
        valid_statuses = [
            OrderStatus.PENDING,
            OrderStatus.PROCESSING,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.FAILED,
        ]

        for i, status in enumerate(valid_statuses):
            order_data = {
                "user_id": created_user.id,
                "plan_id": created_plan.id,
                "device_id": created_device.id,
                "number_id": created_number.id,
                "order_number": f"ORD12345678{i}",
                "status": status,
                "total_amount": Decimal("1255000"),
                "delivery_address": "서울시 강남구",
            }
            order = Order(**order_data)
            db_session.add(order)

        # When
        db_session.commit()

        # Then
        orders = db_session.query(Order).all()
        assert len(orders) == len(valid_statuses)
        for order in orders:
            assert order.status in valid_statuses

    def test_order_string_representation(self, created_user, created_plan, created_device, created_number):
        """주문 모델 문자열 표현 테스트"""
        # Given
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

        # When
        str_repr = str(order)

        # Then
        assert "ORD123456789" in str_repr
        assert "PENDING" in str_repr

    def test_order_relationships(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 관계 테스트"""
        # Given
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

        # When & Then
        assert order.user.id == created_user.id
        assert order.plan.id == created_plan.id
        assert order.device.id == created_device.id
        assert order.number.id == created_number.id

    def test_order_status_history_relationship(
        self, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """주문 상태 이력 관계 테스트"""
        # Given
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

        # 상태 이력 추가
        status_history = OrderStatusHistory(
            order_id=order.id, status=OrderStatus.PROCESSING, note="심사 시작", admin_id=created_admin.id
        )
        db_session.add(status_history)
        db_session.commit()

        # When
        order_status_history = order.status_history

        # Then
        assert len(order_status_history) == 1
        assert order_status_history[0].status == OrderStatus.PROCESSING
        assert order_status_history[0].note == "심사 시작"

    def test_order_payment_relationship(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 결제 관계 테스트"""
        # Given
        from app.models.payment import Payment, PaymentStatus

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

        # 결제 정보 추가
        payment = Payment(
            order_id=order.id,
            payment_method="credit_card",
            amount=order.total_amount,
            status=PaymentStatus.COMPLETED,
            transaction_id="TXN123456789",
        )
        db_session.add(payment)
        db_session.commit()

        # When
        order_payment = order.payment

        # Then
        assert order_payment is not None
        assert order_payment.amount == order.total_amount
        assert order_payment.status == PaymentStatus.COMPLETED

    def test_order_is_cancellable_property(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 취소 가능 여부 프로퍼티 테스트"""
        # Given
        cancellable_statuses = [OrderStatus.PENDING, OrderStatus.PROCESSING]
        non_cancellable_statuses = [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.FAILED]

        for i, status in enumerate(cancellable_statuses + non_cancellable_statuses):
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

        orders = db_session.query(Order).all()

        # When & Then
        for order in orders:
            if order.status in cancellable_statuses:
                assert order.is_cancellable is True
            else:
                assert order.is_cancellable is False

    def test_order_is_completed_property(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 완료 여부 프로퍼티 테스트"""
        # Given
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.COMPLETED,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        db_session.add(order)
        db_session.commit()

        # When & Then
        assert order.is_completed is True

    def test_order_processing_time_property(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 처리 시간 프로퍼티 테스트"""
        # Given
        order = Order(
            user_id=created_user.id,
            plan_id=created_plan.id,
            device_id=created_device.id,
            number_id=created_number.id,
            order_number="ORD123456789",
            status=OrderStatus.COMPLETED,
            total_amount=Decimal("1255000"),
            delivery_address="서울시 강남구",
        )
        order.created_at = datetime.now() - timedelta(hours=2)
        order.updated_at = datetime.now()
        db_session.add(order)
        db_session.commit()

        # When
        processing_time = order.processing_time

        # Then
        assert processing_time is not None
        assert processing_time.total_seconds() > 7000  # 약 2시간

    def test_order_generate_order_number(self):
        """주문번호 생성 메서드 테스트"""
        # When
        order_number = Order.generate_order_number()

        # Then
        assert len(order_number) == 12
        assert order_number.startswith("ORD")
        assert order_number[3:].isdigit()

    def test_order_calculate_total_amount(self, created_plan, created_device, created_number):
        """주문 총액 계산 메서드 테스트"""
        # When
        total_amount = Order.calculate_total_amount(
            plan_monthly_fee=created_plan.monthly_fee,
            device_price=created_device.price,
            number_additional_fee=created_number.additional_fee,
            activation_fee=Decimal("10000"),
        )

        # Then
        expected_total = created_plan.monthly_fee + created_device.price + created_number.additional_fee + Decimal("10000")
        assert total_amount == expected_total

    def test_order_update_timestamp(self, db_session, created_user, created_plan, created_device, created_number):
        """주문 수정 시 타임스탬프 업데이트 테스트"""
        # Given
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

        original_updated_at = order.updated_at

        # When
        order.status = OrderStatus.PROCESSING
        db_session.commit()
        db_session.refresh(order)

        # Then
        assert order.updated_at > original_updated_at
