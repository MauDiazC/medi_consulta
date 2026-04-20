"""add user_id to clinical_sessions

Revision ID: sessions_add_user_001
Revises: patients_add_phone_001
Create Date: 2026-04-18 07:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'sessions_add_user_001'
down_revision = 'patients_add_phone_001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('clinical_sessions', sa.Column('user_id', sa.UUID(), nullable=True))
    # We set a default for existing sessions or keep them null if not known
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON clinical_sessions (user_id)")


def downgrade():
    op.drop_column('clinical_sessions', 'user_id')
