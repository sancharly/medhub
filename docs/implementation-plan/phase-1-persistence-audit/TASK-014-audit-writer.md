# TASK-014 — Append-only AuditService

- **Phase:** 1 — Persistence & audit
- **Software item / unit:** SI-AUDIT / U-AUD-Writer
- **Implements:** SR-023
- **Depends on:** TASK-012 (must be merged first)
- **Branch:** `feature/audit-writer`
- **Status:** In Progress (audit 2026-06-29)

## Objective

Implement the central, append-only `AuditService` that records security-relevant events — authentication, clinical-data access, consent changes, administrative actions — with actor, action, target, outcome, IP, and timestamp, never storing plaintext credentials and not modifiable by ordinary users (SR-023). Every security-relevant operation in later items calls this single service so accountability and breach-investigation evidence are produced uniformly (§8.4).

## Interfaces to honor

- Provides the exact `AuditService` interface from [12-interfaces.md](../../design/12-interfaces.md):

  ```python
  class AuditService:
      def record(self, actor, action, target, outcome, ip) -> None: ...  # append-only (SR-023)
  ```

  Consumed by all security-relevant items; it is a side effect of operations, **not** a public HTTP endpoint (api-design.md note; §8.4).
- Writes only via the insert-only `audit_repo` (TASK-012) — append-only; the model/repository expose no update or delete path (consistent with TASK-010 AuditLog having no update path).
- Must **not** accept, store, or log plaintext credentials or unnecessary clinical content (SR-023.5); must **not** offer modification of existing entries; must **not** make authorization decisions (callers are already authorized).

## Implementation detail

- Files to create under `backend/app/audit/`:
  - `service.py` — `AuditService.record(actor, action, target, outcome, ip)`:
    - `actor`: account id (nullable for pre-auth failures, e.g. failed login of unknown user — SR-023.1).
    - `action`: stable string (e.g. `AUTH_LOGIN`, `CLINICAL_ACCESS`, `CONSENT_GRANT`, `CONSENT_REVOKE`, `ACCOUNT_CREATE`, `USER_TYPE_CHANGE`, `GROUP_MODULE_CHANGE`).
    - `target`: `(target_type, target_id)` (e.g. patient id for clinical access — SR-023.2).
    - `outcome`: `SUCCESS|FAILURE`; `ip`: source address; `timestamp`: server time, set by the service (not the caller).
    - Persists one immutable `AuditLog` row via `audit_repo.add`. Defensive scrub: rejects/strips any field that looks like a credential (e.g. a `password` key) so credentials never reach the log (SR-023.5).
  - `actions.py` — enum/constants of allowed action strings (so callers in later phases reference a fixed catalog; supports SR-023.1–4 event categories).
  - `deps.py` — FastAPI DI provider yielding an `AuditService` bound to the request DB session.
- Libraries (exact stack): SQLAlchemy 2.x (via repository), Pydantic v2 for the input value object.
- Config keys: none beyond DB.
- Error cases: an audit write must not silently swallow failures for security events; on write failure the security-relevant operation is treated as failed/rolled back per caller policy (documented for consumers). The service itself raises on persistence failure rather than returning success.

## Tests (write first — TDD, CLAUDE.md §4)

- `backend/tests/audit/test_audit_writer.py` (ephemeral PostgreSQL):
  - **SR-023.1**: a recorded auth attempt (success and failure) stores actor (nullable) and timestamp.
  - **SR-023.2**: a clinical-data-access event stores actor, target patient, timestamp.
  - **SR-023.3**: consent grant/revoke events store actor, target, timestamp.
  - **SR-023.4**: administrative actions (e.g. user-type change, group/module management) are recorded.
  - **SR-023.5 (immutability)**: there is no API to update or delete an existing audit row; attempting an update via the repository/service is unavailable/raises (append-only).
  - **SR-023.5 (no credentials)**: passing a payload containing a password-like field results in a stored row with no plaintext credential.
  - `timestamp` is server-assigned, not caller-supplied.
- Each test references its SR-023 criterion.

## Acceptance criteria

Distilled from SR-023:

- [ ] Authentication attempts (success and failure) are recorded with actor and timestamp (SR-023.1).
- [ ] Clinical-data access is recorded with actor, target patient, and timestamp (SR-023.2).
- [ ] Consent grant/revoke actions are recorded with actor, target, and timestamp (SR-023.3).
- [ ] Administrative actions (user-type change, group/module management) are recorded (SR-023.4).
- [ ] Audit entries are append-only — not modifiable or deletable by ordinary users / via any service path (SR-023.5).
- [ ] No plaintext credentials (or unnecessary clinical content) are stored in the audit log (SR-023.5).
- [ ] `record(actor, action, target, outcome, ip)` matches the 12-interfaces contract; audit is a side effect, not a public endpoint.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`/`mypy`)
- [ ] Unit/integration tests pass; coverage target met
- [ ] OpenAPI regenerated and re-linted (N/A — no public endpoint)
- [ ] Audit events emitted for security-relevant actions — this task **is** the writer; later items wire calls to it (SR-023)
- [ ] Traceability matrix row updated (SR-023 → TASK-014 → audit-writer tests)
- [ ] Security review completed (N/A — no auth/session code here; the writer is consumed by auth tasks under SR-031.6)

## Audit verdict (2026-06-29)

- **Verdict:** PARTIAL
- Reviewed against code + tests + runtime smoke; see `docs/implementation-plan/AUDIT-LEDGER.md`.
- **Remediation:** AUDIT-FINDINGS.md (record() signature; DB append-only). Unchecked acceptance-criteria / DoD items above reflect the gaps the audit found; this task stays **In Progress** until they are addressed.
