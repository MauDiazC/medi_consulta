"""fix_signing_columns

Revision ID: signing_tables_fix
Revises: signing_tables_001
Create Date: 2026-03-14 01:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'signing_tables_fix'
down_revision = 'signing_tables_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Safe addition of missing column
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='organization_root_fingerprint') THEN
                ALTER TABLE organization_keys ADD COLUMN organization_root_fingerprint TEXT NULL;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    op.drop_column('organization_keys', 'organization_root_fingerprint')
