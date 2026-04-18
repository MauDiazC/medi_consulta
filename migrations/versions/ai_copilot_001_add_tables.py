"""create ai copilot suggestions table

Revision ID: ai_copilot_001_add_tables
Revises: signing_identity_001
Create Date: 2026-04-18 04:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ai_copilot_001_add_tables'
down_revision = 'signing_identity_001'
branch_labels = None
depends_on = None


def upgrade():
    # Usamos raw SQL con IF NOT EXISTS para evitar errores si la tabla ya fue creada manualmente
    op.execute("""
        CREATE TABLE IF NOT EXISTS ai_copilot_suggestions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            note_id UUID NOT NULL,
            session_id VARCHAR,
            suggestion_type VARCHAR NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
        )
    """)
    
    # El índice también debe ser creado con precaución
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_copilot_note ON ai_copilot_suggestions (note_id)
    """)


def downgrade():
    op.drop_table('ai_copilot_suggestions')
