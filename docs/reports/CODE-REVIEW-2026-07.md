# Production Code Review — 2026-07-07

- **Scope:** full codebase (backend `app/` ~7.4k LOC, frontend `src/`, infra, docs design record) against architecture, correctness, code quality, performance, security, concurrency, testing, API design, documentation, and IEC 62304 regulatory criteria.
- **Method:** graph-assisted exploration (graphify), line-level verification of every candidate finding, cross-check against the prior phase 0–7 audit (`docs/implementation-plan/AUDIT-LEDGER.md`) and remediation tasks TASK-116..134.
- **Reviewer:** Claude (Software Architect / Security Reviewer / QA Engineer role), session `audit/fable-review`.
- **Outcome:** 15 confirmed findings → 14 new remediation tasks (TASK-135..148); 6 known gaps already tracked by existing tasks (pointers below); 3 candidates refuted; 1 verification-process integrity finding.

Severity scale: Critical = exploitable/patient-safety impact now · High = must fix before release · Medium = fix before release recommended · Low = hygiene/hardening.

**No Critical findings.** Core security posture is strong: Argon2id + dummy-hash timing parity, opaque Redis sessions with absolute+idle expiry, deny-by-default authz with audited decisions, double-submit CSRF, security headers/CSP, SSE-AES256 object storage, field-level AES-GCM for clinical text, append-only audit enforced by migration, no raw SQL, zero TODO/FIXME debt, ~490 backend tests with real integration suites.

## Confirmed findings

