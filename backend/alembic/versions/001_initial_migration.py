"""Initial migration: create all tables

Revision ID: 001
Revises: 
Create Date: 2025-01-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='사용자 이름'),
        sa.Column('phone', sa.String(length=20), nullable=False, comment='휴대폰 번호'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='이메일 주소'),
        sa.Column('birth_date', sa.Date(), nullable=False, comment='생년월일'),
        sa.Column('gender', sa.String(length=10), nullable=False, comment='성별'),
        sa.Column('address', sa.Text(), nullable=False, comment='주소'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, comment='본인인증 완료 여부'),
        sa.Column('verification_method', sa.String(length=50), nullable=True, comment='인증 방법'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create plans table
    op.create_table('plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='요금제 이름'),
        sa.Column('description', sa.Text(), nullable=True, comment='요금제 설명'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='카테고리 (5G, LTE, 데이터중심, 통화중심)'),
        sa.Column('monthly_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='월 요금'),
        sa.Column('setup_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='개통비'),
        sa.Column('data_limit', sa.Integer(), nullable=True, comment='데이터 제공량 (MB, NULL=무제한)'),
        sa.Column('call_minutes', sa.Integer(), nullable=True, comment='통화 시간 (분, NULL=무제한)'),
        sa.Column('sms_count', sa.Integer(), nullable=True, comment='문자 개수 (개, NULL=무제한)'),
        sa.Column('additional_services', sa.Text(), nullable=True, comment='부가 서비스 목록 (JSON)'),
        sa.Column('discount_rate', sa.Numeric(precision=5, scale=2), nullable=False, comment='할인율 (%)'),
        sa.Column('promotion_text', sa.String(length=200), nullable=True, comment='프로모션 문구'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='활성화 상태'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='표시 순서'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plans_id'), 'plans', ['id'], unique=False)
    op.create_index(op.f('ix_plans_category'), 'plans', ['category'], unique=False)

    # Create devices table
    op.create_table('devices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=False, comment='브랜드 (삼성, 애플, LG 등)'),
        sa.Column('model', sa.String(length=100), nullable=False, comment='모델명'),
        sa.Column('color', sa.String(length=50), nullable=False, comment='색상'),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False, comment='단말기 가격'),
        sa.Column('discount_price', sa.Numeric(precision=10, scale=2), nullable=True, comment='할인 가격'),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, comment='재고 수량'),
        sa.Column('specifications', sa.JSON(), nullable=True, comment='상세 스펙 (JSON)'),
        sa.Column('description', sa.Text(), nullable=True, comment='상품 설명'),
        sa.Column('image_url', sa.String(length=500), nullable=True, comment='대표 이미지 URL'),
        sa.Column('image_urls', sa.JSON(), nullable=True, comment='추가 이미지 URL 목록 (JSON)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='판매 활성화 상태'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, comment='추천 상품 여부'),
        sa.Column('display_order', sa.Integer(), nullable=False, comment='표시 순서'),
        sa.Column('release_date', sa.String(length=20), nullable=True, comment='출시일'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_id'), 'devices', ['id'], unique=False)
    op.create_index(op.f('ix_devices_brand'), 'devices', ['brand'], unique=False)

    # Create admins table
    op.create_table('admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False, comment='관리자 아이디'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='이메일'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='해시된 비밀번호'),
        sa.Column('role', sa.String(length=50), nullable=False, comment='역할 (admin, super_admin, operator)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='활성화 상태'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, comment='슈퍼유저 여부'),
        sa.Column('last_login', sa.DateTime(), nullable=True, comment='마지막 로그인 시간'),
        sa.Column('login_count', sa.String(length=10), nullable=False, comment='로그인 횟수'),
        sa.Column('full_name', sa.String(length=100), nullable=True, comment='실명'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='부서'),
        sa.Column('phone', sa.String(length=20), nullable=True, comment='연락처'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admins_id'), 'admins', ['id'], unique=False)
    op.create_index(op.f('ix_admins_username'), 'admins', ['username'], unique=True)

    # Create numbers table
    op.create_table('numbers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('number', sa.String(length=20), nullable=False, comment='전화번호'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='번호 카테고리 (일반, 연속, 특별)'),
        sa.Column('additional_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='번호 추가 요금'),
        sa.Column('status', sa.String(length=20), nullable=False, comment='상태 (available, reserved, assigned)'),
        sa.Column('reserved_until', sa.DateTime(), nullable=True, comment='예약 만료 시간'),
        sa.Column('reserved_by_order_id', sa.String(length=50), nullable=True, comment='예약한 주문 ID'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, comment='프리미엄 번호 여부'),
        sa.Column('pattern_type', sa.String(length=50), nullable=True, comment='패턴 유형 (연속, 반복, 대칭 등)'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_numbers_id'), 'numbers', ['id'], unique=False)
    op.create_index(op.f('ix_numbers_number'), 'numbers', ['number'], unique=True)
    op.create_index(op.f('ix_numbers_category'), 'numbers', ['category'], unique=False)
    op.create_index(op.f('ix_numbers_status'), 'numbers', ['status'], unique=False)
    op.create_index('idx_number_status_category', 'numbers', ['status', 'category'], unique=False)
    op.create_index('idx_number_reserved_until', 'numbers', ['reserved_until'], unique=False)

    # Create orders table
    op.create_table('orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_number', sa.String(length=50), nullable=False, comment='주문번호'),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
        sa.Column('plan_id', sa.Integer(), nullable=False, comment='요금제 ID'),
        sa.Column('device_id', sa.Integer(), nullable=True, comment='단말기 ID'),
        sa.Column('number_id', sa.Integer(), nullable=True, comment='번호 ID'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='주문 상태 (pending, confirmed, processing, completed, cancelled)'),
        sa.Column('total_amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='총 주문 금액'),
        sa.Column('plan_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='요금제 비용'),
        sa.Column('device_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='단말기 비용'),
        sa.Column('setup_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='개통비'),
        sa.Column('number_fee', sa.Numeric(precision=10, scale=2), nullable=False, comment='번호 추가 요금'),
        sa.Column('delivery_address', sa.Text(), nullable=True, comment='배송 주소'),
        sa.Column('delivery_request', sa.Text(), nullable=True, comment='배송 요청사항'),
        sa.Column('preferred_delivery_time', sa.String(length=50), nullable=True, comment='희망 배송 시간'),
        sa.Column('terms_agreed', sa.Boolean(), nullable=False, comment='약관 동의 여부'),
        sa.Column('privacy_agreed', sa.Boolean(), nullable=False, comment='개인정보 처리 동의'),
        sa.Column('marketing_agreed', sa.Boolean(), nullable=False, comment='마케팅 수신 동의'),
        sa.Column('notes', sa.Text(), nullable=True, comment='주문 메모'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ),
        sa.ForeignKeyConstraint(['number_id'], ['numbers.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)

    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False, comment='주문 ID'),
        sa.Column('payment_method', sa.String(length=50), nullable=False, comment='결제 방법 (card, bank_transfer, simple_pay)'),
        sa.Column('payment_provider', sa.String(length=50), nullable=True, comment='결제 제공업체 (kakao_pay, naver_pay 등)'),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='결제 금액'),
        sa.Column('currency', sa.String(length=10), nullable=False, comment='통화'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='결제 상태 (pending, processing, completed, failed, cancelled, refunded)'),
        sa.Column('transaction_id', sa.String(length=100), nullable=True, comment='PG사 거래 ID'),
        sa.Column('pg_provider', sa.String(length=50), nullable=True, comment='PG사 (toss, iamport 등)'),
        sa.Column('pg_transaction_id', sa.String(length=100), nullable=True, comment='PG사 내부 거래 ID'),
        sa.Column('card_company', sa.String(length=50), nullable=True, comment='카드사'),
        sa.Column('card_number_masked', sa.String(length=20), nullable=True, comment='마스킹된 카드번호'),
        sa.Column('installment_months', sa.Integer(), nullable=False, comment='할부 개월수 (0=일시불)'),
        sa.Column('paid_at', sa.DateTime(), nullable=True, comment='결제 완료 시간'),
        sa.Column('failed_at', sa.DateTime(), nullable=True, comment='결제 실패 시간'),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True, comment='결제 취소 시간'),
        sa.Column('failure_reason', sa.Text(), nullable=True, comment='결제 실패 사유'),
        sa.Column('cancel_reason', sa.Text(), nullable=True, comment='결제 취소 사유'),
        sa.Column('refund_amount', sa.Numeric(precision=12, scale=2), nullable=False, comment='환불 금액'),
        sa.Column('refund_reason', sa.Text(), nullable=True, comment='환불 사유'),
        sa.Column('refunded_at', sa.DateTime(), nullable=True, comment='환불 완료 시간'),
        sa.Column('receipt_url', sa.String(length=500), nullable=True, comment='영수증 URL'),
        sa.Column('notes', sa.Text(), nullable=True, comment='결제 메모'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)
    op.create_index(op.f('ix_payments_transaction_id'), 'payments', ['transaction_id'], unique=True)

    # Create order_status_history table
    op.create_table('order_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False, comment='주문 ID'),
        sa.Column('status', sa.String(length=50), nullable=False, comment='변경된 상태'),
        sa.Column('previous_status', sa.String(length=50), nullable=True, comment='이전 상태'),
        sa.Column('admin_id', sa.Integer(), nullable=True, comment='처리한 관리자 ID'),
        sa.Column('note', sa.Text(), nullable=True, comment='상태 변경 메모'),
        sa.Column('is_automatic', sa.String(length=10), nullable=False, comment='자동 처리 여부'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['admin_id'], ['admins.id'], ),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_order_status_history_id'), 'order_status_history', ['id'], unique=False)
    op.create_index(op.f('ix_order_status_history_order_id'), 'order_status_history', ['order_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('order_status_history')
    op.drop_table('payments')
    op.drop_table('orders')
    op.drop_table('numbers')
    op.drop_table('admins')
    op.drop_table('devices')
    op.drop_table('plans')
    op.drop_table('users')