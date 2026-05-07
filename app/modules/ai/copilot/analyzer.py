import json
import logging
from google import genai
from app.core.config import settings

logger = logging.getLogger("copilot.analyzer")

class CopilotAnalyzer:
    """
    Expert clinical safety analyzer.
    Focuses strictly on identifying Red Flags (high risk signs) 
    and Clinical Omissions (missing safety steps) without 
    influencing or making diagnostic decisions.
    """

    def __init__(self):
        self.api_key = settings.get("GOOGLE_AI_API_KEY")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            logger.warning("GOOGLE_AI_API_KEY not configured. Safety analysis will be basic.")

    async def analyze(self, draft: dict) -> list:
        """
        Analyzes a SOAP draft for clinical safety risks and omissions.
        Returns a list of safety suggestions.
        """
        suggestions = []

        # 1. Structural Basic Validations (Rule-based)
        if not draft.get("assessment"):
            suggestions.append({
                "type": "OMISSION",
                "content": "Se recomienda completar la sección de impresión diagnóstica (Assessment).",
                "severity": "medium"
            })

        if not draft.get("plan"):
            suggestions.append({
                "type": "OMISSION",
                "content": "Se recomienda definir un plan de tratamiento o seguimiento para el paciente.",
                "severity": "medium"
            })

        # 2. Clinical Intelligence (LLM-based)
        if self.client and (draft.get("subjective") or draft.get("objective")):
            ai_safety = await self._run_ai_safety_check(draft)
            suggestions.extend(ai_safety)

        return suggestions

    async def _run_ai_safety_check(self, draft: dict) -> list:
        """
        Consults Gemini to identify specific clinical safety risks.
        """
        try:
            # Contextual prompt for Safety Only
            prompt = f"""
            Actúa como un Auditor de Seguridad Clínica experto. 
            Analiza esta nota médica incompleta (SOAP) y detecta únicamente riesgos graves u omisiones críticas.

            REGLAS DE RESPUESTA (IMPORTANTE):
            - NO utilices las palabras 'omisión' o 'red flag' en la descripción.
            - Utiliza SIEMPRE la frase "Se recomienda..." al inicio de cada observación.
            - Ejemplo: "Se recomienda descartar infarto por dolor torácico referido" en lugar de "Red flag: dolor torácico".
            - Ejemplo: "Se recomienda solicitar hemoglobina glicosilada" en lugar de "Omisión: falta HbA1c".

            REGLAS ESTRICTAS:
            - NO sugieras diagnósticos definitivos.
            - NO tomes decisiones por el médico.
            - Solo advierte de peligros u omisiones de seguridad.
            - Si no hay riesgos claros, devuelve un array vacío [].
            - El idioma debe ser Español profesional.

            NOTA MÉDICA:
            Subjetivo: {draft.get('subjective', '')}
            Objetivo: {draft.get('objective', '')}
            Impresión: {draft.get('assessment', '')}
            Plan: {draft.get('plan', '')}

            Responde EXCLUSIVAMENTE en formato JSON con esta estructura:
            [
              {{
                "type": "RED_FLAG" | "OMISSION",
                "content": "Se recomienda [descripción corta y profesional]",
                "severity": "high" | "medium"
              }}
            ]
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                config=genai.types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
                contents=[prompt]
            )

            if not response.text:
                return []

            return json.loads(response.text)

        except Exception as e:
            logger.error(f"Error in AI Safety Check: {str(e)}")
            return []
