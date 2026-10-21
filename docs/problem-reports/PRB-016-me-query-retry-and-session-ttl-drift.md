---
id: "PRB-016"
type: problem-report
title: "The `me` query is issued from nine places with inconsistent retry and a hard-coded session TTL"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-09-17"
updated: "2026-10-21"
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

TASK-144 (draft) — a shared `useMe` hook with one retry policy, seeded from the server-reported TTL.

## Source

`docs/reports/CODE-REVIEW-2026-07.md` finding R.
