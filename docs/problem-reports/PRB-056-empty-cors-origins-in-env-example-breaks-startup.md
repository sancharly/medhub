---
id: "PRB-056"
type: problem-report
title: "The empty CORS_ORIGINS in .env.example makes the backend fail at start-up"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-30"
updated: "2026-10-30"
criticality: minor
links: []
tags: ["infrastructure", "configuration", "backend"]
---

# PRB-056 — The empty CORS_ORIGINS in .env.example makes the backend fail at start-up

## Observed

With `infra/.env` copied unchanged from `infra/.env.example`, the backend container restarts in a
loop with `SettingsError: error parsing value for field "cors_origins"`. Found by the software
developer during CR-002 TASK-179 and reproduced by QA on 2026-10-30. Setting `CORS_ORIGINS=[]`
works.

## Impact

A fresh installation that follows the example configuration does not start until the operator
works out the expected format.

## Investigation

`infra/.env.example:80-82` ships `CORS_ORIGINS=` with the comment "Comma-separated list of allowed
origins (empty = no CORS)". The settings field is `cors_origins: list[str] = []`, which
pydantic-settings parses from the environment as JSON, so an empty string is not a valid value and
a comma-separated list is not accepted either. Both lines come from commit 7cd2b6a (TASK-003,
2026-06-20), so the defect predates CR-002.

## Safety evaluation

It fails loudly at start-up and affects only availability on a fresh setup from the example. No
data, safety-related function or clinical decision is affected. No released version exists, so no
notification is needed. Hence `minor`.

## Proposed resolution

Ship `CORS_ORIGINS=[]` with a comment showing the JSON form (`["https://example.org"]`), or accept a
comma-separated value in the settings, and add a test that the example file loads. Needs a task and
a CR; outside CR-002's scope. Until it is fixed, verification runs set `CORS_ORIGINS=[]` in their
temporary `.env`.

## Source

Software developer and QA, CR-002 TASK-179 (2026-10-30).
