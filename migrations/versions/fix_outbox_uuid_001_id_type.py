"""convert_outbox_id_to_uuid

Revision ID: fix_outbox_uuid_001
Revises: fix_outbox_001
Create Date: 2026-04-17 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_outbox_uuid_001'
down_revision = 'fix_outbox_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Drop existing primary key constraint
    op.execute("ALTER TABLE outbox_events DROP CONSTRAINT outbox_events_pkey")
    
    # 2. Rename old id and create new uuid id
    op.execute("ALTER TABLE outbox_events RENAME COLUMN id TO old_id")
    op.add_column('outbox_events', sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False))
    
    # 3. Set the new primary key
    op.execute("ALTER TABLE outbox_events ADD PRIMARY KEY (id)")
    
    # 4. Drop the old id column
    op.drop_column('outbox_events', 'old_id')

def downgrade() -> None:
    # This is a destructive migration, downgrade would be complex. 
    # For now, we keep it simple as it's a fix for a broken table.
    pass
