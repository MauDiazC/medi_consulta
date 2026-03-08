class CopilotAnalyzer:

    def analyze(self, draft: dict):

        suggestions = []

        if not draft.get("assessment"):
            suggestions.append({
                "type": "missing_section",
                "content": "Assessment section is empty"
            })

        if not draft.get("plan"):
            suggestions.append({
                "type": "missing_section",
                "content": "Plan section missing"
            })

        return suggestions
