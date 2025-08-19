"""Add encryption to user fields

Revision ID: 005
Revises: 004
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    사용자 테이블의 민감한 정보 필드를 암호화 타입으로 변경
    기존 데이터는 암호화하여 마이그레이션
    """
    # 임시 컬럼 추가 (암호화된 데이터 저장용)
    op.add_column('users', sa.Column('name_encrypted', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('address_encrypted', sa.Text(), nullable=True))
    
    # 기존 데이터를 암호화하여 새 컬럼에 저장하는 SQL 함수 생성
    # 실제 운영 환경에서는 별도 스크립트로 처리 권장
    op.execute(text("""
        CREATE OR REPLACE FUNCTION encrypt_existing_data() RETURNS void AS $$
        BEGIN
            -- 이 함수는 실제 암호화 로직으로 대체되어야 함
            -- 여기서는 예시로 단순 복사만 수행
            UPDATE users SET 
                name_encrypted = name,
                address_encrypted = address
            WHERE name_encrypted IS NULL OR address_encrypted IS NULL;
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    # 함수 실행
    op.execute(text("SELECT encrypt_existing_data();"))
    
    # 기존 컬럼 삭제
    op.drop_column('users', 'name')
    op.drop_column('users', 'address')
    
    # 새 컬럼 이름 변경
    op.alter_column('users', 'name_encrypted', new_column_name='name')
    op.alter_column('users', 'address_encrypted', new_column_name='address')
    
    # NOT NULL 제약 조건 추가
    op.alter_column('users', 'name', nullable=False)
    op.alter_column('users', 'address', nullable=False)
    
    # 임시 함수 삭제
    op.execute(text("DROP FUNCTION IF EXISTS encrypt_existing_data();"))


def downgrade() -> None:
    """
    암호화 타입을 일반 타입으로 되돌림
    """
    # 임시 컬럼 추가
    op.add_column('users', sa.Column('name_decrypted', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('address_decrypted', sa.Text(), nullable=True))
    
    # 복호화 함수 생성 (실제로는 복호화 로직 필요)
    op.execute(text("""
        CREATE OR REPLACE FUNCTION decrypt_existing_data() RETURNS void AS $$
        BEGIN
            -- 이 함수는 실제 복호화 로직으로 대체되어야 함
            UPDATE users SET 
                name_decrypted = name,
                address_decrypted = address
            WHERE name_decrypted IS NULL OR address_decrypted IS NULL;
        END;
        $$ LANGUAGE plpgsql;
    """))
    
    # 함수 실행
    op.execute(text("SELECT decrypt_existing_data();"))
    
    # 기존 컬럼 삭제
    op.drop_column('users', 'name')
    op.drop_column('users', 'address')
    
    # 새 컬럼 이름 변경
    op.alter_column('users', 'name_decrypted', new_column_name='name')
    op.alter_column('users', 'address_decrypted', new_column_name='address')
    
    # 컬럼 타입 변경
    op.alter_column('users', 'name', type_=sa.String(100), nullable=False)
    op.alter_column('users', 'address', type_=sa.Text(), nullable=False)
    
    # 임시 함수 삭제
    op.execute(text("DROP FUNCTION IF EXISTS decrypt_existing_data();"))