# Mediconsulta Clinical Safety & Legal Invariants

This document defines the STRICT invariants for managing legal medical records within Mediconsulta. Any violation of these rules constitutes a **Clinical Integrity Risk**.

## CORE INVARIANTS

1.  **Immutability of Signed Notes:** Once a clinical note is signed, it is IMMUTABLE. No modifications are allowed.
2.  **Append-Only Versioning:** Clinical notes must be versioned. Updates create new versions; history must be preserved for auditability.
3.  **No Silent Overwrites:** Data must never be overwritten without explicit versioning or tracking.
4.  **Optimistic Concurrency:** All updates to clinical notes MUST respect optimistic concurrency tokens to prevent "lost updates" in a multi-user environment.
5.  **State Freezing:** Signing a note MUST freeze the clinical state of the workspace into a permanent snapshot.
6.  **Workspace vs. Legal Record:** The active Workspace is a runtime state for draft/collaboration; only the signed Snapshot constitutes the legal record.
7.  **Canonical JSON Snapshots:** Snapshots must be generated from canonical JSON to ensure consistency across different platforms and versions.
8.  **Deterministic Hashing:** The hashing process for signing must be strictly deterministic.
9.  **Independent Verification:** Signatures must be verifiable independently of the active system (using public keys/certificates).
10. **Atomic Signing Flows:** No partial or "multi-step" signing flows that leave the note in an intermediate state are allowed.

---

## PROHIBITED ACTIONS (REJECT CRITERIA)

The Architecture Review Board MUST reject any code that:
-   **Mutates signed notes:** Any attempt to update a record with a `signed` status.
-   **Edits without locks:** Bypassing the clinical locking semantics required for concurrent editing.
-   **Skips audit logging:** Any clinical state change that does not produce an audit trail.
-   **Skips event publication:** Failing to notify the system of workspace changes via the event bus.
-   **Skips concurrency checks:** Updating notes without validating the version/ETag.
-   **Invalidates Author Identity:** Allowing signing without strict validation of the practitioner's identity and permissions.

---

## RISK ASSESSMENT

If a proposal introduces risk to these invariants, the response must be:
**"Clinical Integrity Risk."**

Followed by an explanation of the legal impact (e.g., "This change breaks the chain of custody," "This allows repudiation of medical records").

**Correctness > Performance.**
**Legal Integrity > Developer Convenience.**
