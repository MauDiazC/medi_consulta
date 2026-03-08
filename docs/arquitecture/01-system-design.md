# Diseño del Sistema - Mediconsulta

## Visión
Mediconsulta es una plataforma clínica de nivel empresarial construida sobre una **Arquitectura de Dominios Modulares**. Prioriza la integridad de los datos, la seguridad clínica y la capacidad de respuesta en tiempo real mediante un enfoque asíncrono y guiado por eventos.

## Arquitectura de Alto Nivel
- **Tipo de Arquitectura:** Dominios Modulares (Bounded Contexts).
- **Gestión de Estado:** Basada en Workspaces (estado mutable en ejecución) con Snapshots Inmutables.
- **Comunicación:** Dirigida por eventos a través de Redis Pub/Sub.
- **Concurrencia:** Control de concurrencia optimista con bloqueos distribuidos.
- **Evolución de Datos:** Migraciones versionadas con Alembic.

## Stack Tecnológico
- **Backend:** FastAPI (Python 3.13+)
- **Motor Asíncrono:** Asyncio
- **Base de Datos:** PostgreSQL con Async SQLAlchemy 2.0+
- **Migraciones:** Alembic
- **Caché y Mensajería:** Redis (Upstash)
- **Observabilidad:** OpenTelemetry (Tracing) y Prometheus (Metrics)
- **Seguridad:** Supabase Auth + JWT Institucional
- **IA:** Groq (Llama 3+)
