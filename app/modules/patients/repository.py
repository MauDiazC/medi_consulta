from sqlalchemy import text


class PatientRepository:

    def __init__(self, db):
        self.db = db

    async def create(self, payload, org):
        r = await self.db.execute(
            text("""
                INSERT INTO patients(
                    first_name, last_name, phone_number, email, 
                    birth_date, sex,
                    organization_id, is_active,
                    emergency_contact_name, emergency_contact_phone,
                    emergency_contact_address, emergency_contact_relationship,
                    emergency_contact_email
                )
                VALUES(:f, :l, :p, :e, :b, :s, CAST(:o AS UUID), true, :ecn, :ecp, :eca, :ecr, :ece)
                RETURNING *
            """),
            {
                "f": payload.first_name, 
                "l": payload.last_name, 
                "p": payload.phone_number,
                "e": payload.email,
                "b": payload.birth_date,
                "s": payload.sex,
                "o": org,
                "ecn": payload.emergency_contact_name,
                "ecp": payload.emergency_contact_phone,
                "eca": payload.emergency_contact_address,
                "ecr": payload.emergency_contact_relationship,
                "ece": payload.emergency_contact_email
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def list(self, org, limit, offset):
        r = await self.db.execute(
            text("""
                SELECT *
                FROM patients
                WHERE organization_id=CAST(:org AS UUID)
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
                    last_name  = COALESCE(:l, last_name),
                    phone_number = COALESCE(:p, phone_number),
                    email      = COALESCE(:e, email),
                    birth_date = COALESCE(:b, birth_date),
                    sex        = COALESCE(:s, sex),
                    emergency_contact_name = COALESCE(:ecn, emergency_contact_name),
                    emergency_contact_phone = COALESCE(:ecp, emergency_contact_phone),
                    emergency_contact_address = COALESCE(:eca, emergency_contact_address),
                    emergency_contact_relationship = COALESCE(:ecr, emergency_contact_relationship),
                    emergency_contact_email = COALESCE(:ece, emergency_contact_email)
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
                RETURNING *
            """),
            {
                "id": patient_id,
                "org": org,
                "f": payload.first_name,
                "l": payload.last_name,
                "p": payload.phone_number,
                "e": payload.email,
                "b": payload.birth_date,
                "s": payload.sex,
                "ecn": payload.emergency_contact_name,
                "ecp": payload.emergency_contact_phone,
                "eca": payload.emergency_contact_address,
                "ecr": payload.emergency_contact_relationship,
                "ece": payload.emergency_contact_email
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def get_by_phone(self, phone: str):
        """
        Busca un paciente por su número de teléfono (formato internacional).
        """
        r = await self.db.execute(
            text("""
                SELECT *
                FROM patients
                WHERE phone_number = :p OR phone_number = :p_with_plus
                LIMIT 1
            """),
            {"p": phone.replace("+", ""), "p_with_plus": f"+{phone.replace('+', '')}"},
        )
        return r.mappings().first()

    async def deactivate(self, patient_id, org):
        await self.db.execute(
            text("""
                UPDATE patients
                SET is_active=false
                WHERE id=CAST(:id AS UUID) AND organization_id=CAST(:org AS UUID)
            """),
            {"id": patient_id, "org": org},
        )
        await self.db.commit()