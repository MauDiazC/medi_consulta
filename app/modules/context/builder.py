from sqlalchemy import text


class ContextBuilder:

    def __init__(self, db):
        self.db = db

    async def build(self, patient_id):

        r = await self.db.execute(text("""
        SELECT assessment, plan
        FROM clinical_notes n
        JOIN encounters e
        ON e.id=n.encounter_id
        WHERE e.patient_id=:pid
        ORDER BY n.created_at DESC
        LIMIT 5
        """), {"pid": patient_id})

        notes = r.mappings().all()

        summary = "\n".join(
            n["assessment"] or ""
            for n in notes
        )

        medications = "\n".join(
            n["plan"] or ""
            for n in notes
        )

        return {
            "summary": summary,
            "medications": medications,
            "alerts": "",
        }
