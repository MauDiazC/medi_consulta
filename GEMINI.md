# Mediconsulta Architecture Governance (v1)

Este proyecto sigue una arquitectura modular estricta. Todas las modificaciones DEBEN cumplir con estas reglas.

## ESTADO DEL PROYECTO (2026-04-19)

### ✅ AVANCES REALIZADOS
1.  **Módulo de Citas (Appointments):**
    *   Migración completa de n8n a **Meta Cloud API (WhatsApp)** directa.
    *   Implementación de **Gemini 2.5 Flash** para generación de mensajes y extracción de intención.
    *   Nuevos intervalos de recordatorio: **Inmediato, 12 horas y 5 minutos** antes de la cita.
2.  **Arquitectura de Workers (Escalabilidad):**
    *   Separación de responsabilidades en 3 servicios: `api`, `worker-realtime` y `worker-appointments`.
    *   Worker dedicado para citas para garantizar precisión clínica en las notificaciones.
3.  **Base de Datos:**
    *   Unificación de cabezas de Alembic (`update_reminders_12h_5m` re-encadenado a `sessions_add_user_001`).
    *   Nuevas columnas de seguimiento: `reminder_12h_sent` y `reminder_5m_sent`.
4.  **Seguridad & Auditoría:**
    *   Endpoint de emergencia implementado para reasignación de `doctor_id` en encuentros.
    *   Auditoría de identidades para el Dashboard personalizada por rol (Admin vs Doctor).

### 🛠 ESTADO ACTUAL EN RAILWAY
- **API:** Desplegada y operativa.
- **Worker Realtime:** Procesa Outbox, PDFs y seguridad.
- **Worker Appointments:** Loop dedicado (cada 30s) para WhatsApp.
- **Webhooks:** `/appointments/webhook` listo para ser configurado en Meta Developers.

### 🚀 PUNTO DE PARTIDA PARA LA PRÓXIMA SESIÓN
1.  **Validación de Webhook:** Probar la recepción de respuestas de pacientes ("Sí", "No", "Mañana") y verificar la actualización automática del estado de la cita.
2.  **Configuración Meta:** Confirmar que las variables `META_WHATSAPP_TOKEN`, `META_PHONE_NUMBER_ID` y `META_VERIFY_TOKEN` han sido copiadas al nuevo worker en Railway.
3.  **Dashboard Médico:** Verificar que los encuentros reasignados y las citas confirmadas aparecen correctamente en el `summary` del Doctor.
4.  **Testing:** Implementar tests de integración para el flujo de Webhooks de Meta.

---

## REGLAS DE ARQUITECTURA (NO NEGOCIABLES)
- **Modular Domain Architecture:** Todo lo relacionado a citas vive en `app/modules/appointments`.
- **Async-first:** Prohibido el uso de IO bloqueante.
- **Event-driven:** El cambio de estado de una cita debe publicar un evento `appointment.updated`.
- **Gemini Model:** Usar preferentemente la familia **Flash (2.5)** para tareas de baja latencia.
