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
