# Secuencia de Validación del Flujo Clínico (v2)

Sigue este orden lógico para validar el sistema desde cero (Cold Start).

## Paso 1: Onboarding de Identidad (Identity Bootstrap)
Antes de tener una organización, el usuario debe existir en el sistema.
- **Endpoint:** `POST /auth/bootstrap`
- **Payload:** `{"access_token": "SUPABASE_JWT"}`
- **Descripción:** Este paso crea tu registro de usuario en Mediconsulta basado en tu identidad de Supabase.
- **Resultado esperado:** Token JWT inicial de Mediconsulta.

## Paso 2: Creación de Organización y Vínculo de Administrador
Con el token obtenido en el paso 1, crea tu clínica.
- **Endpoint:** `POST /organizations`
- **Headers:** `Authorization: Bearer <TOKEN_PASO_1>`
- **Payload:** `{"name": "Clínica San José"}`
- **Descripción:** Este endpoint crea la organización y vincula automáticamente a tu usuario como administrador de la misma.
- **Resultado esperado:** Objeto Organización con su `id`.

## Paso 3: Re-Autenticación (Obtener Token con Org Context)
Para que el sistema sepa en qué organización estás operando, debes obtener un nuevo token que ya incluya el `organization_id`.
- **Endpoint:** `POST /auth/login` o `POST /auth/exchange`
- **Resultado esperado:** Token JWT que contiene los claims `sub` (user_id) y `org` (organization_id). **Usa este token para todos los pasos siguientes.**

## Paso 4: Registro de Paciente
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

## Paso 5: Iniciar Encuentro (Consulta)
- **Endpoint:** `POST /encounters`
- **Payload:**
```json
{
  "patient_id": "ID_DEL_PASO_4",
  "clinical_session_id": "GUID_ALEATORIO",
  "reason": "Consulta por dolor abdominal"
}
```

## Paso 6: Dictado y Sugerencias IA
1. **Dictado (WebSocket):** Conectar a `WS /dictation/ws` y enviar chunks de audio.
2. **Sugerencias SOAP (SSE):** `POST /notes/ai/stream/{encounter_id}` para recibir la nota estructurada.

## Paso 7: Cierre Legal y Firma
1. **Finalizar Borrador:** `POST /notes/finalize/{encounter_id}`.
2. **Firma Digital:** `POST /notes/{note_id}/sign` (Subiendo archivo `.pem`).

## Paso 8: Auditoría
- **Endpoint:** `GET /notes/verify/{note_id}` para confirmar la integridad criptográfica.
