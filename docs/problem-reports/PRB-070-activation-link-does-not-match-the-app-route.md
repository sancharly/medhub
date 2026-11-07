---
id: "PRB-070"
type: problem-report
title: "The e-mailed activation link does not match the app's activation route"
status: resolved
version: "1.2"
author: "Carlos Santiago Liceras"
created: "2026-11-07"
updated: "2026-11-07"
criticality: major
links: []
tags: ["activation", "frontend", "hazard:availability", "found-in:TASK-206-planning"]
---

# PRB-070 — The e-mailed activation link does not match the app's activation route

## Observed

Found by the Software Architect role while planning TASK-206 (2026-11-07), from the code. The activation
e-mail carries `<PUBLIC_BASE_URL>/activate?token=<token>`, but the single-page app serves the activation
page only at `/activation/<token>`. Not yet confirmed on a started stack: that confirmation is TASK-206's
job (its started-stack check).

## Impact

From the code, following the e-mailed link does not reach the activation page: the user is sent to the
sign-in page and, since the account is not yet active, cannot sign in. No new account can be activated
through the e-mail (SR-033 AC 1 and AC 3), so a patient or clinician cannot start using the application
(RISK-009, "cannot activate their account"). An administrator's resend (SR-033 AC 7) produces a link of
the same form, so it does not help. The account and its data are not affected; a user who is given the
`/activation/<token>` form by hand can activate.

## Investigation

Path of a real link, on HEAD 3eef9fb:

1. `backend/app/workers/email_tasks.py:97` builds `f"{settings.public_base_url}/activate?token={activation_token}"`.
   The token is `secrets.token_urlsafe(32)` (`backend/app/identity/activation.py:40`), so it is safe in a
   path segment. The same task sends the resend e-mail (`identity/activation.py:116`,
   `identity/account_service.py`).
2. Reverse proxy, `infra/reverse-proxy/nginx.conf:45-47`: `location /` proxies to the frontend unchanged.
   No rewrite or redirect for `/activate`.
3. Frontend container, `frontend/nginx.conf:6-8`: `try_files $uri $uri/ /index.html`, so `/activate` is
   answered with the SPA's `index.html`.
4. SPA routes, `frontend/src/app/App.tsx:72-74`: `/login`, `/activation/:token`, then `*` →
   `RequireAuth`. `/activate` matches only `*`. No route reads a `token` query parameter (no
   `useSearchParams` for it in `frontend/src`).
5. `frontend/src/auth/RequireAuth.tsx:18-22`: with no session, `/me` fails with `AuthError` and the user is
   navigated to `/login?next=/activate`. The query string, and the token with it, is dropped
   (`location.pathname` only).
6. The account is inactive, so login fails (SR-033 AC 8). Dead end.

The mismatch dates from the frontend foundation (commit 30748ca added `/activation/:token`; the e-mail
link comes from 845886c). No test spans both: `backend/tests/workers/test_email_tasks.py:15-16` checks the
renderer with a literal `/activate?token=abc`, and no test builds the link from `send_activation_email`
and resolves it against the SPA routes. In `frontend/src/core/nav/routeRoles.test.ts:13-14`
`/activation/:token` is an exempt public route (`ActivationPage` only).

Root cause: the link format is defined twice, in the worker and in the SPA route table, with nothing tying
them together.

## Safety evaluation

Availability of the activation function: new users cannot activate, so they cannot see appointments or
clinical information through the application (RISK-009). No data is disclosed or altered. Criticality
**major**: a primary function (SR-033) fails for every new account, with a manual workaround only. No
release exists (CR-004 A-1), so no released version in use is affected and no notification is needed.
The human sets the final criticality.

## Resolution

Fixed by TASK-206 (CR-004 D-16); status `resolved` on QA approval (D-8).

- `send_activation_email` builds `{PUBLIC_BASE_URL}/activation/<token>` (`backend/app/workers/email_tasks.py`);
  the resend path uses the same task. `infra/tests/test_activation_link_route.py` fails if the link template or
  the `<Route path="/activation/:token">` in `frontend/src/app/App.tsx` changes alone;
  `backend/tests/workers/test_email_tasks.py::test_activation_email_link_uses_the_activation_route`.
- Started stack: an account created by an administrator produced a mail whose only link was
  `https://localhost/activation/<token>`; the proxy served the SPA for it with `Referrer-Policy: no-referrer`;
  the token validated, activated the account, and the new password signed in; no log held the token. The
  browser rendering of the page was not done in this check (the token must not be displayed); the route is
  covered by the static route test and `routeRoles.test.ts`.
- Found on the same stack: the API process could not enqueue the mail at all (PRB-071, fixed in the same task). After that fix, with no broker override, a real e-mailed link rendered the activation page in a browser, activated the account and signed in.

## Source

TASK-206 planning (Software Architect role), found while listing token-bearing URLs for PRB-068; human
decision 2026-11-07 (D-16).

## Version history

- 1.0 (2026-11-07) — Created. `open`, `major`.
- 1.1 (2026-11-07) — Resolution written by the Software Developer role (TASK-206). Left `open` (CR-004 D-8).
- 1.2 (2026-11-07) — QA approved TASK-206: status `resolved` (CR-004 D-8).
