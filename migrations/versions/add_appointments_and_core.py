"""add appointments and core infrastructure tables

Revision ID: add_appointments_and_core
Revises: signing_tables_fix_columns
Create Date: 2026-04-01 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_appointments_and_core'
down_revision = 'signing_tables_fix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Appointments Table
    op.create_table(
        'appointments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='scheduled'),
        sa.Column('reminder_immediate_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reminder_8h_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('reminder_15m_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('patient_confirmation', sa.Boolean(), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointments_scheduled_at'), 'appointments', ['scheduled_at'], unique=False)

    # 2. Infrastructure Tables (if not exist)
    # Clinical Audit Log
    op.create_table(
        'clinical_audit_log',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('entity', sa.String(), nullable=False),
        sa.Column('entity_id', sa.UUID(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('performed_by', sa.UUID(), nullable=True),
        sa.Column('entry_metadata', sa.JSON(), nullable=True),
        sa.Column('previous_hash', sa.String(length=128), nullable=True),
        sa.Column('entry_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Idempotency Keys
    op.create_table(
        'idempotency_keys',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('response_payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('retention_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('idempotency_keys')
    op.drop_table('clinical_audit_log')
    op.drop_index(op.f('ix_appointments_scheduled_at'), table_name='appointments')
    op.drop_table('appointments')
