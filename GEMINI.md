# Mediconsulta Architecture Governance (v1)

This project follows a STRICT enterprise architecture. All modifications MUST comply with these rules.

## ARCHITECTURE GOVERNANCE (NON-NEGOTIABLE)

**Architecture Type:**
- Modular Domain Architecture
- Workspace-driven clinical model
- Event-driven backend
- Async-first system

The architecture is already frozen. No redesigns allowed.

---

## FOLDER OWNERSHIP RULES

Allowed top-level folders:
- `app/core` → cross-cutting infrastructure ONLY
- `app/modules` → ALL business/domain logic
- `app/worker` → background processing
- `app/cli` → operational tooling

**Forbidden global layers:**
- ❌ `app/services`
- ❌ `app/models`
- ❌ `app/utils`
- ❌ `app/api`
- ❌ shared domain folders

If functionality belongs to a domain, it MUST live inside that domain module (e.g., `app/modules/notes/signing`).

---

## DOMAIN BOUNDARIES

Each module is a bounded context.

**A module MAY contain:**
- `router.py`, `service.py`, `repository.py`, `schemas.py`, internal utils, internal models.

**A module MUST NOT:**
- Access another module's database tables directly.
- Bypass services via repositories.
- Introduce cross-module coupling.

Communication between modules must happen through services, events, or explicit interfaces.

---

## DATABASE RULES

- Async SQLAlchemy ONLY.
- No synchronous DB access.
- **Repositories:** CRUD / persistence only. Business logic NEVER lives here.
- **Services:** Business decisions and orchestration only.
- **Routers:** Transport layer only. NEVER execute SQL.

---

## WORKSPACE MODEL (CRITICAL)

- Workspace represents runtime clinical state and is **MUTABLE**.
- Snapshots are **IMMUTABLE**.
- Signing a note means: FREEZE workspace clinical state → create snapshot.
- AI MUST NEVER: Store workspace state as legal record, bypass snapshot creation, or mutate signed notes.

---

## CLINICAL NOTE RULES

- Append-only versioned.
- Optimistic concurrency controlled.
- Draft until signed; immutable after signing.
- Signing belongs ONLY to `app/modules/notes/signing`.

---

## CRYPTOGRAPHY RULES

- Operations MUST remain inside `notes/signing`.
- MUST be deterministic and use canonical JSON.
- MUST hash before signing.
- MUST NOT run blocking operations in request path unless explicitly required.

---

## EVENT SYSTEM RULES

- System is event-driven.
- Changes affecting workspace MUST publish events.
- AI MUST NOT: Introduce polling, shared in-memory state, or bypass Redis event flow.

---

## IMPORT RULES

- Use **absolute imports ONLY** (e.g., `from app.modules.notes.service import ...`).
- ❌ No relative imports across modules.

---

## ASYNC SAFETY

- No blocking IO or sync filesystem operations.
- CPU-heavy work belongs to workers.

---

## REFACTOR SAFETY

- ❌ NO reorganizing folders, renaming modules, or introducing new architecture layers.
- ❌ NO automatic Clean Architecture or DTO abstraction layers.
- Refactors require explicit user approval.

---

## CODE STYLE EXPECTATIONS

- Explicit dependency injection.
- Small services, deterministic behavior, predictable side effects.
- Clarity over cleverness. No magic abstractions or hidden globals.

---

# SESSION LOG & PROJECT STATUS (2026-04-17)

## ✅ AVANCES REALIZADOS
1.  **Clinical Safety Watcher (AI):** Upgrade del `CopilotAnalyzer` usando Gemini para detectar Red Flags y Omisiones Críticas sin interferir en el diagnóstico médico.
2.  **SaaS Deep Audit Trail:** Implementación de auditoría de acceso en segundo plano que rastrea IP, User-Agent y `organization_id` de forma inmutable.
3.  **Atomic Onboarding:** Nuevo endpoint `POST /auth/register-saas` que crea Organización + Admin en un solo paso atómico.
4.  **Multi-tenancy Hardening:** Blindaje total de los repositorios de `notes`, `patients` y `organizations` con validación estricta de `organization_id` y casting de UUID para PostgreSQL.
5.  **Enriched Auth Response:** Login y Registro ahora devuelven metadatos completos (`user_id`, `org_id`, `role`, `email`) para facilitar el Frontend.
6.  **SaaS Lifecycle (CRUD):** Implementación completa de flujos de Activación/Desactivación para Usuarios, Pacientes y Organizaciones.
7.  **DevOps & Infra:** 
    *   Sincronización de puerto dinámico ($PORT) en Dockerfile y `railway.toml` (Fix Error 502).
    *   Unificación de cabezas de Alembic y corrección de migraciones.
    *   Herramientas de desarrollo: Comando CLI y Endpoint de purga (`purge-dev`).
8.  **Seguridad Clínica:** Restricción de endpoints de IA exclusivamente al rol de `doctor`.

## 🛠 ESTADO ACTUAL
- **Railway:** Desplegado y Operacional.
- **Base de Datos:** Migrada y saneada (unificada a `is_active`).
- **Endpoints Verificados:** Health, Auth, Organizations, Users, Patients.

## 🚀 PUNTO DE PARTIDA PARA MAÑANA
- Iniciar con el registro del primer **Encounter** (Encuentro Clínico).
- Probar el flujo de escritura de notas con **Autosave** y **Locking**.
- Verificar la **Firma Digital** y el **Backup Inmutable**.
- Explorar el módulo de **Appointments** (Citas).
