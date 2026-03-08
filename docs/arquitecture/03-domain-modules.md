# Límites de Dominio y Módulos

## Estructura de Módulos
Cada módulo bajo `app/modules/` es un contexto delimitado y autosuficiente.

**Archivos permitidos dentro de un módulo:**
- `router.py`: Capa de transporte (endpoints de API).
- `service.py`: Lógica de dominio, decisiones de negocio y orquestación del módulo.
- `repository.py`: Operaciones CRUD y persistencia SQL.
- `schemas.py`: Modelos Pydantic para peticiones/respuestas (DTOs).
- `models.py`: Modelos SQLAlchemy específicos del módulo (opcional, si no usa SQL crudo).

## Reglas de Interacción
- **Sin Acceso Directo a la DB:** Los módulos NO deben consultar tablas de otros módulos directamente.
- **Comunicación solo vía Servicios:** Si el Módulo A necesita datos del Módulo B, DEBE llamar al servicio del Módulo B o reaccionar a un evento.
- **Aislamiento de Repositorios:** Los repositorios solo interactúan con las tablas definidas en su propio contexto.

## Módulos Core
- `auth`: Gestión de identidad y acceso institucional.
- `patients`: Datos demográficos y perfiles de pacientes.
- `encounters`: Seguimiento de encuentros clínicos.
- `notes`: Creación, versionado y firma legal de documentos.
- `workspace`: Estado mutable de la sesión clínica activa.
- `timeline`: Historial agregado de eventos del paciente.
- `organizations`, `users`, `dictation`, `rag`.
