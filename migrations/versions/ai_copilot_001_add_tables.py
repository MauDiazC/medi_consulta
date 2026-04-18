"""create ai copilot suggestions table

Revision ID: ai_copilot_001_add_tables
Revises: signing_identity_001
Create Date: 2026-04-18 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ai_copilot_001_add_tables'
down_revision = 'signing_identity_001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ai_copilot_suggestions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('note_id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('suggestion_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_copilot_note', 'ai_copilot_suggestions', ['note_id'])


def downgrade():
    op.drop_table('ai_copilot_suggestions')
