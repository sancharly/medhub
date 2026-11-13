---
id: "PRB-078"
type: problem-report
title: "Reverse proxy rejects uploads larger than 1 MiB"
status: resolved
version: "1.1"
author: "Carlos Santiago Liceras"
created: "2026-11-13"
updated: "2026-11-13"
criticality: major
links: []
tags: ["deployment", "attachments", "hazard:availability", "found-in:cr-006-plan"]
---

# PRB-078 — Reverse proxy rejects uploads larger than 1 MiB

## Observed

Found at the CR-006 Plan stage (2026-11-13) while planning the 150 MiB attachment limit (D-2): no
`client_max_body_size` directive exists anywhere in `infra/reverse-proxy/nginx.conf` (neither in the
`http` block nor in the `server` blocks at lines 19 and 27 nor in `location /api/` at lines 74-80) or in
`frontend/nginx.conf`. Found by reading the configuration; not yet reproduced on a started stack.

## Impact

nginx's documented default for `client_max_body_size` is 1 MiB. On the deployed stack every request
body above 1 MiB to `/api/` is answered with HTTP 413 by nginx before it reaches the backend, so a doctor
cannot attach any file above 1 MiB, including every typical DICOM study (50 to 150 MB,
`docs/design/10-quality-requirements.md`). SR-013 AC 1 (attach DICOM files) fails on the deployed
stack; the backend tests do not pass through nginx, which is why the suites stay green. Nothing is
stored, altered or disclosed. The nginx 413 page is not an RFC 7807 problem, so the client shows a
generic error (SR-027 AC 3).

## Investigation

- `infra/reverse-proxy/nginx.conf`: the `/api/` location proxies to `backend:8000` with header settings
  only; no body-size directive at any level, so the default applies (SOUP-024).
- Backend limit: `attachment_max_bytes` defaults to 100 MiB (`backend/app/attachments/service.py:70`),
  raised to 150 MiB by CR-006 D-2. The proxy limit and the application limit were never aligned.
- To confirm at fix time: a 2 MiB upload through the started stack returns nginx's 413.

## Safety evaluation

The failure is loud: the upload is refused and nothing is half-written, so no wrong clinical
information is shown. The clinical attachment, in particular an imaging study, is not available in the
record, which delays care (RISK-007, information unavailable). No new hazard; no control relied on the
missing directive. Criticality **major**: a core function (SR-013 AC 1) is unusable for most real files
on the deployed stack, with a workaround only outside the product. No release exists, so no
notification is needed. The human sets the final criticality.

## Resolution

CR-006 (Plan-gate decision D-18), TASK-135 (2026-11-13): `client_max_body_size 151m;` added to
`location /api/` in `infra/reverse-proxy/nginx.conf`, with a comment naming `attachment_max_bytes`;
`infra/tests/test_proxy_body_limit.py` checks that the directive is present, not 0, and not smaller than
the `Settings.attachment_max_bytes` default, and that Compose defaults `ATTACHMENT_MAX_BYTES` to that
value (the setting is also in `infra/.env.example`).

Verified in the working tree with real nginx 1.31.8-alpine (the image the stack pins, started on a
throwaway network in front of a permissive stub upstream, ports 18443/18444, removed afterwards):
the configuration as committed at HEAD answered 413 to POST bodies of 2 MB, 100 MB, 150 MiB and 160 MB
(reproducing the report); the working-tree configuration answered 200 to 2 MB, 100 MB and 150 MiB and
413 to 160 MB. Human decision (QA finding 5, 2026-11-13): above the limit nginx no longer shows its HTML 413 page.
`location /api/` has `error_page 413 =400 @upload_too_large;` and an internal named location returns
`application/problem+json` with the API's own over-limit refusal (status 400, type
`https://medhub.example/errors/validation-error`, title `Validation Error`, a fixed detail, `errors: []`;
no `instance`, no upstream detail), so the client sees one contract (SR-013 AC 6). 400 rather than 413
because the API's refusal of the same condition is 400 and the frontend handles one problem type.
Checked with real nginx: 160 MB gives `400`, `Content-Type: application/problem+json` and that body;
2 MB and 150 MiB still reach the upstream. Reproduction (run from the repository root; `$S` is any scratch directory, ports 18443 and
18444 free; the stub upstream needs `client_max_body_size 0` or it answers 413 itself):

```
printf 'server { listen 8000; listen 8080; client_max_body_size 0; location / { return 200 "ok"; } }\n' > $S/stub.conf
git show HEAD:infra/reverse-proxy/nginx.conf > $S/old.conf; cp infra/reverse-proxy/nginx.conf $S/new.conf
docker network create t135net
docker run -d --rm --name t135stub --network t135net --network-alias backend --network-alias frontend \
  -v $S/stub.conf:/etc/nginx/conf.d/default.conf:ro nginx:1.31.8-alpine
docker run -d --rm --name t135px-old --network t135net -p 127.0.0.1:18443:443 \
  -v $S/old.conf:/etc/nginx/conf.d/default.conf:ro -v $PWD/infra/certs:/etc/nginx/certs:ro nginx:1.31.8-alpine
docker run -d --rm --name t135px-new --network t135net -p 127.0.0.1:18444:443 \
  -v $S/new.conf:/etc/nginx/conf.d/default.conf:ro -v $PWD/infra/certs:/etc/nginx/certs:ro nginx:1.31.8-alpine
for n in 2000000 100000000 157286400 160000000; do head -c $n /dev/zero > $S/body.bin
  for p in 18443 18444; do echo "$p $n $(curl -sk -o /dev/null -w '%{http_code}' -X POST --data-binary @$S/body.bin https://127.0.0.1:$p/api/v1/x)"; done; done
docker rm -f t135px-old t135px-new t135stub; docker network rm t135net
```

Not verified: an upload through the project's own started stack (reverse proxy, backend
and object store together); the running stack was left untouched. That is TASK-226 (100 MiB through the
started stack).

## Version history

- 1.0 (2026-11-13) — Created from CR-006 Plan-stage finding P-4, at the human's Plan-gate decision. Resolved by
  CR-006 (TASK-135).
- 1.1 (2026-11-13) — TASK-135: `client_max_body_size 151m` on `/api/`; reproduced and verified against
  real nginx in the working tree (see Resolution). `resolved`; `closed` after the CR closes.
