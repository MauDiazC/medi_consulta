# Mediconsulta - Architecture Context

## Stack
- FastAPI
- Async SQLAlchemy
- PostgreSQL
- Redis
- Event-driven architecture

## Core Modules
- auth
- patients
- encounters
- notes
- workspace
- timeline

## Clinical Notes Model
- append-only versioning
- active draft
- signed immutable notes
- autosave enabled
- optimistic concurrency
- redis locks
- audit trail

## Realtime
- Redis pub/sub
- SSE streaming
- workspace cache invalidation

## Current State
Autosave + Locks + Events + Streaming AI implemented.

Next Step:
Clinical Diff Viewer + Signed Snapshot PDF


Continuamos Mediconsulta.

Context:
[paste ARCHITECTURE_CONTEXT.md]

Estamos implementando Clinical Diff Viewer y Signed Snapshot.

seguimos contruyendo

Clinical Snapshot + Cryptographic Signature Pipeline

guarda este estado como memoria del proyecto.
Continuamos Mediconsulta.
Carga el estado arquitectónico actual del proyecto.
Seguimos mapeando módulos antes de implementar Snapshot