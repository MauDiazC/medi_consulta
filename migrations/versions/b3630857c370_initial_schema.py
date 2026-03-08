"""initial_schema

Revision ID: b3630857c370
Revises: 
Create Date: 2026-03-08 16:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3630857c370'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # 2. Main Tables (Using raw SQL from your source of truth for the baseline)
    schema_sql = """
    create table organizations (
        id uuid primary key default uuid_generate_v4(),
        name text not null,
        plan_code text null, 
        active boolean not null default true,
        created_at timestamp with time zone default now()
    );

    create table users (
        id uuid primary key default uuid_generate_v4(),
        organization_id uuid references organizations(id),
        email text unique not null,
        full_name text not null,
        role text not null default 'doctor',
        password_hash text null,
        active boolean not null default true,
        created_at timestamp with time zone default now()
    );

    create table patients (
        id uuid primary key default uuid_generate_v4(),
        organization_id uuid references organizations(id),
        first_name text not null,
        last_name text not null,
        email text null,
        birth_date date null,
        sex text null,
        is_active boolean not null default true,
        created_at timestamp with time zone default now()
    );

    create table clinical_sessions (
        id uuid primary key default uuid_generate_v4(),
        organization_id uuid references organizations(id),
        name text not null,
        created_at timestamp with time zone default now()
    );

    create table encounters (
        id uuid primary key default uuid_generate_v4(),
        organization_id uuid references organizations(id),
        patient_id uuid references patients(id),
        doctor_id uuid references users(id),
        clinical_session_id uuid references clinical_sessions(id),
        reason text null,
        status text not null default 'open',
        created_at timestamp with time zone default now()
    );

    create table clinical_notes (
        id uuid primary key default uuid_generate_v4(),
        encounter_id uuid references encounters(id),
        created_by uuid references users(id),
        version integer not null default 1,
        is_active_draft boolean not null default true,
        subjective text null,
        objective text null,
        assessment text null,
        plan text null,
        signed_at timestamp with time zone null,
        updated_at timestamp with time zone default now(),
        created_at timestamp with time zone default now()
    );

    create table clinical_audit_log (
        id bigserial primary key,
        entity text not null,
        entity_id text not null,
        action text not null,
        performed_by uuid references users(id),
        metadata jsonb not null default '{}',
        previous_hash text null,
        entry_hash text not null,
        created_at timestamp with time zone default now()
    );

    create table outbox_events (
        id bigserial primary key,
        event_type text not null,
        payload jsonb not null,
        processed boolean not null default false,
        created_at timestamp with time zone default now()
    );

    create table clinical_snapshots (
        id uuid primary key default uuid_generate_v4(),
        note_id uuid references clinical_notes(id),
        encounter_id uuid references encounters(id),
        organization_id uuid references organizations(id),
        content_hash text not null,
        canonical_content jsonb not null,
        signature text not null,
        signed_by uuid references users(id),
        version_num INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active',
        legal_hold BOOLEAN DEFAULT FALSE,
        is_immutable BOOLEAN DEFAULT FALSE,
        retention_source TEXT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed
    ON outbox_events(processed)
    WHERE processed = FALSE;
    """
    
    # Execute split statements
    for stmt in schema_sql.split(';'):
        if stmt.strip():
            op.execute(sa.text(stmt))


def downgrade() -> None:
    op.drop_table('clinical_snapshots')
    op.drop_table('outbox_events')
    op.drop_table('clinical_audit_log')
    op.drop_table('clinical_notes')
    op.drop_table('encounters')
    op.drop_table('clinical_sessions')
    op.drop_table('patients')
    op.drop_table('users')
    op.drop_table('organizations')
