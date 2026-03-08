from .analyzer import CopilotAnalyzer


class CopilotService:

    def __init__(self, repo):
        self.repo = repo
        self.analyzer = CopilotAnalyzer()

    async def process_snapshot(
        self,
        note_id,
        session_id,
        draft,
    ):

        suggestions = self.analyzer.analyze(draft)

        if suggestions:
            await self.repo.save(
                note_id,
                session_id,
                suggestions,
            )

        return suggestions

    async def suggestions(self, note_id):
        return await self.repo.latest(note_id)
