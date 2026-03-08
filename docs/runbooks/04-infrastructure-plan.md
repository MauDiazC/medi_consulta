# Plan de Acción: Infraestructura y CI/CD

Este runbook describe las tareas para automatizar la calidad de código y asegurar un despliegue confiable en producción.

## Fase 1: Calidad de Código Local
- [ ] **Pre-commit Hooks:** Configurar `ruff` (linter/formatter), `mypy` (tipado estático) e `isort`.
- [ ] **Ruff Rules:** Definir un conjunto de reglas de estilo estrictas para mantener la consistencia del código.
- [ ] **Pyproject.toml:** Asegurar que todas las herramientas de calidad estén configuradas correctamente en el archivo raíz.

## Fase 2: Automatización en GitHub Actions
- [ ] **Linter Pipeline:** Ejecutar `ruff` y `mypy` en cada commit y bloquear el merge si hay errores.
- [ ] **Test Pipeline:** Ejecutar todos los tests (unitarios e integración) en cada Pull Request.
- [ ] **Build Pipeline:** Automatizar la creación de la imagen Docker y su subida a un registro de contenedores (ej: Docker Hub, GHCR).

## Fase 3: Despliegue Continuo (CD)
- [ ] **Infrastructure as Code (IaC):** Definir la infraestructura (EKS, RDS, Redis) usando Terraform o similar.
- [ ] **Deployment Workflow:** Configurar un flujo que actualice los servicios en Staging/Producción automáticamente tras aprobar un PR.
- [ ] **Database Migrations:** Automatizar la ejecución de `alembic upgrade head` durante el despliegue para evitar discrepancias de esquema.
