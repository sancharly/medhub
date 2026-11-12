---
id: SOUP-005
type: soup
title: Gunicorn
status: in_review
version: "1.3"
author: Carlos Santiago Liceras
created: "2026-10-21"
updated: "2026-11-13"
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

Relied-on configuration: the control socket is **disabled** by `--no-control-socket` (setting
`control_socket_disable`) in the backend image `CMD` (PRB-041, TASK-214). MedHub does not use the
`gunicornc` management interface (worker status, graceful reload). Reload (`HUP`) and shutdown
(`TERM`) by signal are unaffected: the flag only skips starting the control server. Without the flag the control
server fails at every start because the service user has no home (`Errno 13`), logging an ERROR.

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
| Control socket on by default: `control_socket_disable` defaults to `False`; the socket goes to `$XDG_RUNTIME_DIR/gunicorn.ctl`, else `$HOME/.gunicorn/gunicorn.ctl` (since 25.1.0) | Settings reference | Behaviour, not a defect | Yes: the service user has no home, so the control server fails at every start. Was open as **PRB-041** (minor); disabled by configuration since TASK-214 (`--no-control-socket`, see Functional requirements); not a new escalation |
| Control socket leaks a thread, selector fd and socket per worker on each SIGHUP reload (#3648) | 26.1.0 notes | 26.1.0 | No: MedHub does not reload by SIGHUP, and the control server does not start (PRB-041); with `--no-control-socket` (TASK-214) it is never created |
| Children reparented to gunicorn as PID 1 are reaped as workers; one exiting with code 3 or 4 halts the server (#3220) | 26.1.0 notes | 26.1.0 | Applies in principle: `exec gunicorn` makes it PID 1 in the backend container and Compose sets no `init`. Triggered only by an orphaned process; the backend starts no subprocesses and the healthcheck's `python -c` does not fork. Availability only |
| HTTP parser fixes: truncated chunked bodies accepted, duplicate `Host`/`Content-Type` accepted (26.1.0); HTTP/2 header policy and `Upgrade` bodies dropped on the ASGI worker (26.2.0) | 26.1.0 / 26.2.0 notes | 26.1.0 / 26.2.0 | No: these are Gunicorn's own sync/gthread/asgi workers and parser. MedHub uses `UvicornWorker`, where Uvicorn parses HTTP; HTTP/2 is off |

`packaging` 26.2: none found.

### MedHub use and judgement

Gunicorn only supervises the Uvicorn workers (the backend image `CMD`, `backend/Dockerfile`); it
parses no requests. The control-socket failure was PRB-041 (minor), disabled by configuration since
TASK-214. Its effect on log monitoring, which RISK-007 relies on, is evaluated there. The PID-1 reaping bug can at worst stop the API (availability,
RISK-007: covered by `restart: unless-stopped` and the healthcheck), and MedHub's container gives
it no trigger. Nothing here is hazard-relevant and no MedHub behaviour beyond PRB-041 is affected:
no new RISK or PRB. `init: true` for the backend service was considered and not adopted (CR-005
Q-3). Moving to 26.1.0 or later is a separate CR (CR-001 A-4).

## Forwarded-header handling (CR-004, TASK-185)

MedHub relies on Gunicorn's `forwarded_allow_ips` being **empty**. The default is `127.0.0.1,::1`
(or `$FORWARDED_ALLOW_IPS`), and `UvicornWorker` passes it to Uvicorn's proxy-headers handling, which
would rewrite `request.client` for those peers. the backend image `CMD` (`backend/Dockerfile`) starts Gunicorn with
`--forwarded-allow-ips=` (empty): the setting parses to an empty list, so no peer is trusted and
`request.client` is always the TCP peer. The application applies the one trusted-proxy rule of
SR-042 itself (`backend/app/core/client_address.py`, ADR-0019). Verified for 26.0.0 on the started
stack (TS-016 TC-016.3: `request.client.host` is the proxy's address while the originating address
is the caller's). A version that changes how an empty value is parsed needs the check repeated.

## Monitoring

Per [PLAN-002](../plans/PLAN-002-maintenance-plan.md): reviewed at every dependency change, before
every release and at most 365 days apart, by the Software Architect role with the human
accountable. Hazard-relevant anomalies go to `risk-management`; defects affecting MedHub become PRBs.

## Change log

- 2026-10-21 — Record created at the locked/declared version when the SOUP list moved from
  ADD-004 to one `soup` record per component (medical-records 0.3.2).
- 2026-10-22 — 26.0.0 (unchanged). First anomaly-list review (TASK-154, CR-001 AC-11/AC-12): no advisory for 26.0.0; control socket on by default and failing in MedHub's image (PRB-041, already open); later-fixed process-manager and parser bugs judged; nothing hazard-relevant. Record 1.0 → 1.1; approval record removed for re-review.
- 2026-10-31 — 26.0.0 (unchanged). TASK-185 (CR-004): records the reliance on `forwarded_allow_ips` being empty (SR-042, ADR-0019). Record 1.1 → 1.2; approval record removed for re-review.
- 2026-11-12 — 26.0.0 (unchanged). TASK-214 (CR-005, PRB-041): control socket disabled by configuration (`--no-control-socket` in the backend image `CMD`); relied-on configuration and Findings rows updated; also corrected the stale references: the Gunicorn command is the image `CMD` (not `backend/entrypoint.sh`, since TASK-191), PRB-041 is no longer open, `init: true` was not adopted (CR-005 Q-3); and stated that reload/shutdown by signal are unaffected (QA round 1, 2026-11-13). The version and the published information are unchanged, so no new anomaly review (`anomaly_review` stays 2026-10-22). Record 1.2 → 1.3; approval record removed for re-review.
