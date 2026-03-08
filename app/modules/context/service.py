class ContextService:

    def __init__(
        self,
        repo,
        builder,
    ):
        self.repo = repo
        self.builder = builder

    async def refresh(self, patient_id):

        memory = await self.builder.build(
            patient_id
        )

        await self.repo.upsert(
            patient_id,
            memory["summary"],
            memory["medications"],
            memory["alerts"],
        )

    async def get(self, patient_id):
        return await self.repo.get(patient_id)
