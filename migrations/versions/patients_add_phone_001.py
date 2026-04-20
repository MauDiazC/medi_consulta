"""add phone_number to patients

Revision ID: patients_add_phone_001
Revises: signing_legal_artifacts_001
Create Date: 2026-04-18 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'patients_add_phone_001'
down_revision = 'signing_legal_artifacts_001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('patients', sa.Column('phone_number', sa.String(20), nullable=True))


def downgrade():
    op.drop_column('patients', 'phone_number')
