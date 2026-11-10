---
id: "PRB-067"
type: problem-report
title: "A failing /me request is re-requested in a tight loop"
status: resolved
version: "1.4"
author: "Carlos Santiago Liceras"
created: "2026-11-06"
updated: "2026-11-07"
criticality: major
links: []
tags: ["availability", "frontend", "found-in:TASK-142-qa"]
---

# PRB-067 — A failing /me request is re-requested in a tight loop

## Observed

Found by QA while reviewing TASK-142 (2026-11-06). When `GET /api/v1/me` answers an error that is
not an authentication error (a 403 or a 5xx), the frontend asks for it again and again. QA's probe
counted 176 requests in 0.9 s, and 709 in 3.3 s on HEAD without the TASK-142 guard, so the loop
predates CR-004. It made `App.test.tsx` "mounts nothing when me fails with 403" exceed the 5 s test
timeout.

## Impact

During a backend outage or a persistent 5xx on `/me`, every open browser tab floods the API with
hundreds of requests per second, which can keep a recovering server down. Availability defect; no
data is disclosed or altered. Criticality **major**.

## Investigation

- `frontend/src/auth/RequireAuth.tsx:25` returns `null` while the `["me"]` query is loading
  (`isLoading`), which unmounts the whole authenticated subtree.
- A query that has failed and holds no data goes back to `pending` on every new fetch. Observers
  that mount after the error (`ForcedPasswordGate`, `AuthenticatedApp`, the page queries) default to
  `retryOnMount: true`, so each one refetches on mount.
- The refetch makes `RequireAuth` return `null` again, the subtree unmounts, the error arrives, the
  subtree remounts, and the new observers refetch: a loop with no delay.
- Root cause: an errored, data-less query is refetched on mount by every observer, and the parent
  that gates the subtree unmounts on every refetch.

## Safety evaluation

No effect on confidentiality or integrity. The loop can degrade availability of the API for all
users while `/me` fails. No release exists (CR-004 A-1), so no notification is needed. The human
sets the final criticality.

## Resolution

Fixed in CR-004 (D-12) by TASK-142 (in review; `resolved` on QA approval, D-8). Three parts:

- `frontend/src/api/queryClient.ts` sets `retryOnMount: false` as the default for the `["me"]`
  query key, so an errored `/me` is not refetched by every observer that mounts. Chosen over
  changing `RequireAuth` alone because the loop comes from every observer of the key (nine files
  declare one today); one default covers all of them and any future one. `setQueryDefaults` matches
  by key prefix, so `["me", "consents"]` gets an explicit `retryOnMount: true` override and keeps
  retrying on mount.
- `RequireAuth` no longer sets `retry: false`: the client-wide policy applies, so a 401 still
  redirects at once (no retry on 4xx) and a 5xx is retried up to 3 times with backoff. That is a
  bounded number of requests inside one fetch, not the loop.
- When `/me` still fails with an error that is not an authentication error, `RequireAuth` renders
  an `Alert` (role `alert`: "Could not load your account. Check your connection and try again.")
  with a "Try again" button that calls `refetch()`, instead of a blank screen (SR-027 AC 3); the alert shows only when there is no loaded `/me` data, so a failed background refetch of an already-loaded `/me` keeps the app mounted.

Verified by TS-002 TC-002.9: `App.test.tsx` (a `/me` that fails with 500 is requested exactly 4
times, 1 plus 3 retries, and the alert shows; 500 then 200 recovers through "Try again"; a 401 is
requested once and goes to login) and `queryClient.test.tsx` (`["me","consents"]` still retries on
mount). Removing the `["me"]` default, putting `retry: false` back, removing the alert or removing
the consents override each fails a test.

## Source

TASK-142 QA review round 1; human decision 2026-11-06 to open it and fold it into CR-004.

## Version history

- 1.0 (2026-11-06) — Created from the TASK-142 QA review. `open`, `major`.
- 1.1 (2026-11-06) — Resolution written (TASK-142). Status stays `open` until QA approval (CR-004 D-8).
- 1.2 (2026-11-07) — TASK-142 round 3: Resolution updated (retry policy, recovery alert, consents override). Status stays `open` (D-8).
- 1.3 (2026-11-07) — TASK-142 R3-1: alert only when no `/me` data is loaded. Status stays `open` (D-8).
- 1.4 (2026-11-07) — QA approved TASK-142 (R3-1 check, CR-004 D-15): status `resolved` (CR-004 D-8).
