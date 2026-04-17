"""unify_patient_active_status

Revision ID: patients_unify_status
Revises: patients_active_001
Create Date: 2026-04-17 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'patients_unify_status'
down_revision = 'patients_active_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Sync data from 'active' to 'is_active' before dropping
    op.execute("UPDATE patients SET is_active = active")
    # 2. Drop the redundant column
    op.drop_column('patients', 'active')
    
def downgrade() -> None:
    op.add_column('patients', sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.execute("UPDATE patients SET active = is_active")
