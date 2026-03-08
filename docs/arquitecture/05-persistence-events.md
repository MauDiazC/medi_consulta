# Persistencia y Arquitectura Dirigida por Eventos

## Capa de Base de Datos
Mediconsulta utiliza **Async SQLAlchemy 2.0+** para la interacción con PostgreSQL.

- **Solo Asíncrono:** Toda la E/S de la base de datos DEBE ser no bloqueante. Las llamadas síncronas están prohibidas.
- **Migraciones con Alembic:** Todos los cambios en el esquema deben realizarse mediante migraciones versionadas.
- **Patrón Repositorio:** Únicamente operaciones CRUD y lógica SQL directa. No debe haber lógica de negocio en los repositorios.

## Sistema de Eventos (Redis)
Todos los cambios de estado entre módulos DEBEN publicar un evento en Redis.

- **Redis Pub/Sub:** Utilizado para actualizaciones en tiempo real y comunicación entre servicios.
- **Descarga a Workers:** Las tareas pesadas de CPU o llamadas a APIs externas se envían a los workers a través de eventos.
- **Sincronización en Tiempo Real:** Los clientes frontend reciben eventos de invalidación de workspace a través de SSE disparados por mensajes de Redis.

## Seguridad Asíncrona
- **E/S no bloqueante:** Las operaciones de archivos o red deben usar `aiofiles` o `httpx` (async).
- **Procesamiento en Worker:** Los cálculos de larga duración pertenecen a la capa de worker (`app/worker`).
