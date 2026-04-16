"""add_signing_tables

Revision ID: signing_tables_001
Revises: b3630857c370
Create Date: 2026-03-13 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'signing_tables_001'
down_revision = 'b3630857c370'
branch_labels = None
depends_on = None

def upgrade() -> None:
    schema_sql = """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    CREATE TABLE IF NOT EXISTS organization_keys (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        organization_id UUID NOT NULL REFERENCES organizations(id),
        public_key_pem TEXT NOT NULL,
        public_key_fingerprint TEXT NOT NULL UNIQUE,
        encrypted_private_key TEXT NOT NULL,
        organization_root_fingerprint TEXT NULL,
        is_active BOOLEAN DEFAULT TRUE,
        retired_at TIMESTAMP WITH TIME ZONE NULL,
        retention_until TIMESTAMP WITH TIME ZONE NULL,
        retention_source TEXT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    DO $$ 
    BEGIN 
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='organization_keys' AND column_name='organization_root_fingerprint') THEN
            ALTER TABLE organization_keys ADD COLUMN organization_root_fingerprint TEXT NULL;
        END IF;
    END $$;

    CREATE TABLE IF NOT EXISTS note_snapshots (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        note_id UUID NOT NULL REFERENCES clinical_notes(id),
        version_id UUID NOT NULL UNIQUE,
        snapshot_json JSONB NOT NULL,
        content_hash TEXT NOT NULL,
        signature TEXT NOT NULL,
        signed_by UUID NOT NULL REFERENCES users(id),
        signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        public_key_fingerprint TEXT NOT NULL,
        previous_snapshot_hash TEXT NULL,
        archival_status TEXT DEFAULT 'ACTIVE',
        legal_hold BOOLEAN DEFAULT FALSE,
        is_immutable BOOLEAN DEFAULT TRUE,
        retention_until TIMESTAMP WITH TIME ZONE NULL,
        retention_source TEXT NULL,
        pdf_path TEXT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS encounter_seals (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        encounter_id UUID NOT NULL REFERENCES encounters(id) UNIQUE,
        aggregate_hash TEXT NOT NULL,
        signature TEXT NOT NULL,
        signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        public_key_fingerprint TEXT NOT NULL,
        seal_payload JSONB NOT NULL,
        is_immutable BOOLEAN DEFAULT TRUE,
        retention_until TIMESTAMP WITH TIME ZONE NULL,
        retention_source TEXT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS idempotency_keys (
        id TEXT PRIMARY KEY,
        response_payload JSONB NOT NULL,
        retention_until TIMESTAMP WITH TIME ZONE NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );

    CREATE TABLE IF NOT EXISTS backup_jobs (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        organization_id UUID NOT NULL REFERENCES organizations(id),
        mode TEXT NOT NULL,
        status TEXT NOT NULL,
        backup_hash TEXT NULL,
        manifest_hash TEXT NULL,
        certification_signature TEXT NULL,
        organization_root_fingerprint TEXT NOT NULL,
        previous_backup_hash TEXT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        completed_at TIMESTAMP WITH TIME ZONE NULL,
        executor_id UUID NOT NULL REFERENCES users(id),
        retention_until TIMESTAMP WITH TIME ZONE NULL,
        retention_source TEXT NULL,
        is_immutable BOOLEAN DEFAULT FALSE,
        legal_hold BOOLEAN DEFAULT FALSE,
        archival_status TEXT DEFAULT 'active'
    );
    """
    op.execute(sa.text(schema_sql))

def downgrade() -> None:
    op.drop_table('backup_jobs')
    op.drop_table('idempotency_keys')
    op.drop_table('encounter_seals')
    op.drop_table('note_snapshots')
    op.drop_table('organization_keys')
