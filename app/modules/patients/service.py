from fastapi import HTTPException


class PatientService:

    def __init__(self, repo):
        self.repo = repo

    async def create(self, payload, org):
        return await self.repo.create(payload, org)

    async def list(self, org, limit, offset):
        return await self.repo.list(org, limit, offset)

    async def get(self, patient_id, org):
        patient = await self.repo.get(patient_id, org)
        if not patient:
            raise HTTPException(404, "Patient not found")
        return patient

    async def update(self, patient_id, org, payload):
        patient = await self.repo.update(patient_id, org, payload)
        if not patient:
            raise HTTPException(404, "Patient not found")
        return patient

    async def deactivate(self, patient_id, org):
        await self.repo.deactivate(patient_id, org)