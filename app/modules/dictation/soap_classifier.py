import json
import logging
from google import genai
from app.core.config import settings
import asyncio

logger = logging.getLogger("dictation.soap")

class SOAPClassifier:
    """
    Expert Clinical Intelligence Layer.
    Extracts and organizes medical dictation into a full SOAP structure.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            self.client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            self.client = None

    async def classify(self, text: str):
        """
        Processes free-text dictation and maps it to the 4 SOAP pillars.
        Cleans speech artifacts (ums, ehs) and uses professional terminology.
        """
        if not self.client:
            return {
                "subjective": text,
                "objective": "",
                "assessment": "",
                "plan": ""
            }

        prompt = f"""
        Actúa como un transcriptor médico experto. Tu objetivo es procesar un dictado de voz y organizarlo en una estructura SOAP completa.

        REGLAS:
        1. Filtra muletillas ("eh", "este", "bueno") y ruidos del habla.
        2. Transforma el lenguaje coloquial a lenguaje clínico profesional (ej: "le duelen las anginas" -> "odinofagia / amigdalitis").
        3. Si una sección no tiene información, devuélvela como una cadena vacía "".
        4. No inventes información que no esté en el texto.

        ESTRUCTURA DE SALIDA (JSON):
        - subjective: Motivo de consulta y síntomas referidos por el paciente.
        - objective: Hallazgos físicos, signos vitales o laboratorios mencionados.
        - assessment: Impresión diagnóstica o análisis del médico.
        - plan: Medicamentos, dosis, estudios solicitados y seguimiento.

        TEXTO A PROCESAR:
        "{text}"

        Responde ÚNICAMENTE con el objeto JSON plano.
        """

        try:
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
            logger.error(f"Gemini Full SOAP Extraction Error: {str(e)}")
            return {
                "subjective": text,
                "objective": "",
                "assessment": "",
                "plan": ""
            }
