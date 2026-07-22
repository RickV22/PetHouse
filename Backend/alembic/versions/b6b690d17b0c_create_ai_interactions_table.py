"""create ai_interactions table

Revision ID: b6b690d17b0c
Revises: 
Create Date: 2026-07-21 01:20:53.074787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b6b690d17b0c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('ai_interactions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('question', sa.Text(), nullable=False),
    sa.Column('generated_sql', sa.Text(), nullable=True),
    sa.Column('execution_ms', sa.Integer(), nullable=True),
    sa.Column('response', sa.Text(), nullable=True),
    sa.Column('provider', sa.String(length=50), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_interactions_user_id'), 'ai_interactions', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_interactions_user_id'), table_name='ai_interactions')
    op.drop_table('ai_interactions')
