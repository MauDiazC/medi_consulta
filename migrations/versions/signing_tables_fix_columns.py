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
    # Safe addition of missing columns from ImmutableLegalArtifact and root fingerprint
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='organization_root_fingerprint') THEN
                ALTER TABLE organization_keys ADD COLUMN organization_root_fingerprint TEXT NULL;
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='archival_status') THEN
                ALTER TABLE organization_keys ADD COLUMN archival_status TEXT DEFAULT 'active' NOT NULL;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='legal_hold') THEN
                ALTER TABLE organization_keys ADD COLUMN legal_hold BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='is_immutable') THEN
                ALTER TABLE organization_keys ADD COLUMN is_immutable BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='retention_until') THEN
                ALTER TABLE organization_keys ADD COLUMN retention_until TIMESTAMP WITH TIME ZONE NULL;
            END IF;

            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='retention_source') THEN
                ALTER TABLE organization_keys ADD COLUMN retention_source TEXT NULL;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    pass
