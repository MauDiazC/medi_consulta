"""users_add_slug_column

Revision ID: 133b41a172d2
Revises: 711f26255395
Create Date: 2026-05-26 19:14:05.282890

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '133b41a172d2'
down_revision: str | Sequence[str] | None = '711f26255395'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("slug", sa.Text(), nullable=True, unique=True))

    # Backfill slugs for existing doctors
    import re
    import unicodedata

    bind = op.get_bind()
    result = bind.execute(sa.text("SELECT id, full_name FROM users WHERE role = 'doctor' AND slug IS NULL"))
    users = result.mappings().all()

    for user in users:
        user_id = user["id"]
        full_name = user["full_name"]

        base_slug = full_name.lower().strip()
        base_slug = unicodedata.normalize('NFKD', base_slug).encode('ascii', 'ignore').decode('utf-8')
        base_slug = re.sub(r'[^a-z0-9]+', '-', base_slug)
        base_slug = re.sub(r'-+', '-', base_slug).strip('-')
        if not base_slug:
            base_slug = "doctor"

        slug = base_slug
        counter = 1
        while True:
            chk = bind.execute(sa.text("SELECT id FROM users WHERE slug = :slug"), {"slug": slug}).first()
            if not chk:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1

        bind.execute(
            sa.text("UPDATE users SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": user_id}
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "slug")
