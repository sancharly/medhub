---
id: "SR-042"
type: software-requirement
title: "Originating client address and per-client rate limiting"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-10-31"
updated: "2026-10-31"
approved_by: Carlos Santiago Liceras
approved_on: "2026-10-31"
approval_note: self-approved at the ship-feature spec gate (sancharly/medhub#27)
links:
  - target: "RR-004"
    relation: satisfies
  - target: "NFR-007"
    relation: derives_from
  - target: "RISK-006"
    relation: mitigates
  - target: "RISK-007"
    relation: mitigates
tags: ["control:design", "control:protective", "issue:sancharly/medhub#27"]
---

## Summary

The system shall determine the originating client address of each request from the reverse proxy's forwarded header only when the request comes from a trusted proxy, and shall rate-limit the code-authorized anonymized-data retrieval per originating client address.

## Description

MedHub runs behind a reverse proxy, so the TCP peer of every request is the proxy. Any control that needs to know who sent a request, such as the audit source address (SR-023 AC 6) or a rate limit, gets the proxy's address unless the application reads the forwarded header. If it reads the header from any peer, a client can claim any address. This requirement defines one rule for the originating client address and applies it to the anonymized-data retrieval limit (ADR-0013: 5 attempts per hour against code guessing), which is keyed on the proxy address today, so all callers share one bucket (PRB-029).

§5.2.2 categories: e (security, audit trail), j (IT-network aspects).

## Acceptance Criteria

1. The originating client address of a request is the address of the TCP peer, unless that peer is a trusted proxy. Then it is the right-most address in `X-Forwarded-For` that is not itself a trusted proxy.
2. An `X-Forwarded-For` header received from a peer that is not a trusted proxy is ignored: the originating client address is the peer's own address.
3. The trusted proxies are a deployment setting. With the setting empty, no forwarded header is trusted. The deployment definition sets it to the MedHub reverse proxy.
4. The anonymized-data retrieval endpoint counts attempts per originating client address. The sixth attempt from one address within the 3600-second window that starts at its first counted attempt is refused with HTTP 429, and the presented code is not evaluated.
5. Attempts from one originating client address do not count toward another's limit. After client A has used up its limit, a request from client B through the same proxy is still evaluated.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity". Satisfies RR-004 "Accountability: auditability of access to health data" (source address of each security-relevant action).

## Risk Analysis

### Rationale

RR-004 requires the source address of every security-relevant action, and the audit record is only as good as the address it carries. The retrieval rate limit is the anti-guessing control of ADR-0013; keyed on the proxy, it protects no caller and blocks all of them at once.

### Potential Risks

- Trusting the forwarded header from any peer lets a client forge its address in the audit trail (RISK-006) and get around the rate limit.
- A limit shared by all callers lets one caller deny the retrieval to every legitimate user (RISK-007).
- A wrong trusted-proxy setting makes every address the proxy's again, so the failure is silent. AC 3 and a test on a started stack catch it.

### Control Measures

- One address rule used by the audit log and the rate limit (AC 1 to AC 3).
- Per-address counting with negative tests: a forged header from an untrusted peer, two clients through one proxy (AC 4, AC 5).
- The TS is written at the Build stage. TASK-113's security review checks the `X-Forwarded-For` trust chain.

## Version history

- 1.0 (2026-10-31) — Initial creation (CR-004, GitHub sancharly/medhub#27), from PRB-029 and the address need of PRB-010.
