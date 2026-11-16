---
id: "PRB-016"
type: problem-report
title: "The `me` query is issued from nine places with inconsistent retry and a hard-coded session TTL"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-11-14"
criticality: major
links: []
tags: ["correctness", "hazard:availability"]
---

# PRB-016 — The `me` query is issued from nine places with inconsistent retry and a hard-coded session TTL

## Observed

`["me"]` is issued from nine files with differing retry settings, so an expired session can produce three 401s before the redirect; `auth/SessionActivityProvider` seeds a hard-coded 15-minute expiry that is never reconciled with the server TTL.

## Impact

SR-030 session behaviour differs between the client and the server, producing surprise logouts or stale sessions in the UI.

## Safety evaluation

Contributes to RISK-005 (account takeover: a UI that believes a dead session is alive) and RISK-007.

## Resolution

TASK-144, change request CR-006 (verified in the working tree, 2026-11-14):

- Backend: `SessionService.remaining_seconds` (role idle timeout capped by the absolute remainder); `GET /me` returns it as `sessionExpiresInSeconds` and `POST /auth/session/extend` as `expiresInSeconds` next to `expiresAt` (additive; `openapi.json` and `openapi.ts` regenerated).
- Frontend: `auth/useMe.ts` is the only reader of the `me` query (key in `api/queryKeys.ts`, `retry: false`, 30 s stale time); the ten former readers use it, so an expired session gives one 401 instead of retried ones. `SessionActivityProvider` takes its deadline from the receipt time of the `me` or extend response plus the reported seconds; the 15-minute seed and the role table (`getTimeoutMinutes`) are removed. A 401 on a mutation clears the cache and redirects once to `/login?timeout=1`.
- Verified by `test_session_service.py`, `test_me_router.py`, `test_auth_router.py` (backend, 1698 passed), `SessionActivityProvider.test.tsx`, `useMe.test.tsx`, `queryClient.test.tsx`, `IdleWarningDialog.test.tsx` (frontend, 340 passed); negative controls: a constant deadline, no mutation handler, retries in `useMe`, a second reader of `me`, a missing `me` field and no absolute cap each fail a test. `POST /auth/password` now answers a wrong current password with 400 `validation-error` on `currentPassword` instead of 401, so the mutation handler cannot sign the user out. Recorded in TS-001 TC-001.11.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding R.
