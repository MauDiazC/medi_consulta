"""add_settings_json_to_organizations

Revision ID: org_settings_001
Revises: update_reminders_12h_5m
Create Date: 2026-05-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'org_settings_001'
down_revision = 'rag_001_add_embeddings'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('organizations', sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))

def downgrade() -> None:
    op.drop_column('organizations', 'settings')
