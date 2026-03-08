# Estándares de Ingeniería y Seguridad

## Estándares de Calidad de Código
- **Inyección de Dependencias Explícita:** Los servicios y repositorios DEBEN ser inyectados.
- **Servicios Pequeños:** La lógica debe descomponerse en funciones pequeñas de responsabilidad única.
- **Efectos Secundarios Predecibles:** Los eventos y cambios en la DB deben estar claramente documentados en los métodos del servicio.
- **Calidad Automatizada:** Uso de `ruff` para linting, `mypy` para tipado y `pytest` para validación lógica.

## Seguridad y Criptografía
Las operaciones en `app/modules/notes/signing` deben seguir estas reglas:
- **JSON Canónico:** Los payloads deben canonicalizarse antes del hashing para asegurar resultados deterministas.
- **Hashing:** Payload → Hash SHA-256.
- **Firma:** Hash → Firma con Llave Privada RSA/ECDSA.
- **Trail de Auditoría:** Cada cambio genera una entrada encadenada criptográficamente (`app/core/audit.py`).

## Seguridad Clínica
- **Aislamiento Multitenant:** Cada consulta DEBE filtrar por `organization_id`.
- **Integridad de Datos:** No se eliminan notas clínicas; solo se inactivan o se crean nuevas versiones.
- **Validación de Configuración:** El sistema no arranca si faltan variables críticas (Dynaconf Validators).
