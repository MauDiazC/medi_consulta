import json
import httpx

from app.core.config import settings


class SOAPClassifier:

    async def classify(self, text: str):

        prompt = f"""
You are a clinical documentation assistant.

Classify the following medical sentence
into ONE SOAP section:

Subjective
Objective
Assessment
Plan

Return JSON ONLY:

{{
 "section": "...",
 "content": "clean clinical phrasing"
}}

Sentence:
{text}
"""

        async with httpx.AsyncClient() as client:

            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization":
                    f"Bearer {settings.groq_api_key}"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                },
            )

        data = r.json()

        content = (
            data["choices"][0]
            ["message"]["content"]
        )

        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            # Fallback simple
            return {"section": "Subjective", "content": text}
