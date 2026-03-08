# Modelo Clínico - Workspace y Snapshots

## Estrategia de Workspace
El **Workspace** representa el estado activo y mutable de una sesión clínica.
- **Estado Mutable:** Borradores activos, dictados en curso y datos clínicos que están siendo editados.
- **Ciclo de Auto-guardado:** Cada cambio en el workspace dispara un evento de auto-guardado en Redis.
- **Estado de Borrador:** Una nota clínica permanece como "borrador" mientras resida en el workspace.

## Estrategia de Snapshot
Un **Snapshot** es el registro clínico inmutable en un punto específico del tiempo.
- **Inmutabilidad:** Una vez creado el snapshot, NO DEBE ser editado.
- **Registro Legal:** Los snapshots firmados son la fuente de verdad para auditorías clínicas.
- **Flujo de Firma:** `Congelar Estado del Workspace` → `Crear Snapshot` → `Aplicar Firma Criptográfica`.

## Versionado de Notas
- **Solo Anexar (Append-only):** Las notas se versionan de forma incremental. Las versiones antiguas se conservan para auditoría.
- **Responsabilidad de Firma:** La lógica de firma reside EXCLUSIVAMENTE en `app/modules/notes/signing`.
- **Notas Firmadas:** Una vez firmada, la nota es inmutable y pasa a formar parte de la línea de tiempo clínica.
