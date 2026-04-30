from fastapi import HTTPException


class EncounterService:

    def __init__(self, repo):
        self.repo = repo

    async def create(self, payload, org, doctor_id):
        return await self.repo.create(payload, org, doctor_id)

    async def get(self, encounter_id, org):
        encounter = await self.repo.get(encounter_id, org)
        if not encounter:
            raise HTTPException(404, "Encounter not found")
        return encounter

    async def list_all(self, org, limit, offset, doctor_ids=None):
        return await self.repo.list_all(org, limit, offset, doctor_ids)

    async def list_by_patient(self, patient_id, org, limit, offset, doctor_ids=None):
        return await self.repo.list_by_patient(patient_id, org, limit, offset, doctor_ids)

    async def list_by_doctor(self, doctor_id, org, limit, offset):
        return await self.repo.list_by_doctor(doctor_id, org, limit, offset)

    async def list_by_session(self, session_id, org, limit, offset, doctor_ids=None):
        return await self.repo.list_by_session(session_id, org, limit, offset, doctor_ids)

    async def update(self, encounter_id, org, payload):
        encounter = await self.repo.update(encounter_id, org, payload)
        if not encounter:
            raise HTTPException(404, "Encounter not found")
        return encounter

    async def close(self, encounter_id, org):
        await self.repo.close(encounter_id, org)

    async def reassign(self, encounter_id, org, new_doctor_id):
        encounter = await self.repo.reassign_doctor(encounter_id, org, new_doctor_id)
        if not encounter:
            raise HTTPException(404, "Encounter not found")
        return encounter
