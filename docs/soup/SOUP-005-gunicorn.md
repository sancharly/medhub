---
id: SOUP-005
type: soup
title: Gunicorn
status: in_review
version: "1.1"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-10-22"
manufacturer: Benoit Chesneau
soup_version: 26.0.0
anomaly_review: "2026-10-22"
links: []
tags:
  - soup
  - layer:backend
  - class:B
---

# SOUP-005 — Gunicorn 26.0.0

## Functional and performance requirements

Production process manager supervising Uvicorn workers.

## Required hardware and software environment

Python 3.12; Linux (POSIX process model).

## Anomaly list review

**Reviewed 2026-10-22** (TASK-154, CR-001 AC-11) for Gunicorn 26.0.0, the version `backend/uv.lock` resolves, with packaging 26.2. Published information only: nothing was
fetched from or run out of the component's repository.

`anomaly_source`: OSV.dev; GitHub Advisory Database and https://github.com/benoitc/gunicorn/security/advisories; NVD; https://gunicorn.org/2026-news/ and https://gunicorn.org/reference/settings/

### Sources checked

- OSV.dev, PyPI ecosystem — `POST https://api.osv.dev/v1/query` with the exact version (https://osv.dev): `gunicorn` 26.0.0, `packaging` 26.2.
- GitHub Advisory Database — `GET https://api.github.com/advisories?ecosystem=pip&affects=<package>@<version>` (https://github.com/advisories): `gunicorn@26.0.0`.
- Gunicorn repository advisories — https://github.com/benoitc/gunicorn/security/advisories.
- NVD keyword search — `https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch=<keyword>` (https://nvd.nist.gov/vuln/search): keyword `gunicorn`.
- Changelog — https://gunicorn.org/2026-news/ (26.0.0, 2026-05-05) and the GitHub release notes of the later releases, 26.1.0 (2026-08-18) and 26.2.0 (2026-08-24): https://github.com/benoitc/gunicorn/releases. There is no 26.0.x patch.
- Settings reference — https://gunicorn.org/reference/settings/ (`control_socket`, `control_socket_disable`).

### Findings

No security advisory for 26.0.0 in OSV, the GitHub Advisory Database, the repository or NVD
(NVD's `gunicorn` matches are other products). Published behaviour and bugs that apply to 26.0.0:

| Item | Source | Fixed in | MedHub affected? |
|---|---|---|---|
| Control socket on by default: `control_socket_disable` defaults to `False`; the socket goes to `$XDG_RUNTIME_DIR/gunicorn.ctl`, else `$HOME/.gunicorn/gunicorn.ctl` (since 25.1.0) | Settings reference | Behaviour, not a defect | Yes: the service user has no home, so the control server fails at every start. Already open as **PRB-041** (minor); not a new escalation |
| Control socket leaks a thread, selector fd and socket per worker on each SIGHUP reload (#3648) | 26.1.0 notes | 26.1.0 | No: MedHub does not reload by SIGHUP, and the control server does not start (PRB-041). PRB-041's proposed `--no-control-socket` removes it |
| Children reparented to gunicorn as PID 1 are reaped as workers; one exiting with code 3 or 4 halts the server (#3220) | 26.1.0 notes | 26.1.0 | Applies in principle: `exec gunicorn` makes it PID 1 in the backend container and Compose sets no `init`. Triggered only by an orphaned process; the backend starts no subprocesses and the healthcheck's `python -c` does not fork. Availability only |
| HTTP parser fixes: truncated chunked bodies accepted, duplicate `Host`/`Content-Type` accepted (26.1.0); HTTP/2 header policy and `Upgrade` bodies dropped on the ASGI worker (26.2.0) | 26.1.0 / 26.2.0 notes | 26.1.0 / 26.2.0 | No: these are Gunicorn's own sync/gthread/asgi workers and parser. MedHub uses `UvicornWorker`, where Uvicorn parses HTTP; HTTP/2 is off |

`packaging` 26.2: none found.

### MedHub use and judgement

Gunicorn only supervises the Uvicorn workers (`backend/entrypoint.sh`); it parses no requests. The
control-socket failure is PRB-041 (open, minor). Its effect on log monitoring, which RISK-007
relies on, is evaluated there. The PID-1 reaping bug can at worst stop the API (availability,
RISK-007: covered by `restart: unless-stopped` and the healthcheck), and MedHub's container gives
it no trigger. Nothing here is hazard-relevant and no MedHub behaviour beyond PRB-041 is affected:
no new RISK or PRB. When PRB-041 is fixed, its CR can also consider `init: true` for the backend
service. Moving to 26.1.0 or later is a separate CR (CR-001 A-4).

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 26.0.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no advisory for 26.0.0; control socket on by default and failing in MedHub's image (PRB-041, already open); later-fixed process-manager and parser bugs judged; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
