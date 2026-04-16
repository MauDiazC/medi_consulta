"""add_auth_reset_tokens

Revision ID: auth_reset_001
Revises: b3630857c370
Create Date: 2026-04-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'auth_reset_001'
down_revision = 'b3630857c370'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id uuid NOT NULL REFERENCES users(id),
        token text NOT NULL UNIQUE,
        expires_at timestamp with time zone NOT NULL,
        created_at timestamp with time zone DEFAULT now(),
        used_at timestamp with time zone
    );
    """)

def downgrade() -> None:
    op.drop_table('password_reset_tokens')
