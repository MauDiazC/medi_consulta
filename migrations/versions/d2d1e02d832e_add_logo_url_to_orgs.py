"""add_logo_url_to_orgs

Revision ID: d2d1e02d832e
Revises: 9cb27b353209
Create Date: 2026-05-15 08:17:25.137491

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2d1e02d832e'
down_revision: Union[str, Sequence[str], None] = '9cb27b353209'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('organizations', sa.Column('logo_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('organizations', 'logo_url')
