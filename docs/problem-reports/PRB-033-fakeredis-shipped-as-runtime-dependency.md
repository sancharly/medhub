---
id: "PRB-033"
type: problem-report
title: "fakeredis is declared as a runtime dependency and ships in the production image"
status: open
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-21"
updated: "2026-10-21"
criticality: minor
links: []
tags: ["soup", "configuration-management"]
---

# PRB-033 — fakeredis is declared as a runtime dependency

## Observed

`backend/pyproject.toml` lists `fakeredis>=2.36.2` under `[project] dependencies`, so it is
installed into the production image. No module under `backend/app/` or `backend/modules/` imports
it; only the test suite does.

## Impact

- An in-memory Redis imitation ships in the product without being relied on, adding an unreviewed
  SOUP item ([SOUP-018](../soup/SOUP-018-fakeredis.md)) and attack surface for no function.
- A misconfiguration that wires it in place of the real client would silently drop sessions on
  restart; nothing prevents that today.

## Safety evaluation

No hazard is realized: the package is unused at runtime. It would contribute to RISK-005 and
RISK-007 only through the misconfiguration described above.

## Resolution

Move `fakeredis` to the `dev` dependency group, refresh `uv.lock`, and mark SOUP-018 `obsolete`
in the same change. Needs a task and a CR.

## Source

Found while splitting the SOUP list into one record per component (2026-10-21).
