"""add closed_at to clinical_sessions

Revision ID: sessions_closed_at_001
Revises: update_reminders_12h_5m
Create Date: 2026-05-06 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'sessions_closed_at_001'
down_revision = 'encounters_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('clinical_sessions', sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True))
    
def downgrade() -> None:
    op.drop_column('clinical_sessions', 'closed_at')
