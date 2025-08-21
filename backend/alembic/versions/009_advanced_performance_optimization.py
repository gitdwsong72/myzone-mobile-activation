"""Advanced performance optimization: composite indexes and query optimization

Revision ID: 009
Revises: 008
Create Date: 2025-01-18 10:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 복합 인덱스 생성 (자주 함께 사용되는 컬럼들)
    
    # Orders 테이블 - 관리자 대시보드 쿼리 최적화
    op.create_index('idx_orders_status_created_at', 'orders', ['status', 'created_at'])
    op.create_index('idx_orders_user_created_at', 'orders', ['user_id', 'created_at'])
    op.create_index('idx_orders_plan_status', 'orders', ['plan_id', 'status'])
    
    # Numbers 테이블 - 번호 검색 최적화
    op.create_index('idx_numbers_category_status_fee', 'numbers', ['category', 'status', 'additional_fee'])
    op.create_index('idx_numbers_premium_available', 'numbers', ['is_premium', 'status'])
    
    # Devices 테이블 - 상품 목록 조회 최적화
    op.create_index('idx_devices_active_brand_price', 'devices', ['is_active', 'brand', 'price'])
    op.create_index('idx_devices_featured_active', 'devices', ['is_featured', 'is_active', 'display_order'])
    
    # Plans 테이블 - 요금제 목록 최적화
    op.create_index('idx_plans_active_category_order', 'plans', ['is_active', 'category', 'display_order'])
    op.create_index('idx_plans_active_fee', 'plans', ['is_active', 'monthly_fee'])
    
    # Users 테이블 - 사용자 검색 최적화
    op.create_index('idx_users_active_verified', 'users', ['is_active', 'is_verified'])
    
    # Payments 테이블 - 결제 통계 최적화
    op.create_index('idx_payments_status_paid_at', 'payments', ['status', 'paid_at'])
    op.create_index('idx_payments_method_status', 'payments', ['payment_method', 'status'])
    
    # Order Status History - 처리 이력 조회 최적화
    op.create_index('idx_order_history_order_created', 'order_status_history', ['order_id', 'created_at'])
    
    # 부분 인덱스 생성 (PostgreSQL 전용)
    # 활성 상태인 데이터만 인덱싱하여 성능 향상
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_plans_active_only 
        ON plans (category, monthly_fee, display_order) 
        WHERE is_active = true
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_devices_available_only 
        ON devices (brand, price, display_order) 
        WHERE is_active = true AND stock_quantity > 0
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_numbers_available_only 
        ON numbers (category, additional_fee, number) 
        WHERE status = 'available'
    """)
    
    # 함수 기반 인덱스 (검색 성능 향상)
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_numbers_last_four_digits 
        ON numbers (RIGHT(number, 4))
    """)
    
    op.execute("""
        CREATE INDEX CONCURRENTLY idx_orders_date_only 
        ON orders (DATE(created_at))
    """)


def downgrade() -> None:
    # 함수 기반 인덱스 삭제
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_orders_date_only")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_numbers_last_four_digits")
    
    # 부분 인덱스 삭제
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_numbers_available_only")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_devices_available_only")
    op.execute("DROP INDEX CONCURRENTLY IF EXISTS idx_plans_active_only")
    
    # 복합 인덱스 삭제
    op.drop_index('idx_order_history_order_created', table_name='order_status_history')
    op.drop_index('idx_payments_method_status', table_name='payments')
    op.drop_index('idx_payments_status_paid_at', table_name='payments')
    op.drop_index('idx_users_active_verified', table_name='users')
    op.drop_index('idx_plans_active_fee', table_name='plans')
    op.drop_index('idx_plans_active_category_order', table_name='plans')
    op.drop_index('idx_devices_featured_active', table_name='devices')
    op.drop_index('idx_devices_active_brand_price', table_name='devices')
    op.drop_index('idx_numbers_premium_available', table_name='numbers')
    op.drop_index('idx_numbers_category_status_fee', table_name='numbers')
    op.drop_index('idx_orders_plan_status', table_name='orders')
    op.drop_index('idx_orders_user_created_at', table_name='orders')
    op.drop_index('idx_orders_status_created_at', table_name='orders')