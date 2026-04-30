"""create staff assignments table

Revision ID: staff_assignments_001
Revises: update_reminders_12h_5m
Create Date: 2026-04-29 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'staff_assignments_001'
down_revision = 'update_reminders_12h_5m'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'staff_assignments',
        sa.Column('staff_id', sa.UUID(), nullable=False),
        sa.Column('doctor_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['doctor_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staff_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('staff_id', 'doctor_id')
    )
    op.create_index('idx_staff_assignments_doctor', 'staff_assignments', ['doctor_id'])

def downgrade() -> None:
    op.drop_table('staff_assignments')
