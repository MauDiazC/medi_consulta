# Guía de Despliegue en Railway (v2 - Docker Edition)

Railway es la opción recomendada por su soporte nativo de Docker multi-etapa y su facilidad para inyectar variables de entorno de servicios externos.

## 1. Preparación de Infraestructura Externa
Asegúrate de tener las credenciales de:
- **Base de Datos:** Supabase (URL de conexión asíncrona `postgresql+asyncpg://...`)
- **Cache/Events:** Upstash Redis (URL `redis://...`)
- **IA:** Groq API Key (para el dictado y SOAP)

## 2. Configuración del Proyecto en Railway
1. Conecta tu repositorio de GitHub a Railway.
2. Railway detectará el `Dockerfile` automáticamente y comenzará el build.
3. **Variables de Entorno (Variables tab):**
   - `DATABASE_URL`: Tu cadena de Supabase (usar el puerto 5432 o 6543 con modo sesión).
   - `REDIS_URL`: Tu cadena de Upstash.
   - `SUPABASE_URL` y `SUPABASE_ANON_KEY`: Para el módulo de Auth.
   - `GROQ_API_KEY`: Para el motor de IA.

## 3. Configuración de Servicios (Web y Worker)
Al usar Dockerfile, Railway levantará un servicio por defecto. Debes configurar dos servicios usando la misma imagen:

### Servicio 1: API (Web)
- **Service Name:** `mediconsulta-api`
- **Start Command:** (Déjalo vacío, usará el `CMD` del Dockerfile: `uvicorn app.main:app --host 0.0.0.0 --port 8000`)
- **Networking:** Expone el puerto `8000`.

### Servicio 2: Realtime Worker (Background)
1. En el mismo proyecto, haz clic en **New -> GitHub Repo**.
2. Selecciona el mismo repositorio.
3. Ve a **Settings -> Deploy -> Start Command**.
4. Ingresa el comando para el worker:
   ```bash
   python -m app.worker.realtime_worker
   ```
5. En **Variables**, asegúrate de que tenga las mismas que el API (puedes usar Shared Variables).

---
## ¿Por qué Dockerfile?
- **Librerías de Sistema:** Instala automáticamente `pango` y `cairo` necesarias para WeasyPrint (PDFs).
- **Audio:** Incluye `libsndfile` necesaria para el procesamiento de dictado.
- **Paridad:** Garantiza que lo que corre en Railway sea idéntico a lo que corre en cualquier otro entorno.
