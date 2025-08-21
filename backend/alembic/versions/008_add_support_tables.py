"""add support tables

Revision ID: 008
Revises: 007
Create Date: 2024-01-18 10:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade():
    # FAQ 테이블 생성
    op.create_table('faqs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False, comment='카테고리'),
        sa.Column('question', sa.Text(), nullable=False, comment='질문'),
        sa.Column('answer', sa.Text(), nullable=False, comment='답변'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='활성화 여부'),
        sa.Column('view_count', sa.Integer(), nullable=True, comment='조회수'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_faqs_id'), 'faqs', ['id'], unique=False)
    op.create_index(op.f('ix_faqs_category'), 'faqs', ['category'], unique=False)

    # 1:1 문의 테이블 생성
    op.create_table('inquiries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, comment='문의자 이름'),
        sa.Column('email', sa.String(length=255), nullable=False, comment='이메일'),
        sa.Column('phone', sa.String(length=20), nullable=True, comment='연락처'),
        sa.Column('order_number', sa.String(length=50), nullable=True, comment='신청번호'),
        sa.Column('category', sa.String(length=50), nullable=False, comment='문의 유형'),
        sa.Column('subject', sa.String(length=200), nullable=False, comment='제목'),
        sa.Column('content', sa.Text(), nullable=False, comment='문의 내용'),
        sa.Column('status', sa.String(length=20), nullable=True, comment='처리 상태'),
        sa.Column('admin_reply', sa.Text(), nullable=True, comment='관리자 답변'),
        sa.Column('replied_at', sa.DateTime(timezone=True), nullable=True, comment='답변 일시'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inquiries_id'), 'inquiries', ['id'], unique=False)

    # 기본 FAQ 데이터 삽입
    op.execute("""
        INSERT INTO faqs (category, question, answer, is_active, view_count) VALUES
        ('요금제', '5G 요금제와 LTE 요금제의 차이점은 무엇인가요?', '5G 요금제는 더 빠른 데이터 속도와 낮은 지연시간을 제공합니다. 5G 네트워크가 구축된 지역에서 5G 단말기를 사용하시면 최대 20배 빠른 속도를 경험하실 수 있습니다.', true, 0),
        ('요금제', '요금제 변경은 언제 가능한가요?', '요금제 변경은 매월 1일부터 말일까지 언제든지 가능합니다. 변경된 요금제는 다음 달 1일부터 적용됩니다.', true, 0),
        ('개통절차', '개통까지 얼마나 걸리나요?', '온라인 신청 후 본인인증과 결제가 완료되면 1-2 영업일 내에 개통됩니다. 단말기 배송이 필요한 경우 배송 기간이 추가로 소요됩니다.', true, 0),
        ('개통절차', '본인인증은 어떻게 하나요?', '휴대폰 SMS 인증, 공인인증서, 간편인증(카카오, 네이버) 중 하나를 선택하여 본인인증을 진행하실 수 있습니다.', true, 0),
        ('결제', '어떤 결제 방법을 사용할 수 있나요?', '신용카드, 체크카드, 계좌이체, 간편결제(카카오페이, 네이버페이)를 지원합니다. 단말기 구매 시 할부 결제도 가능합니다.', true, 0),
        ('결제', '결제 실패 시 어떻게 해야 하나요?', '결제 실패 시 다른 결제 방법을 선택하거나 카드사에 문의하여 결제 한도를 확인해 주세요. 문제가 지속되면 고객센터로 연락해 주시기 바랍니다.', true, 0),
        ('배송', '단말기 배송은 얼마나 걸리나요?', '재고가 있는 단말기는 결제 완료 후 1-2일 내에 발송되며, 배송까지는 2-3일 정도 소요됩니다. 품절 상품은 입고 후 순차 발송됩니다.', true, 0),
        ('배송', '배송지 변경이 가능한가요?', '발송 전까지는 배송지 변경이 가능합니다. 이미 발송된 경우에는 택배사를 통해 배송지 변경을 요청해 주세요.', true, 0),
        ('단말기', '단말기 색상 변경이 가능한가요?', '결제 완료 전까지는 색상 변경이 가능합니다. 결제 완료 후에는 취소 후 재주문해야 합니다.', true, 0),
        ('번호', '원하는 번호를 선택할 수 있나요?', '네, 일반번호, 연속번호, 특별번호 중에서 선택하실 수 있습니다. 단, 이미 사용 중인 번호는 선택할 수 없습니다.', true, 0)
    """)


def downgrade():
    op.drop_index(op.f('ix_inquiries_id'), table_name='inquiries')
    op.drop_table('inquiries')
    op.drop_index(op.f('ix_faqs_category'), table_name='faqs')
    op.drop_index(op.f('ix_faqs_id'), table_name='faqs')
    op.drop_table('faqs')