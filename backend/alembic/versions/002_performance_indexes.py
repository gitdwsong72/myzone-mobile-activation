"""Performance optimization: add indexes

Revision ID: 002
Revises: 001
Create Date: 2025-01-12 10:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 성능 최적화를 위한 추가 인덱스 생성
    
    # Users 테이블 인덱스
    op.create_index('idx_users_birth_date', 'users', ['birth_date'])
    op.create_index('idx_users_is_verified', 'users', ['is_verified'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    # Plans 테이블 인덱스
    op.create_index('idx_plans_is_active_category', 'plans', ['is_active', 'category'])
    op.create_index('idx_plans_monthly_fee', 'plans', ['monthly_fee'])
    op.create_index('idx_plans_display_order', 'plans', ['display_order'])
    
    # Devices 테이블 인덱스
    op.create_index('idx_devices_brand_is_active', 'devices', ['brand', 'is_active'])
    op.create_index('idx_devices_price', 'devices', ['price'])
    op.create_index('idx_devices_stock_quantity', 'devices', ['stock_quantity'])
    op.create_index('idx_devices_is_featured', 'devices', ['is_featured'])
    
    # Numbers 테이블 인덱스 (이미 생성된 것 외 추가)
    op.create_index('idx_numbers_is_premium', 'numbers', ['is_premium'])
    op.create_index('idx_numbers_additional_fee', 'numbers', ['additional_fee'])
    
    # Orders 테이블 인덱스
    op.create_index('idx_orders_user_id_status', 'orders', ['user_id', 'status'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    op.create_index('idx_orders_total_amount', 'orders', ['total_amount'])
    op.create_index('idx_orders_plan_id', 'orders', ['plan_id'])
    op.create_index('idx_orders_device_id', 'orders', ['device_id'])
    
    # Payments 테이블 인덱스
    op.create_index('idx_payments_order_id_status', 'payments', ['order_id', 'status'])
    op.create_index('idx_payments_paid_at', 'payments', ['paid_at'])
    op.create_index('idx_payments_payment_method', 'payments', ['payment_method'])
    op.create_index('idx_payments_amount', 'payments', ['amount'])
    
    # Order Status History 테이블 인덱스
    op.create_index('idx_order_status_history_created_at', 'order_status_history', ['created_at'])
    op.create_index('idx_order_status_history_status', 'order_status_history', ['status'])
    op.create_index('idx_order_status_history_admin_id', 'order_status_history', ['admin_id'])
    
    # Admins 테이블 인덱스
    op.create_index('idx_admins_is_active_role', 'admins', ['is_active', 'role'])
    op.create_index('idx_admins_last_login', 'admins', ['last_login'])


def downgrade() -> None:
    # 인덱스 삭제 (역순)
    op.drop_index('idx_admins_last_login', table_name='admins')
    op.drop_index('idx_admins_is_active_role', table_name='admins')
    
    op.drop_index('idx_order_status_history_admin_id', table_name='order_status_history')
    op.drop_index('idx_order_status_history_status', table_name='order_status_history')
    op.drop_index('idx_order_status_history_created_at', table_name='order_status_history')
    
    op.drop_index('idx_payments_amount', table_name='payments')
    op.drop_index('idx_payments_payment_method', table_name='payments')
    op.drop_index('idx_payments_paid_at', table_name='payments')
    op.drop_index('idx_payments_order_id_status', table_name='payments')
    
    op.drop_index('idx_orders_device_id', table_name='orders')
    op.drop_index('idx_orders_plan_id', table_name='orders')
    op.drop_index('idx_orders_total_amount', table_name='orders')
    op.drop_index('idx_orders_created_at', table_name='orders')
    op.drop_index('idx_orders_user_id_status', table_name='orders')
    
    op.drop_index('idx_numbers_additional_fee', table_name='numbers')
    op.drop_index('idx_numbers_is_premium', table_name='numbers')
    
    op.drop_index('idx_devices_is_featured', table_name='devices')
    op.drop_index('idx_devices_stock_quantity', table_name='devices')
    op.drop_index('idx_devices_price', table_name='devices')
    op.drop_index('idx_devices_brand_is_active', table_name='devices')
    
    op.drop_index('idx_plans_display_order', table_name='plans')
    op.drop_index('idx_plans_monthly_fee', table_name='plans')
    op.drop_index('idx_plans_is_active_category', table_name='plans')
    
    op.drop_index('idx_users_created_at', table_name='users')
    op.drop_index('idx_users_is_verified', table_name='users')
    op.drop_index('idx_users_birth_date', table_name='users')