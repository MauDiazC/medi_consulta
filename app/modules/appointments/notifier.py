import json
import logging
from google import genai
from app.core.config import settings
from datetime import datetime, timezone
import os
import httpx
import asyncio

logger = logging.getLogger("appointments.notifier")

class AppointmentNotifier:
    def __init__(self):
        self.meta_token = settings.get("META_WHATSAPP_TOKEN")
        self.phone_number_id = settings.get("META_PHONE_NUMBER_ID")
        
        # Initialize Google GenAI (New SDK)
        if settings.get("GOOGLE_AI_API_KEY"):
            self.client = genai.Client(api_key=settings.GOOGLE_AI_API_KEY)
        else:
            self.client = None
            logger.warning("GOOGLE_AI_API_KEY not configured. AI reminders will be disabled.")

    async def generate_ai_message(self, patient_name: str, doctor_name: str, scheduled_at: str, reason: str, reminder_type: str):
        """
        Generates a personalized WhatsApp message using Google Gemini 2.0.
        reminder_type: 'immediate', '12h', '5m'
        """
        prompt = f"""
        Eres un asistente médico virtual amable y profesional.
        Genera un mensaje de WhatsApp para un paciente con los siguientes datos:
        - Paciente: {patient_name}
        - Doctor: {doctor_name}
        - Fecha/Hora: {scheduled_at}
        - Motivo: {reason}
        - Tipo de recordatorio: {reminder_type} (immediate = recién agendada, 12h = faltan 12 horas, 5m = faltan 5 minutos)

        Si es 5m o 12h, pide confirmación de asistencia de forma muy breve.
        El mensaje debe ser corto, cálido y claro. Usa emojis de forma moderada.
        Responde ÚNICAMENTE con el texto del mensaje.
        """

        if not self.client:
            return f"Hola {patient_name}, te recordamos tu cita con el Dr. {doctor_name} el {scheduled_at}. ¡Te esperamos!"

        try:
            # Gemini execution with Gemini 2.5 Flash
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-2.5-flash',
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Google Gemini error: {str(e)}")
            # Fallback message
            return f"Hola {patient_name}, te recordamos tu cita con el Dr. {doctor_name} el {scheduled_at}. ¡Te esperamos!"

    async def send_whatsapp(self, phone: str, message: str, appointment_id: str):
        """
        Sends the message using Meta Cloud API.
        """
        if not self.meta_token or not self.phone_number_id:
            logger.warning("Meta Cloud API credentials not configured. Skipping WhatsApp.")
            return

        # Meta standard: phone number without '+'
        clean_phone = phone.replace("+", "").replace(" ", "").strip()
        
        url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.meta_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                r = await client.post(url, json=payload, headers=headers, timeout=10.0)
                if r.status_code >= 400:
                    logger.error(f"Meta API error ({r.status_code}): {r.text}")
                else:
                    logger.info(f"WhatsApp message sent to {clean_phone} for appointment {appointment_id}")
        except Exception as e:
            logger.error(f"Meta HTTP client error: {str(e)}")

    async def extract_intent(self, user_message: str):
        """
        Uses Gemini to extract intention from a WhatsApp message.
        Returns: 'confirm', 'cancel', or 'other'
        """
        if not self.client:
            # Fallback a lógica simple
            msg = user_message.lower()
            if any(k in msg for k in ["si", "confirm", "acepto", "voy"]): return "confirm"
            if any(k in msg for k in ["no", "cancel", "posp", "malo"]): return "cancel"
            return "other"

        prompt = f"""
        Analiza el siguiente mensaje de un paciente respondiendo a un recordatorio de cita médica.
        Determina si el paciente está CONFIRMANDO, CANCELANDO o si es OTRA COSA (duda, cambio de hora, etc.).
        
        Mensaje: "{user_message}"
        
        Responde ÚNICAMENTE con una de estas tres palabras: confirm, cancel, other.
        """

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model='gemini-1.5-flash',
                contents=prompt
            )
            result = response.text.strip().lower()
            if "confirm" in result: return "confirm"
            if "cancel" in result: return "cancel"
            return "other"
        except Exception:
            return "other"
