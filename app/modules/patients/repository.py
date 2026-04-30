from sqlalchemy import text


class PatientRepository:

    def __init__(self, db):
        self.db = db

    def _format_mexico_phone(self, phone: str | None) -> str | None:
        if not phone:
            return None
        # Limpiar caracteres no numéricos
        clean_phone = "".join(filter(str.isdigit, phone))
        # Si tiene 10 dígitos, añadir 52
        if len(clean_phone) == 10:
            return f"52{clean_phone}"
        # Si ya tiene 12 y empieza con 52, dejarlo así
        if len(clean_phone) == 12 and clean_phone.startswith("52"):
            return clean_phone
        return clean_phone

    async def create(self, payload, org):
        phone = self._format_mexico_phone(payload.phone_number)
        
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
                "p": phone,
                "e": payload.email,
                "b": payload.birth_date,
                "s": payload.sex,
                "o": org,
                "ecn": payload.emergency_contact_name,
                "ecp": self._format_mexico_phone(payload.emergency_contact_phone),
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
                "p": self._format_mexico_phone(payload.phone_number),
                "e": payload.email,
                "b": payload.birth_date,
                "s": payload.sex,
                "ecn": payload.emergency_contact_name,
                "ecp": self._format_mexico_phone(payload.emergency_contact_phone),
                "eca": payload.emergency_contact_address,
                "ecr": payload.emergency_contact_relationship,
                "ece": payload.emergency_contact_email
            },
        )
        await self.db.commit()
        return r.mappings().first()

    async def get_by_phone(self, phone: str):
        """
        Busca un paciente por su número de teléfono. 
        Maneja formatos con y sin prefijo 52.
        """
        clean_phone = "".join(filter(str.isdigit, phone))
        
        # Generar variantes para la búsqueda
        ten_digits = clean_phone[-10:] if len(clean_phone) >= 10 else clean_phone
        with_52 = f"52{ten_digits}"
        
        r = await self.db.execute(
            text("""
                SELECT *
                FROM patients
                WHERE phone_number = :p1 
                   OR phone_number = :p2 
                   OR phone_number = :p3
                LIMIT 1
            """),
            {"p1": ten_digits, "p2": with_52, "p3": f"+{with_52}"},
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
