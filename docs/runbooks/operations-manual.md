# Manual de Operaciones - Mediconsulta

Este documento describe cómo gestionar el sistema tras la profesionalización.

## 1. Gestión de Base de Datos (Alembic)
Ya no uses scripts SQL manuales. Todo cambio en la DB debe quedar registrado.

- **Crear nueva migración:**
  Si modificas un modelo o quieres añadir una tabla:
  `alembic revision --autogenerate -m "descripcion del cambio"`
- **Aplicar cambios en local:**
  `alembic upgrade head`
- **En Producción (Railway):**
  Asegúrate de que tu comando de despliegue incluya las migraciones antes de arrancar el API:
  `alembic upgrade head && uvicorn app.main:app ...`

## 2. Desarrollo Local Diario
Para mantener la calidad, usa el stack de herramientas instalado:

- **Formateo y Linting:** `ruff check . --fix` y `ruff format .`
- **Tipado:** `uv run mypy app/`
- **Tests con Cobertura:** `pytest --cov=app`

## 3. Flujo del Usuario (Ciclo de Vida)
El sistema opera bajo un flujo de confianza progresiva:

1.  **Onboarding:** El usuario inicia sesión vía Supabase y se "bootstrapea" en Mediconsulta (`/auth/bootstrap`).
2.  **Contexto:** El sistema inyecta el `organization_id` en cada petición automáticamente vía el token JWT.
3.  **Acción Clínica:** El médico crea un encuentro y dicta.
    - El **Worker** procesa el audio en segundo plano.
    - El **API** recibe eventos de Redis para actualizar el Workspace.
4.  **Cierre Legal:** Al firmar, el sistema congela el estado, crea el snapshot y genera el hash encadenado (Audit Trail).

## 4. Monitoreo y Debugging
- **Métricas:** Revisa `https://tu-api.railway.app/metrics`.
- **Trazas:** Si configuraste un OTLP Collector, verás los cuellos de botella de cada query SQL.
- **Logs:** Busca el `trace_id` en los logs de Railway para ver todo lo que pasó en una sola petición.
