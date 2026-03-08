class ClinicalRAG:

    def __init__(
        self,
        embedder,
        repo,
    ):
        self.embedder = embedder
        self.repo = repo

    async def retrieve(
        self,
        patient_id,
        query_text,
    ):

        emb = await self.embedder.embed(
            query_text
        )

        notes = await self.repo.search(
            patient_id,
            emb,
        )

        return notes
