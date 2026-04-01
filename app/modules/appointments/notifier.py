import json
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger("appointments.notifier")

class AppointmentNotifier:
    def __init__(self):
        self.n8n_url = os.getenv("N8N_WHATSAPP_WEBHOOK_URL")
        self.groq_key = settings.GROQ_API_KEY

    async def generate_ai_message(self, patient_name: str, doctor_name: str, scheduled_at: str, reason: str, reminder_type: str):
        """
        Generates a personalized WhatsApp message using Groq.
        reminder_type: 'immediate', '8h', '15m'
        """
        prompt = f"""
        Eres un asistente médico virtual amable y profesional.
        Genera un mensaje de WhatsApp para un paciente con los siguientes datos:
        - Paciente: {patient_name}
        - Doctor: {doctor_name}
        - Fecha/Hora: {scheduled_at}
        - Motivo: {reason}
        - Tipo de recordatorio: {reminder_type} (immediate = recién agendada, 8h = faltan 8 horas, 15m = faltan 15 minutos)

        Si es 15m o 8h, pide confirmación de asistencia.
        El mensaje debe ser corto, cálido y claro. Usa emojis de forma moderada.
        Responde ÚNICAMENTE con el texto del mensaje.
        """

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                    },
                    timeout=10.0
                )
                data = r.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"Groq AI error: {str(e)}")
            # Fallback message
            return f"Hola {patient_name}, te recordamos tu cita con el Dr. {doctor_name} el {scheduled_at}. ¡Te esperamos!"

    async def send_whatsapp(self, phone: str, message: str, appointment_id: str):
        """
        Sends the message to n8n webhook.
        """
        if not self.n8n_url:
            logger.warning("N8N_WHATSAPP_WEBHOOK_URL not configured. Skipping WhatsApp.")
            return

        payload = {
            "phone": phone,
            "message": message,
            "appointment_id": str(appointment_id),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        try:
            async with httpx.AsyncClient() as client:
                await client.post(self.n8n_url, json=payload, timeout=5.0)
        except Exception as e:
            logger.error(f"n8n webhook error: {str(e)}")

import os
from datetime import datetime, timezone
