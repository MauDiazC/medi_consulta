# Estructura del Proyecto y Gobernanza

## Reglas de Propiedad de Carpetas
La estructura está estrictamente segregada por dominio. No se permiten capas de lógica global compartida.

### Directorios Raíz:
- `app/core/` → ÚNICAMENTE infraestructura transversal (config, db, seguridad, logging, eventos, telemetría).
- `app/modules/` → TODA la lógica de negocio/dominio. Cada subcarpeta es un contexto delimitado.
- `app/worker/` → Procesamiento en segundo plano (tareas asíncronas).
- `app/cli/` → Operaciones internas y scripts de automatización.

### Capas Prohibidas:
Para evitar la degradación arquitectónica, las siguientes capas globales están **estrictamente prohibidas**:
- ❌ `app/services` (Servicios globales)
- ❌ `app/models` (Modelos compartidos)
- ❌ `app/utils` (Utilidades genéricas compartidas)
- ❌ `app/api` (Enrutamiento centralizado)

## Reglas de Importación
- **Solo Importaciones Absolutas:** `from app.modules.notes.service import ...`
- **Sin Importaciones Relativas:** Nunca usar rutas relativas entre módulos para asegurar la portabilidad modular.
