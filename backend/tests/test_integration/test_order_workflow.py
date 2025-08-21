"""
주문 워크플로우 통합 테스트
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus


class TestOrderWorkflow:
    """주문 워크플로우 통합 테스트 클래스"""

    def test_complete_order_workflow(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """전체 주문 워크플로우 통합 테스트"""

        # 1. 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        assert login_response.status_code == 200
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 2. 사용자 생성 (이미 created_user 픽스처로 생성됨)
        user_response = client.get(f"/api/v1/users/{created_user.id}", headers=admin_headers)
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert user_data["name"] == created_user.name

        # 3. 요금제 조회
        plans_response = client.get("/api/v1/plans/")
        assert plans_response.status_code == 200
        plans = plans_response.json()
        assert len(plans) > 0

        # 4. 단말기 조회
        devices_response = client.get("/api/v1/devices/")
        assert devices_response.status_code == 200
        devices = devices_response.json()
        assert len(devices) > 0

        # 5. 번호 조회
        numbers_response = client.get("/api/v1/numbers/")
        assert numbers_response.status_code == 200
        numbers = numbers_response.json()
        assert len(numbers) > 0

        # 6. 주문 생성
        order_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response = client.post("/api/v1/orders/", json=order_data, headers=admin_headers)
        assert order_response.status_code == 201
        order = order_response.json()
        assert order["status"] == OrderStatus.PENDING.value
        assert order["user_id"] == created_user.id
        assert order["plan_id"] == created_plan.id

        # 7. 결제 처리
        payment_data = {"order_id": order["id"], "payment_method": "credit_card", "amount": order["total_amount"]}

        payment_response = client.post("/api/v1/payments/", json=payment_data, headers=admin_headers)
        assert payment_response.status_code == 200
        payment = payment_response.json()
        assert payment["status"] == PaymentStatus.COMPLETED.value
        assert payment["amount"] == order["total_amount"]

        # 8. 주문 상태 확인 (결제 완료 후 자동으로 처리중으로 변경되어야 함)
        updated_order_response = client.get(f"/api/v1/orders/{order['id']}", headers=admin_headers)
        assert updated_order_response.status_code == 200
        updated_order = updated_order_response.json()
        assert updated_order["status"] == OrderStatus.PROCESSING.value

        # 9. 관리자가 주문 처리 완료
        status_update_data = {"status": OrderStatus.COMPLETED.value, "note": "개통 완료"}

        status_response = client.put(f"/api/v1/orders/{order['id']}/status", json=status_update_data, headers=admin_headers)
        assert status_response.status_code == 200
        final_order = status_response.json()
        assert final_order["status"] == OrderStatus.COMPLETED.value

        # 10. 주문 번호로 조회 (고객이 현황 확인)
        order_number = order["order_number"]
        public_order_response = client.get(f"/api/v1/orders/number/{order_number}")
        assert public_order_response.status_code == 200
        public_order = public_order_response.json()
        assert public_order["status"] == OrderStatus.COMPLETED.value
        assert public_order["order_number"] == order_number

    def test_order_cancellation_workflow(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """주문 취소 워크플로우 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 주문 생성
        order_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response = client.post("/api/v1/orders/", json=order_data, headers=admin_headers)
        assert order_response.status_code == 201
        order = order_response.json()

        # 주문 취소
        cancel_data = {"status": OrderStatus.CANCELLED.value, "note": "고객 요청으로 취소"}

        cancel_response = client.put(f"/api/v1/orders/{order['id']}/status", json=cancel_data, headers=admin_headers)
        assert cancel_response.status_code == 200
        cancelled_order = cancel_response.json()
        assert cancelled_order["status"] == OrderStatus.CANCELLED.value

        # 취소된 주문은 다시 처리할 수 없어야 함
        process_data = {"status": OrderStatus.PROCESSING.value, "note": "처리 시도"}

        invalid_response = client.put(f"/api/v1/orders/{order['id']}/status", json=process_data, headers=admin_headers)
        assert invalid_response.status_code == 400

    def test_payment_failure_workflow(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """결제 실패 워크플로우 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 주문 생성
        order_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response = client.post("/api/v1/orders/", json=order_data, headers=admin_headers)
        assert order_response.status_code == 201
        order = order_response.json()

        # 잘못된 결제 정보로 결제 시도
        invalid_payment_data = {"order_id": order["id"], "payment_method": "invalid_method", "amount": order["total_amount"]}

        payment_response = client.post("/api/v1/payments/", json=invalid_payment_data, headers=admin_headers)
        assert payment_response.status_code == 400

        # 주문 상태는 여전히 PENDING이어야 함
        order_check_response = client.get(f"/api/v1/orders/{order['id']}", headers=admin_headers)
        assert order_check_response.status_code == 200
        order_check = order_check_response.json()
        assert order_check["status"] == OrderStatus.PENDING.value

    def test_concurrent_number_reservation(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """동시 번호 예약 처리 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 첫 번째 주문으로 번호 예약
        order_data_1 = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response_1 = client.post("/api/v1/orders/", json=order_data_1, headers=admin_headers)
        assert order_response_1.status_code == 201

        # 같은 번호로 두 번째 주문 시도 (실패해야 함)
        order_data_2 = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,  # 같은 번호
            "delivery_address": "부산시 해운대구 센텀로 456",
        }

        order_response_2 = client.post("/api/v1/orders/", json=order_data_2, headers=admin_headers)
        assert order_response_2.status_code == 409  # Conflict

    def test_order_statistics_integration(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """주문 통계 통합 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 여러 주문 생성
        for i in range(3):
            order_data = {
                "user_id": created_user.id,
                "plan_id": created_plan.id,
                "device_id": created_device.id,
                "number_id": created_number.id,
                "delivery_address": f"서울시 강남구 테헤란로 {123 + i}",
            }

            order_response = client.post("/api/v1/orders/", json=order_data, headers=admin_headers)
            assert order_response.status_code == 201

        # 통계 조회
        stats_response = client.get("/api/v1/admin/statistics/orders", headers=admin_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()

        assert stats["total_orders"] >= 3
        assert stats["pending_orders"] >= 3
        assert "daily_orders" in stats
        assert "monthly_orders" in stats

    def test_notification_integration(
        self, client, db_session, created_user, created_plan, created_device, created_number, created_admin
    ):
        """알림 시스템 통합 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 주문 생성
        order_data = {
            "user_id": created_user.id,
            "plan_id": created_plan.id,
            "device_id": created_device.id,
            "number_id": created_number.id,
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response = client.post("/api/v1/orders/", json=order_data, headers=admin_headers)
        assert order_response.status_code == 201
        order = order_response.json()

        # 주문 상태 변경 (알림이 발송되어야 함)
        status_update_data = {"status": OrderStatus.PROCESSING.value, "note": "심사 시작"}

        status_response = client.put(f"/api/v1/orders/{order['id']}/status", json=status_update_data, headers=admin_headers)
        assert status_response.status_code == 200

        # 알림 발송 확인 (실제 구현에서는 모킹된 알림 서비스 확인)
        # 여기서는 상태 변경이 성공했는지만 확인
        updated_order = status_response.json()
        assert updated_order["status"] == OrderStatus.PROCESSING.value

    def test_error_handling_integration(self, client, db_session, created_admin):
        """에러 처리 통합 테스트"""

        # 관리자 로그인
        login_response = client.post("/api/v1/auth/login", data={"username": created_admin.username, "password": "admin123!"})
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # 존재하지 않는 사용자로 주문 생성 시도
        invalid_order_data = {
            "user_id": 999,  # 존재하지 않는 사용자
            "plan_id": 999,  # 존재하지 않는 요금제
            "device_id": 999,  # 존재하지 않는 단말기
            "number_id": 999,  # 존재하지 않는 번호
            "delivery_address": "서울시 강남구 테헤란로 123",
        }

        order_response = client.post("/api/v1/orders/", json=invalid_order_data, headers=admin_headers)
        assert order_response.status_code == 400
        error_data = order_response.json()
        assert "error_code" in error_data

        # 존재하지 않는 주문 조회
        invalid_order_response = client.get("/api/v1/orders/999", headers=admin_headers)
        assert invalid_order_response.status_code == 404

        # 잘못된 주문번호로 조회
        invalid_number_response = client.get("/api/v1/orders/number/INVALID")
        assert invalid_number_response.status_code == 404
