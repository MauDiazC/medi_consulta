# Patrones de API y Endpoints

## Responsabilidad del Router
Los routers son capas delgadas de transporte.
- **Reglas:** Sin ejecución de SQL, sin lógica de negocio directa.
- **Flujo:** Parsear petición → Validar esquemas → Inyectar servicios → Retornar respuesta.

## Endpoints en Tiempo Real (SSE y WebSockets)
- **Actualizaciones por Streaming:** Uso de `Server-Sent Events` (SSE) para actualizaciones clínicas continuas.
- **IA y Dictado:** Utilizan respuestas por streaming para retroalimentación inmediata.
- **Invalidación de Workspace:** Los mensajes de invalidación de estado del cliente se envían a través de canales SSE específicos.

## Patrones de Concurrencia
- **Bloqueo Optimista:** Gestionado en la capa de servicio usando campos de versión.
- **Bloqueos Distribuidos (Redis):** Utilizados para prevenir condiciones de carrera durante actualizaciones clínicas sensibles (ej: firma de una nota).
- **Control de Tráfico (Rate Limiting):** Implementado vía Redis para proteger endpoints sensibles (Auth, IA) contra abusos.

## Paginación y Búsqueda
- Uso obligatorio de la utilidad de paginación estandarizada en `app/core/pagination.py`.
- Las consultas de búsqueda tienen alcance de módulo y son manejadas por los repositorios.
