"""add_appointment_id_to_encounters

Revision ID: encounters_001
Revises: org_settings_001
Create Date: 2026-05-05 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'encounters_001'
down_revision = 'org_settings_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('encounters', sa.Column('appointment_id', sa.UUID(), sa.ForeignKey('appointments.id'), nullable=True))
    op.create_index('idx_encounters_appointment', 'encounters', ['appointment_id'])

def downgrade() -> None:
    op.drop_index('idx_encounters_appointment', table_name='encounters')
    op.drop_column('encounters', 'appointment_id')
