"""add clinical note embeddings table

Revision ID: rag_001_add_embeddings
Revises: staff_assignments_001
Create Date: 2026-05-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'rag_001_add_embeddings'
down_revision = 'staff_assignments_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Ensure vector extension is enabled (already in initial but safe to repeat)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # 2. Create clinical_note_embeddings table
    op.execute("""
    CREATE TABLE IF NOT EXISTS clinical_note_embeddings (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        note_id UUID NOT NULL UNIQUE REFERENCES clinical_notes(id) ON DELETE CASCADE,
        patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
        embedding VECTOR(768),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """)

    # 3. Create HNSW index for better performance than IVFFlat on small/medium datasets
    op.execute("""
    CREATE INDEX IF NOT EXISTS idx_clinical_note_embeddings_vector 
    ON clinical_note_embeddings USING hnsw (embedding vector_cosine_ops);
    """)


def downgrade() -> None:
    op.drop_table('clinical_note_embeddings')
