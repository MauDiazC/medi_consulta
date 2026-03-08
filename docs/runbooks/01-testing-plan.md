# Plan de Acción: Estrategia de Pruebas (Testing)

Este runbook detalla los pasos para alcanzar una cobertura robusta y asegurar la integridad clínica de Mediconsulta.

## Fase 1: Pruebas Unitarias (Cobertura > 90%)
- [x] **Configuración de Pytest:** Instalar y configurar `pytest`, `pytest-asyncio` y `pytest-cov`.
- [x] **Mocks de Repositorios:** Crear fixtures para mockear los repositorios y probar la lógica de los `service.py` de forma aislada.
- [x] **Pruebas de Reglas de Negocio:** Validar estados de Workspace, validaciones de firma y transiciones de notas. (Completado para módulos Core: Auth, Encounters, Notes, Patients, Organizations, Users).

## Fase 2: Pruebas de Integración (Base de Datos Real)
- [ ] **DB de Test efímera:** Configurar un archivo `conftest.py` que levante una base de datos PostgreSQL temporal (o en Docker) para los tests.
- [ ] **Flujos Router -> Service -> DB:** Validar que los endpoints responden correctamente y que los datos se persisten siguiendo las reglas de la arquitectura.
- [ ] **Pruebas de Eventos:** Verificar que las acciones en los servicios publican los eventos correctos en Redis.

## Fase 3: Pruebas de Carga y E2E
- [ ] **Escenarios Críticos:** Crear scripts que simulen el flujo completo: `Crear Encuentro -> Iniciar Dictado -> Generar Nota -> Firmar Nota`.
- [ ] **Pruebas de Concurrencia:** Validar que los bloqueos de Redis funcionan bajo estrés (ej: dos usuarios intentando editar el mismo Workspace).
