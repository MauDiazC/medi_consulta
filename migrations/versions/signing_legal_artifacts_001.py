"""add legal artifact columns to signing tables

Revision ID: signing_legal_artifacts_001
Revises: ai_copilot_001_add_tables
Create Date: 2026-04-18 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'signing_legal_artifacts_001'
down_revision = 'ai_copilot_001_add_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Tables to update
    tables = ['note_snapshots', 'encounter_seals', 'organization_keys', 'backup_jobs']
    
    for table in tables:
        # Add columns if they don't exist (safety first)
        op.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='retention_until') THEN
                    ALTER TABLE {table} ADD COLUMN retention_until TIMESTAMP WITH TIME ZONE;
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='archival_status') THEN
                    ALTER TABLE {table} ADD COLUMN archival_status VARCHAR(20) DEFAULT 'active' NOT NULL;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='legal_hold') THEN
                    ALTER TABLE {table} ADD COLUMN legal_hold BOOLEAN DEFAULT false NOT NULL;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='is_immutable') THEN
                    ALTER TABLE {table} ADD COLUMN is_immutable BOOLEAN DEFAULT false NOT NULL;
                END IF;

                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='{table}' AND column_name='retention_source') THEN
                    ALTER TABLE {table} ADD COLUMN retention_source VARCHAR(100);
                END IF;
            END $$;
        """)
        
        # Create index for retention
        op.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_retention ON {table} (retention_until)")


def downgrade():
    tables = ['note_snapshots', 'encounter_seals', 'organization_keys', 'backup_jobs']
    for table in tables:
        op.drop_column(table, 'retention_until')
        op.drop_column(table, 'archival_status')
        op.drop_column(table, 'legal_hold')
        op.drop_column(table, 'is_immutable')
        op.drop_column(table, 'retention_source')
