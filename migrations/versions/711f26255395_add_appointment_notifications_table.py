"""add_appointment_notifications_table

Revision ID: 711f26255395
Revises: a6c37fa7b591
Create Date: 2026-05-26 18:53:29.786898

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '711f26255395'
down_revision: Union[str, Sequence[str], None] = 'a6c37fa7b591'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'appointment_notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('appointment_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('whatsapp_message_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_appointment_notifications_appointment_id'), 'appointment_notifications', ['appointment_id'], unique=False)
    op.create_index(op.f('ix_appointment_notifications_whatsapp_message_id'), 'appointment_notifications', ['whatsapp_message_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_appointment_notifications_whatsapp_message_id'), table_name='appointment_notifications')
    op.drop_index(op.f('ix_appointment_notifications_appointment_id'), table_name='appointment_notifications')
    op.drop_table('appointment_notifications')
