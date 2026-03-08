from sqlalchemy import text


class RAGRepository:

    def __init__(self, db):
        self.db = db

    async def search(
        self,
        patient_id,
        embedding,
    ):

        r = await self.db.execute(text("""
        SELECT note_id
        FROM clinical_note_embeddings
        WHERE patient_id=:pid
        ORDER BY embedding <-> :emb
        LIMIT 5
        """), {
            "pid": patient_id,
            "emb": embedding,
        })

        return r.mappings().all()
