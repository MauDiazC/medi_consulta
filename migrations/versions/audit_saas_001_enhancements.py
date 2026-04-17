"""audit_saas_enhancements

Revision ID: audit_saas_001
Revises: auth_reset_001
Create Date: 2026-04-16 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'audit_saas_001'
down_revision = 'auth_reset_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add SaaS tracking columns to clinical_audit_log
    op.add_column('clinical_audit_log', sa.Column('organization_id', sa.UUID(), sa.ForeignKey('organizations.id'), nullable=True))
    op.add_column('clinical_audit_log', sa.Column('ip_address', sa.Text(), nullable=True))
    op.add_column('clinical_audit_log', sa.Column('user_agent', sa.Text(), nullable=True))
    
    # Add index for organization performance
    op.create_index('idx_audit_org', 'clinical_audit_log', ['organization_id'])

def downgrade() -> None:
    op.drop_index('idx_audit_org', table_name='clinical_audit_log')
    op.drop_column('clinical_audit_log', 'user_agent')
    op.drop_column('clinical_audit_log', 'ip_address')
    op.drop_column('clinical_audit_log', 'organization_id')
