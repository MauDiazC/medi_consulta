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
    # Safe addition of missing columns across all infrastructure tables
    op.execute("""
        DO $$ 
        BEGIN 
            -- Fix organization_keys
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

            -- Fix idempotency_keys
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='idempotency_keys' AND column_name='archival_status') THEN
                ALTER TABLE idempotency_keys ADD COLUMN archival_status TEXT DEFAULT 'active' NOT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='idempotency_keys' AND column_name='legal_hold') THEN
                ALTER TABLE idempotency_keys ADD COLUMN legal_hold BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='idempotency_keys' AND column_name='is_immutable') THEN
                ALTER TABLE idempotency_keys ADD COLUMN is_immutable BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;

            -- Fix clinical_audit_log
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clinical_audit_log' AND column_name='entry_hash') THEN
                ALTER TABLE clinical_audit_log ADD COLUMN entry_hash TEXT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clinical_audit_log' AND column_name='archival_status') THEN
                ALTER TABLE clinical_audit_log ADD COLUMN archival_status TEXT DEFAULT 'active' NOT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clinical_audit_log' AND column_name='legal_hold') THEN
                ALTER TABLE clinical_audit_log ADD COLUMN legal_hold BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='clinical_audit_log' AND column_name='is_immutable') THEN
                ALTER TABLE clinical_audit_log ADD COLUMN is_immutable BOOLEAN DEFAULT FALSE NOT NULL;
            END IF;
        END $$;
    """)

def downgrade() -> None:
    pass
