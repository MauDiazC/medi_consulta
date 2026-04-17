"""create_professional_identities

Revision ID: signing_identity_001
Revises: sessions_active_001
Create Date: 2026-04-17 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'signing_identity_001'
down_revision = 'sessions_active_001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Professional Identities Table
    op.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS professional_identities (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID NOT NULL REFERENCES users(id) UNIQUE,
            organization_id UUID NOT NULL REFERENCES organizations(id),
            public_key_pem TEXT NOT NULL,
            license_number TEXT NOT NULL,
            specialty TEXT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """))

def downgrade() -> None:
    op.drop_table('professional_identities')
