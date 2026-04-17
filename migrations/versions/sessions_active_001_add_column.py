"""add_is_active_to_clinical_sessions

Revision ID: sessions_active_001
Revises: fix_outbox_uuid_001
Create Date: 2026-04-17 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'sessions_active_001'
down_revision = 'fix_outbox_uuid_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add is_active column to clinical_sessions with default true
    op.add_column('clinical_sessions', sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    
def downgrade() -> None:
    op.drop_column('clinical_sessions', 'is_active')
