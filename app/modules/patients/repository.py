from sqlalchemy import text


class PatientRepository:

    def __init__(self, db):
        self.db = db

    async def create(self, payload, org):
        r = await self.db.execute(
            text("""
                INSERT INTO patients(
                    first_name,last_name,
                    organization_id,active
                )
                VALUES(:f,:l,CAST(:o AS UUID),true)
                RETURNING *
            """),
            {"f": payload.first_name, "l": payload.last_name, "o": org},
        )
        await self.db.commit()
        return r.mappings().first()

    async def list(self, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM patients
                WHERE organization_id=CAST(:org AS UUID)
                AND active=true
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            {"org": org, "limit": limit, "offset": offset},
        )
        return r.mappings().all()

    async def get(self, patient_id, org):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM patients
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": patient_id, "org": org},
        )
        return r.mappings().first()

    async def update(self, patient_id, org, payload):
        r = await self.db.execute(
            text("""
                UPDATE patients
                SET first_name = COALESCE(:f, first_name),
                    last_name  = COALESCE(:l, last_name)
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
                RETURNING *
            """),
            {
                "id": patient_id,
                "org": org,
                "f": payload.first_name,
                "l": payload.last_name,
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def deactivate(self, patient_id, org):
        await self.db.execute(
            text("""
                UPDATE patients
                SET active=false
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": patient_id, "org": org},
        )
        await self.db.commit()