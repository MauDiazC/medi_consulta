"""add triage and emergency contact fields

Revision ID: triage_and_emergency_contact_001
Revises: update_reminders_12h_5m
Create Date: 2026-04-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'triage_and_emergency_contact_001'
down_revision = 'update_reminders_12h_5m'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add emergency contact fields to patients
    op.add_column('patients', sa.Column('emergency_contact_name', sa.Text(), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact_phone', sa.Text(), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact_address', sa.Text(), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact_relationship', sa.Text(), nullable=True))
    op.add_column('patients', sa.Column('emergency_contact_email', sa.Text(), nullable=True))

    # 2. Create triage table
    op.create_table(
        'triage',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('appointment_id', sa.UUID(), nullable=True),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('heart_rate', sa.Float(), nullable=True),
        sa.Column('oxygen_saturation', sa.Float(), nullable=True),
        sa.Column('blood_pressure', sa.String(length=20), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], )
    )


def downgrade() -> None:
    op.drop_table('triage')
    op.drop_column('patients', 'emergency_contact_email')
    op.drop_column('patients', 'emergency_contact_relationship')
    op.drop_column('patients', 'emergency_contact_address')
    op.drop_column('patients', 'emergency_contact_phone')
    op.drop_column('patients', 'emergency_contact_name')
