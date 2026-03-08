# Plan de Acción: Seguridad y Cumplimiento

Este runbook describe las tareas para asegurar los datos clínicos y cumplir con estándares de seguridad de nivel empresarial.

## Fase 1: Auditoría de Secretos y Dependencias
- [ ] **Gitleaks / TruffleHog:** Configurar una herramienta para detectar secretos en el historial de Git.
- [ ] **Snyk / Safety:** Escanear todas las dependencias en `pyproject.toml` en busca de vulnerabilidades conocidas.
- [ ] **Docker Scanning:** Escanear las imágenes base en busca de fallos de seguridad en el SO.

## Fase 2: Control de Acceso (RBAC)
- [ ] **Políticas Granulares:** Revisar y refinar `app/core/permissions.py` para asegurar que cada acción esté validada por el rol del usuario y la organización.
- [ ] **Manejo de JWT:** Implementar rotación de tokens y una "blacklist" en Redis para tokens revocados (Logout efectivo).
- [ ] **Rate Limiting:** Implementar límites de peticiones por IP y por usuario para mitigar ataques de fuerza bruta.

## Fase 3: Integridad de Datos Clínicos
- [ ] **Encryption at Rest:** Validar que la base de datos y los archivos en S3 estén cifrados.
- [ ] **Firmas Digitales:** Reforzar el pipeline de `app/modules/notes/signing` para asegurar que la firma sea inalterable.
- [ ] **Trail de Auditoría Clínico:** Completar la implementación de logs de auditoría para cada lectura o escritura de datos sensibles.
