# MedHub implementation plan

The plan itself is no longer a set of files here: since the MedTrace migration every task is a
`task` design record in [`../design-outputs/tasks/`](../design-outputs/tasks/), one file per task,
with its traceability in the frontmatter (`implements` → SR, `relates_to` → the tasks it depends
on). The old `phase-*/` folders and the task index that listed them are gone — the records are the
index, and [`../reports/`](../reports/) holds the generated traceability and gap reports.

- **Task template:** [`../templates/task.md`](../templates/task.md) — the stack, repo layout, TDD
  rule, deny-by-default authorization, RFC 7807 errors and audit conventions apply to every task
  and are not repeated per record.
- **Process:** the [software development plan](../software-development-plan.md), which runs the
  IEC 62304 stage overlay (`medical-records:iec62304-sdlc`) declared in
  [`../../CLAUDE.md`](../../CLAUDE.md).
- **Architecture sources:** building blocks (05), runtime views (06), deployment (07), cross-cutting
  concepts (08), interfaces (12) and the ADRs in [`../design/`](../design/), plus API design and
  FHIR mapping in [`../specifications/`](../specifications/).

## How to execute a task

1. Pick the lowest-numbered `draft` task whose dependencies are approved.
2. Create its branch, write tests first, implement, satisfy the Definition of Done.
3. Move the record `draft → in_review` and hand it to the `qa-engineer` agent. Only QA sets
   `approved`.
4. Run `traceability-check` before approval: zero errors is the gate.

## Phase tags

Phases survive as the `phase:` tag on each record, following the architecture's dependency tiers:
backend foundation → security/identity → domain services → API → module host and DICOM backend,
then frontend foundation → core views → module system and DICOM viewer, then integration, system
testing and compliance hardening.

| Tag | Theme |
|---|---|
| `phase:0-foundation-toolchain` | Repo, toolchain, app skeletons, Docker Compose, CI |
| `phase:1-persistence-audit` | Models, migrations, repositories, crypto, audit |
| `phase:2-auth-session-authorization-identity` | Password, session, login/lockout, authz, consent, identity, worker base |
| `phase:3-domain-services` | Groups, clinical entries, attachments, appointments, consent linkage |
| `phase:4-api-layer` | Routers and DTOs per resource, OpenAPI, security middleware |
| `phase:5-module-host-dicom-backend` | Plugin host, PlatformServices, router mount, DICOM backend |
| `phase:6-frontend-foundation` | API client, layout, nav, auth UI |
| `phase:7-frontend-core-views` | Profile, patients, clinical, appointments, consent, admin |
| `phase:8-frontend-module-system-dicom` | Frontend module registry, DICOM viewer |
| `phase:9-integration-system-testing-compliance` | Integration, E2E, performance and security tests, traceability, deploy docs |
| `phase:review-2026-07` | Remediation of the 2026-07 code review |
| `phase:ui-enhancement` | Design system, theming and screen tokenization |

## Audit and review history

- [AUDIT-FINDINGS.md](AUDIT-FINDINGS.md) and [AUDIT-LEDGER.md](AUDIT-LEDGER.md) — the phase 0–7 audit.
- [SMOKE-RESULTS.md](SMOKE-RESULTS.md) — smoke-test run behind that audit.
- [remediation-plan-review-2026-07.md](remediation-plan-review-2026-07.md) — how the 2026-07 review
  findings were turned into tasks.

Open defects from those documents are tracked as problem reports in
[`../problem-reports/`](../problem-reports/) under IEC 62304 §9; the documents themselves stay as
the historical record.
