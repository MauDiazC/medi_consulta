"""expand_organization_profile

Revision ID: org_profile_001
Revises: audit_saas_001
Create Date: 2026-04-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'org_profile_001'
down_revision = 'audit_saas_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column('organizations', sa.Column('address', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('phone', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('description', sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column('organizations', 'description')
    op.drop_column('organizations', 'phone')
    op.drop_column('organizations', 'address')
