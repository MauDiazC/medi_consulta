"""update appointment reminders to 12h and 5m

Revision ID: update_reminders_12h_5m
Revises: add_appointments_and_core
Create Date: 2026-04-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'update_reminders_12h_5m'
down_revision = 'add_appointments_and_core'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename columns to match new logic
    op.alter_column('appointments', 'reminder_8h_sent', new_column_name='reminder_12h_sent')
    op.alter_column('appointments', 'reminder_15m_sent', new_column_name='reminder_5m_sent')


def downgrade() -> None:
    # Revert column names
    op.alter_column('appointments', 'reminder_12h_sent', new_column_name='reminder_8h_sent')
    op.alter_column('appointments', 'reminder_5m_sent', new_column_name='reminder_15m_sent')
