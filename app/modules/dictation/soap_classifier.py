import json
import logging
from google import genai
from app.core.config import settings
import asyncio

logger = logging.getLogger("dictation.soap")

class SOAPClassifier:
    """
    Clinical Intelligence Layer using Google Gemini (New SDK).
    Classifies and cleans medical dictation into SOAP sections.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            self.client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            self.client = None

    async def classify(self, text: str):
        """
        Organizes clinical text into structured SOAP format.
        """
        if not self.client:
            return {"section": "Subjective", "content": text}

        prompt = f"""
        Eres un asistente de documentación clínica experto.
        Tu tarea es clasificar la siguiente oración médica en UNA de las 4 secciones SOAP:
        - Subjective (Lo que el paciente reporta)
        - Objective (Signos físicos, laboratorio, hallazgos)
        - Assessment (Diagnóstico, impresión clínica)
        - Plan (Tratamiento, medicamentos, seguimiento)

        Responde ÚNICAMENTE en formato JSON plano:
        {{
         "section": "Subjective | Objective | Assessment | Plan",
         "content": "Redacción clínica limpia y corregida"
        }}

        Oración:
        {text}
        """

        try:
            # Execute Gemini chat with new SDK using 2.5 model
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Gemini Classification Error: {str(e)}")
            # Fallback safe
            return {"section": "Subjective", "content": text}
