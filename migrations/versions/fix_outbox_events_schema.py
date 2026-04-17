"""fix_outbox_events_schema

Revision ID: fix_outbox_001
Revises: patients_unify_status
Create Date: 2026-04-17 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_outbox_001'
down_revision = 'patients_unify_status'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add missing institutional columns to outbox_events
    op.add_column('outbox_events', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('outbox_events', sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True))
    op.add_column('outbox_events', sa.Column('archival_status', sa.String(), server_default='active', nullable=False))
    op.add_column('outbox_events', sa.Column('legal_hold', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('outbox_events', sa.Column('is_immutable', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('outbox_events', sa.Column('retention_source', sa.String(), nullable=True))
    
    # Switch ID to UUID for better SaaS scaling (optional but recommended for consistency)
    # Keeping bigserial for now to avoid breaking FKs if any, but adding columns above is mandatory.

def downgrade() -> None:
    op.drop_column('outbox_events', 'retention_source')
    op.drop_column('outbox_events', 'is_immutable')
    op.drop_column('outbox_events', 'legal_hold')
    op.drop_column('outbox_events', 'archival_status')
    op.drop_column('outbox_events', 'retention_until')
    op.drop_column('outbox_events', 'processed_at')
