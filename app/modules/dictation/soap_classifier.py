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
        if not self.client or not text:
            return {
                "subjective": text or "",
                "objective": "",
                "assessment": "",
                "plan": ""
            }

        prompt = f"""
        Actúa como un transcriptor médico experto y asistente clínico de alto nivel. 
        Tu objetivo es procesar un dictado de voz y organizarlo en una estructura SOAP profesional.

        INSTRUCCIONES CRÍTICAS:
        1. FILTRADO: Elimina muletillas ("eh", "este", "bueno", "o sea") y ruidos del habla.
        2. TERMINOLOGÍA: Transforma el lenguaje coloquial a lenguaje clínico técnico preciso (ej: "manchas rojas" -> "exantema", "dolor de panza" -> "dolor abdominal").
        3. SUBJECTIVE: Incluye antecedentes, motivo de consulta y síntomas referidos.
        4. OBJECTIVE: Extrae signos vitales, hallazgos de exploración física o resultados de laboratorio mencionados.
        5. ASSESSMENT (MÁXIMA PRIORIDAD): Esta sección NO debe estar vacía. 
           - Si el médico menciona un diagnóstico, úsalo.
           - Si el médico NO menciona un diagnóstico explícito, tú debes INFÉRIR diagnósticos presuntivos o diagnósticos diferenciales basados en los síntomas descritos en 'Subjective'.
           - Utiliza frases como "Impresión diagnóstica de...", "A descartar...", o "Sugerente de...".
        6. PLAN: Incluye el tratamiento (fármacos, dosis, frecuencia), estudios solicitados y recomendaciones.

        ESTRUCTURA DE SALIDA (JSON):
        {{
            "subjective": "...",
            "objective": "...",
            "assessment": "...",
            "plan": "..."
        }}

        TEXTO A PROCESAR:
        "{text}"

        Responde ÚNICAMENTE con el objeto JSON plano, sin explicaciones adicionales.
        """

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-2.0-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )
            
            structured_data = json.loads(response.text)
            
            # Garantizar que todas las llaves existan
            required_keys = ["subjective", "objective", "assessment", "plan"]
            for key in required_keys:
                if key not in structured_data:
                    structured_data[key] = ""
            
            # Refuerzo para Assessment si Gemini lo dejó vacío a pesar de la instrucción
            if not structured_data["assessment"] and structured_data["subjective"]:
                structured_data["assessment"] = f"Impresión diagnóstica basada en: {structured_data['subjective'][:50]}..."

            return structured_data
            
        except Exception as e:
            logger.error(f"Gemini Full SOAP Extraction Error: {str(e)}")
            return {
                "subjective": text,
                "objective": "",
                "assessment": "Error en procesamiento de IA",
                "plan": ""
            }
