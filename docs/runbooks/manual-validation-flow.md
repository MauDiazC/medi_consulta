# Secuencia de Validación del Flujo Clínico

Sigue este orden para validar que todos los módulos (Auth, Patients, Encounters, AI, RAG, Notes) están integrados correctamente.

## Paso 1: Autenticación y Onboarding
Si eres un usuario nuevo en Mediconsulta pero vienes de Supabase:
- **Endpoint:** `POST /auth/bootstrap`
- **Payload:** `{"access_token": "SUPABASE_JWT"}`
- **Resultado esperado:** Token de acceso de Mediconsulta.

## Paso 2: Registro de Paciente
- **Endpoint:** `POST /patients`
- **Payload:**
```json
{
  "first_name": "Juan",
  "last_name": "Pérez",
  "birth_date": "1985-05-20",
  "sex": "M",
  "email": "juan.perez@test.com"
}
```

## Paso 3: Iniciar Encuentro (Consulta)
- **Endpoint:** `POST /encounters`
- **Payload:**
```json
{
  "patient_id": "ID_DEL_PASO_2",
  "clinical_session_id": "GUID_ALEATORIO",
  "reason": "Dolor abdominal agudo"
}
```

## Paso 4: Dictado en Tiempo Real (WebSocket)
- **Endpoint:** `WS /dictation/ws`
- **Acción:** Envía audio en chunks.
- **Validación:** El Worker debería procesar el audio, usar Groq para transcribir y publicar eventos de "texto transcrito" en Redis que el frontend escucha.

## Paso 5: Sugerencias SOAP con IA
- **Endpoint:** `POST /notes/ai/stream/{encounter_id}`
- **Validación:** Recibirás un flujo (SSE) con la estructura SOAP sugerida basada en lo dictado.

## Paso 6: Consulta de Contexto (RAG)
Para traer historia clínica relevante del paciente:
- **Endpoint:** `GET /rag/context/{patient_id}?query=antecedentes gastricos`
- **Validación:** El sistema busca en el repositorio vectorial y devuelve fragmentos de notas anteriores.

## Paso 7: Finalizar y Firmar
1. **Finalizar Versión:** `POST /notes/finalize/{encounter_id}` (Congela el borrador actual).
2. **Firmar Nota:** `POST /notes/{note_id}/sign`
   - **Payload:** Debes subir un archivo `.pem` (tu llave privada).
   - **Validación:** La nota se vuelve inmutable y se genera el hash encadenado en el log de auditoría.

## Paso 8: Verificación de Auditoría
- **Endpoint:** `GET /notes/verify/{note_id}`
- **Resultado:** Confirmación de que la firma es válida y el registro no ha sido alterado.
