"""users_add_settings_json

Revision ID: 9cb27b353209
Revises: sessions_closed_at_001
Create Date: 2026-05-15 08:13:52.780400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '9cb27b353209'
down_revision: Union[str, Sequence[str], None] = 'sessions_closed_at_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'settings')
