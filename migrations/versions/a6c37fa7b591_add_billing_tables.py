"""add_billing_tables

Revision ID: a6c37fa7b591
Revises: d2d1e02d832e
Create Date: 2026-05-15 19:04:01.099916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a6c37fa7b591'
down_revision: Union[str, Sequence[str], None] = 'd2d1e02d832e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update organizations table
    op.add_column('organizations', sa.Column('stripe_customer_id', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('stripe_subscription_id', sa.Text(), nullable=True))
    op.add_column('organizations', sa.Column('subscription_status', sa.Text(), server_default='trialing', nullable=False))
    op.add_column('organizations', sa.Column('subscription_period_end', sa.DateTime(timezone=True), nullable=True))

    # 2. Create billing_payments table
    op.create_table(
        'billing_payments',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('stripe_payment_intent_id', sa.Text(), nullable=False),
        sa.Column('stripe_invoice_id', sa.Text(), nullable=True),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('cfdi_status', sa.Text(), server_default='pending', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. Create billing_invoices table
    op.create_table(
        'billing_invoices',
        sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('payment_id', sa.UUID(), nullable=False),
        sa.Column('facturapi_id', sa.Text(), nullable=False),
        sa.Column('uuid_sat', sa.Text(), nullable=True),
        sa.Column('xml_url', sa.Text(), nullable=True),
        sa.Column('pdf_url', sa.Text(), nullable=True),
        sa.Column('status', sa.Text(), server_default='valid', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['payment_id'], ['billing_payments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Create billing_webhook_logs table
    op.create_table(
        'billing_webhook_logs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('billing_webhook_logs')
    op.drop_table('billing_invoices')
    op.drop_table('billing_payments')
    op.drop_column('organizations', 'subscription_period_end')
    op.drop_column('organizations', 'subscription_status')
    op.drop_column('organizations', 'stripe_subscription_id')
    op.drop_column('organizations', 'stripe_customer_id')