| # | Sev | Area | Finding | Evidence | Task |
|---|-----|------|---------|----------|------|
| A | **High** | Security/Perf | Attachment upload buffers entire body in RAM before size check; download loads full object then re-chunks from memory | `api/routers/attachments.py` (`await file.read()` → `svc.store()` len check; `svc.open()` returns `bytes`) | TASK-135 |
| W | **High** | Regulatory | No ISO 14971 risk register; only arc42 prose (`docs/design/11-risks-and-technical-debt.md`); `docs/risks/` empty | repo inspection | TASK-147 |
| B | Medium | Concurrency/Perf | `async def` deps/handlers do sync Redis/SQLAlchemy/boto3 on the event loop — `get_session`, `get_current_user`, `require()`, `require_module_enabled`, `upload_attachment` | `api/deps.py:44,71,126,198` | TASK-136 |
| D | Medium | Security/Audit | All authz/consent audit records written with `ip=None`; only login/logout/password flows capture source IP (SR-023 gap) | `authz/service.py:71,80` | TASK-137 |
| E | Medium | Privacy | Worker logs emit email addresses via structured `extra` fields, bypassing AuditService scrubbing (NFR-004) | `workers/email_tasks.py:170` | TASK-138 |
| H | Medium | Correctness | Retention sweep leaks DB sessions on per-dataset failure (reassign without close; `finally` closes last only); task declares `max_retries=3` but has no `autoretry_for`/`self.retry` — never retries | `workers/retention_tasks.py:82-92,21-26` | TASK-141 |
| I | Medium | Correctness | Silent `except Exception: pass` (no log) around `.delay()` — dead broker silently drops session-kill propagation and appointment notifications (SR-035) | `identity/lifecycle.py:57`, `appointments/service.py:71` | TASK-141 |
| L | Medium | Security (defense-in-depth) | No route-level role guards — all routes mount for any authenticated user; only nav links role-filtered; backend 403 is sole gate | `frontend/src/app/App.tsx` (AuthenticatedApp) | TASK-142 |
| P | Medium | Correctness | `["myModules"]` query never invalidated after admin module changes — stale DICOM gating until reload | `core/clinical/AttachmentItem.tsx:19` | TASK-144 |
| R | Medium | Correctness | `["me"]` issued from 9 files with inconsistent retry (expired session can 401×3 before redirect); `SessionActivityProvider` hard-codes 15-min expiry seed unreconciled with server TTL | `auth/SessionActivityProvider.tsx`, 9 call sites | TASK-144 |
| T′ | Medium | Testing | Untested security-relevant frontend units: SessionActivityProvider, AttachmentItem, upload path, `csrf.ts` | vitest inventory | TASK-146 |
| F | Medium | Security (hardening) | CSRF exemptions match by `startswith`; `/api/v1/auth/password-reset` and `/api/v1/activation` lack trailing `/` — any future sibling route is silently exempt. No live bypass today | `core/security_middleware.py:53-61,86-88` | TASK-139 |
| G+J | Low | Config/API design | `session_signing_key` required but used nowhere (dead secret, implies signing that doesn't exist); `lockout_svc` optional-`None` parameter shape invites silent brute-force-protection bypass by future callers | `core/config.py:31`, `auth/login.py` | TASK-140 |
| M+N | Low | Code quality | `uploadAttachment` bypasses shared `request()` duplicating RFC 7807 handling (already missing the 401→AuthError branch); hand-written `ProblemError` inside a "generated" file can drift | `api/client.ts:136-160`, `api/generated/types.ts:17` | TASK-143 |
| S | Low | Performance | Zero code splitting — no `React.lazy` anywhere; single bundle will not absorb Cornerstone3D (SR-026 budgets) | `app/App.tsx` static imports | TASK-145 |
| Y | Low | Regulatory | Traceability-matrix remediation table cites dangling `TASK-xxxa` IDs; actual files are TASK-116..134 | `docs/design/traceability-matrix.md` | TASK-148 |

## Verification-process integrity note (regulatory weight)

**TASK-125** ("attachment upload via multipart streaming, remediation") is recorded **Completed**
with checked acceptance criteria, yet the streaming objective is demonstrably unmet (finding A:
full-body `await file.read()` remains). This repeats the failure mode the phase 0–7 audit itself
documented (tasks marked Completed with unmet criteria). Under IEC 62304 §5.7 the verification
record is unreliable evidence. Recommendation: when TASK-135 closes, annotate the AUDIT-LEDGER
verdict for TASK-125, and tighten the DoD convention so "Completed" requires the verifying test to
be named in the task file.

## Known gaps already tracked (no new tasks — schedule, don't duplicate)

| Gap | Tracked by | Status |
|-----|-----------|--------|
| SR-024 erasure re-keying into anonymized dataset (GDPR) | TASK-116 | **open — only unfinished remediation** |
| Requirement→test traceability (matrix test column empty; no test-spec records in `tests-specifications/`) | TASK-114 | draft, not started |
| E2E tests (none exist) + integration test tail | TASK-110/111 | draft |
| Performance validation vs budgets | TASK-112 | draft |
| Security review incl. residuals below | TASK-113 | draft |
| Frontend module registry unimplemented (`modules/index.ts` empty; `appendItems` orphan) + DICOM frontend | TASK-100..103 | draft |
| Deploy/run docs, first-sysadmin bootstrap; `docs/releases/` + `system-requirements/regulatory/` empty | TASK-115 | draft |

**Checklist items to fold into TASK-113 (security review):** verify admin `list_all()` path
(`appointments/service.py:166`) applies the non-clinical projection; run the CSRF exempt-prefix ×
route-inventory audit (pre-work for TASK-139); confirm reverse-proxy `X-Forwarded-For` trust chain
(pre-work for TASK-137).

## Refuted / downgraded candidates (recorded so they aren't re-raised)

- **Env driver mismatch** — refuted: `infra/.env.example:14` uses sync `postgresql://`; only the untracked local `backend/.env` had `+asyncpg`. Operator note only.
- **Consent query-key mismatch** — refuted: `ConsentPage.tsx:12` reads `["me","consents"]`, matching both mutations' invalidation.
- **Authz list-actions allow-all (broken object-level authz)** — largely refuted: repositories scope rows (`list_for_doctor`/`list_for_patient`); service routes by role. Residual admin-projection check → TASK-113.
- **Lockout not wired** — already fixed by TASK-118; only the optional-parameter shape remains (TASK-140).

## Positive observations

- Clean layering (routers → services → repositories → models); plugin/module system matches ADR-0005; no god files (max ~340 lines, migrations aside).
- RFC 7807 uniformly implemented server-side and parsed client-side; OpenAPI contract enforced in CI.
- Config posture: all secrets required, `SecretStr`, secure cookie defaults, no insecure fallbacks.
- Documentation quality well above typical: full arc42 set, 13 ADRs, per-requirement records with approval status, honest audit ledger.

## Remediation plan

See `docs/implementation-plan/remediation-plan-review-2026-07.md` for severity/effort/dependency-ordered phases R0–R4.
