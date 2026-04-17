"""add_active_to_patients

Revision ID: patients_active_001
Revises: org_profile_001
Create Date: 2026-04-17 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'patients_active_001'
down_revision = 'org_profile_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add active column to patients with default true
    op.add_column('patients', sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    
def downgrade() -> None:
    op.drop_column('patients', 'active')
