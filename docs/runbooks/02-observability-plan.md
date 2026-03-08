# Plan de Acción: Observabilidad y Monitoreo

Este runbook detalla los pasos para asegurar que el sistema sea monitoreable y que podamos detectar y depurar problemas rápidamente.

## Fase 1: Implementación de Trazabilidad (Tracing)
- [ ] **OpenTelemetry (OTEL):** Integrar el SDK de OTEL en FastAPI.
- [ ] **Context Propagation:** Asegurar que el ID de traza pase del API al Worker para seguir el flujo de los eventos.
- [ ] **Jaeger / Honeycomb:** Configurar un exportador de trazas para visualizar los cuellos de botella.

## Fase 2: Métricas del Sistema (Metrics)
- [ ] **Prometheus Metrics:** Exponer un endpoint `/metrics` que reporte el tiempo de respuesta, cantidad de errores por tipo y carga de la DB.
- [ ] **Redis Monitoring:** Monitorear la longitud de las colas de eventos y el uso de memoria de Redis.
- [ ] **DB Performance:** Registrar queries lentas a nivel de SQLAlchemy.

## Fase 3: Logging y Alertas
- [ ] **Structured Logging:** Asegurar que todos los logs sean en formato JSON para facilitar su búsqueda en sistemas como ELK o Datadog.
- [ ] **Grafana Dashboards:** Crear un tablero visual que unifique trazas y métricas.
- [ ] **Alertas en Slack / Discord:** Configurar notificaciones críticas para errores de firma o fallos en el sistema de eventos.
