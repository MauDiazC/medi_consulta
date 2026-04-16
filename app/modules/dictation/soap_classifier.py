import json
import logging
import google.generativeai as genai
from app.core.config import settings
import anyio

logger = logging.getLogger("dictation.soap")

class SOAPClassifier:
    """
    Clinical Intelligence Layer using Google Gemini.
    Classifies and cleans medical dictation into SOAP sections.
    """
    
    def __init__(self):
        if settings.get("GOOGLE_AI_API_KEY"):
            genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def classify(self, text: str):
        """
        Organizes clinical text into structured SOAP format.
        """
        if not self.model:
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
            # Execute Gemini chat
            response = await anyio.to_thread.run_sync(
                lambda: self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                )
            )
            
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Gemini Classification Error: {str(e)}")
            # Fallback safe
            return {"section": "Subjective", "content": text}
