#!/usr/bin/env python3
"""Mixed read/write load test for SR-026 AC 5 (TASK-136, TC-018.3).

N authenticated clients (default 20, CR-006 D-3) loop over the routine operations of a small
clinic against ONE API worker for a fixed duration: ``GET /me``, list appointments, list clinical
entries, create a clinical entry, upload a 1 MiB attachment and download it. A separate probe
calls ``GET /healthz`` ten times a second: ``/healthz`` does no IO, so its latency is the event
loop's own responsiveness (a blocked loop shows up there, PRB-009).

Two sub-commands:

* ``seed``  Run INSIDE the backend container (it imports the app and needs DATABASE_URL). Creates
  one doctor and one patient account per client, so that no account holds more than the
  concurrent-session cap. Idempotent.
* ``run``   Needs only httpx and the base URL; runs from anywhere that reaches the API. Prints a
  table and, with ``--json``, writes the result for the verification record.

The shared account password comes from the ``LOAD_TEST_PASSWORD`` environment variable, never
from a command-line argument or a file in the repository. The test accounts are
``lt-doctor-<n>@load.test`` and ``lt-patient-<n>@load.test``.

Reachability: through the reverse proxy use ``https://host/api/v1`` (``--insecure`` for the
self-signed certificate). The proxy refuses bodies above its limit, so for a stack whose proxy
has none (PRB-078) point ``--base-url`` at the backend (``http://backend:8000/api/v1``) and run
with ``SESSION_COOKIE_SECURE=false``.

Pool timeouts and 5xx causes are read from the server log: capture it with ``docker logs`` and
pass the file as ``--server-log``; lines naming ``QueuePool limit`` are counted.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import random
import statistics
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

DOMAIN = "load.test"
POOL_TIMEOUT_MARKER = "QueuePool limit"
# Weights of the routine mix (SR-026): mostly reads, some writes, a few attachments.
MIX: tuple[tuple[str, int], ...] = (
    ("GET /me", 30),
    ("list appointments", 20),
    ("list clinical entries", 20),
    ("create clinical entry", 15),
    ("upload 1 MiB attachment", 8),
    ("download attachment", 7),
)
OPERATIONS = tuple(name for name, _ in MIX) + ("login", "healthz probe")


def _email(role: str, n: int) -> str:
    return f"lt-{role}-{n}@{DOMAIN}"


def _password() -> str:
    password = os.environ.get("LOAD_TEST_PASSWORD", "")
    if len(password) < 12:
        sys.exit("LOAD_TEST_PASSWORD must be set (12 characters or more).")
    return password


# ---------------------------------------------------------------------------
# seed (inside the backend container)
# ---------------------------------------------------------------------------


def seed(clients: int) -> None:
    from sqlalchemy import select  # noqa: PLC0415

    from app.auth.password import PasswordService  # noqa: PLC0415
    from app.db.models.account import Account, AccountStatus, UserType  # noqa: PLC0415
    from app.db.repositories.session import get_engine, get_session_factory  # noqa: PLC0415

    password_hash = PasswordService().hash(_password())
    with get_session_factory(get_engine())() as db:
        for n in range(clients):
            for role, user_type in (("doctor", UserType.DOCTOR), ("patient", UserType.PATIENT)):
                email = _email(role, n)
                exists = db.execute(select(Account.id).where(Account.email == email)).first()
                if exists:
                    continue
                db.add(
                    Account(
                        email=email,
                        password_hash=password_hash,
                        user_type=user_type,
                        status=AccountStatus.ACTIVE,
                        first_name=f"Load{role.title()}",
                        surname=str(n),
                        password_changed_at=datetime.now(UTC),
                    )
                )
        db.commit()
    print(f"seeded {clients} doctors and {clients} patients")


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


class Stats:
    """Latency samples and outcome counts per operation."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.latency: dict[str, list[float]] = defaultdict(list)
        self.count: dict[str, int] = defaultdict(int)
        self.server_errors: dict[str, int] = defaultdict(int)
        self.client_errors: dict[str, int] = defaultdict(int)  # 4xx other than expected
        self.transport_errors: dict[str, int] = defaultdict(int)  # timeout, reset, refused

    def record(self, op: str, seconds: float, status: int | None) -> None:
        self.count[op] += 1
        if status is None:
            self.transport_errors[op] += 1
            return
        self.latency[op].append(seconds)
        if status >= 500:
            self.server_errors[op] += 1
        elif status >= 400:
            self.client_errors[op] += 1


def _pct(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return float("nan")
    index = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return sorted_values[index]


def summarise(stats: Stats, server_log: str | None) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for op in OPERATIONS:
        values = sorted(stats.latency.get(op, []))
        if not stats.count.get(op):
            continue
        rows[op] = {
            "count": stats.count[op],
            "5xx": stats.server_errors.get(op, 0),
            "4xx": stats.client_errors.get(op, 0),
            "transport_errors": stats.transport_errors.get(op, 0),
            "p50_s": round(_pct(values, 0.50), 4),
            "p95_s": round(_pct(values, 0.95), 4),
            "max_s": round(max(values), 4) if values else None,
            "mean_s": round(statistics.fmean(values), 4) if values else None,
        }
    pool_timeouts = None
    if server_log:
        with open(server_log, encoding="utf-8", errors="replace") as handle:
            pool_timeouts = sum(POOL_TIMEOUT_MARKER in line for line in handle)
    return {
        "operations": rows,
        "total_requests": sum(stats.count.values()),
        "total_5xx": sum(stats.server_errors.values()),
        "total_transport_errors": sum(stats.transport_errors.values()),
        "pool_timeouts_in_log": pool_timeouts,
    }


def print_table(result: dict[str, Any]) -> None:
    header = (
        f"{'operation':28}{'count':>7}{'5xx':>6}{'4xx':>6}{'xport':>7}"
        f"{'p50':>9}{'p95':>9}{'max':>9}"
    )
    print(header)
    print("-" * len(header))
    for op, row in result["operations"].items():
        print(
            f"{op:28}{row['count']:>7}{row['5xx']:>6}{row['4xx']:>6}{row['transport_errors']:>7}"
            f"{row['p50_s']:>9.3f}{row['p95_s']:>9.3f}{(row['max_s'] or 0):>9.3f}"
        )
    print(
        f"total requests {result['total_requests']}, 5xx {result['total_5xx']}, "
        f"transport errors {result['total_transport_errors']}, "
        f"pool timeouts in log {result['pool_timeouts_in_log']}"
    )


async def run(args: argparse.Namespace) -> dict[str, Any]:
    import httpx  # noqa: PLC0415

    password = _password()
    stats = Stats()
    base = args.base_url.rstrip("/")
    root = base.split("/api/")[0]
    payload = random.Random(1).randbytes(args.upload_bytes)
    deadline_holder: dict[str, float] = {}
    last_login_status: list[int | None] = [None]
    # Signing in hashes a password (Argon2, deliberately slow): clients sign in a few at a time,
    # as a morning queue does, so that set-up is not itself the load being measured.
    sign_in_slots = asyncio.Semaphore(args.sign_in_parallelism)

    async def timed(
        client: httpx.AsyncClient, op: str, method: str, url: str, **kwargs: Any
    ) -> httpx.Response | None:
        started = time.perf_counter()
        try:
            response = await client.request(method, url, **kwargs)
            await response.aread()
        except httpx.HTTPError:
            stats.record(op, time.perf_counter() - started, None)
            return None
        stats.record(op, time.perf_counter() - started, response.status_code)
        return response

    async def login(client: httpx.AsyncClient, email: str) -> dict[str, Any] | None:
        response = await timed(
            client,
            "login",
            "POST",
            f"{base}/auth/login",
            json={"email": email, "password": password},
        )
        last_login_status[0] = None if response is None else response.status_code
        if response is None or response.status_code != 200:
            return None
        return response.json()  # type: ignore[no-any-return]

    def csrf(client: httpx.AsyncClient) -> dict[str, str]:
        return {"X-CSRF-Token": client.cookies.get("medhub_csrf") or ""}

    async def setup(n: int, stack: contextlib.AsyncExitStack) -> dict[str, Any] | None:
        """Sign in the doctor and the patient, grant consent, create one appointment and entry."""
        try:
            doctor = await stack.enter_async_context(
                httpx.AsyncClient(verify=not args.insecure, timeout=args.timeout)
            )
            patient = await stack.enter_async_context(
                httpx.AsyncClient(verify=not args.insecure, timeout=args.timeout)
            )
            async with sign_in_slots:
                d = await login(doctor, _email("doctor", n))
                p = await login(patient, _email("patient", n))
            if not (d and p):
                print(f"client {n}: sign-in refused (HTTP {last_login_status[0]})", file=sys.stderr)
                return None
            doctor_id, patient_id = d["user"]["id"], p["user"]["id"]
            await patient.post(
                f"{base}/consents", json={"doctorId": doctor_id}, headers=csrf(patient)
            )
            await doctor.post(
                f"{base}/appointments",
                json={
                    "doctorId": doctor_id,
                    "patientId": patient_id,
                    "scheduledAt": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
                },
                headers=csrf(doctor),
            )
            created = await doctor.post(
                f"{base}/patients/{patient_id}/clinical-entries",
                json={"occurredAt": datetime.now(UTC).isoformat(), "description": "setup"},
                headers=csrf(doctor),
            )
            if created.status_code != 201:
                return None
            return {
                "n": n,
                "doctor": doctor,
                "patient_id": patient_id,
                "entry_id": created.json()["id"],
            }
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            print(f"client {n}: setup failed: {exc!r}", file=sys.stderr)
            return None

    async def client_loop(ctx: dict[str, Any]) -> None:
        n, doctor = ctx["n"], ctx["doctor"]
        patient_id, entry_id = ctx["patient_id"], ctx["entry_id"]
        attachment_id: str | None = None
        ops = [name for name, weight in MIX for _ in range(weight)]
        rng = random.Random(n)
        counter = 0
        while time.perf_counter() < deadline_holder["end"]:
            op = rng.choice(ops)
            if op == "download attachment" and not attachment_id:
                op = "upload 1 MiB attachment"
            if op == "GET /me":
                await timed(doctor, op, "GET", f"{base}/me")
            elif op == "list appointments":
                await timed(doctor, op, "GET", f"{base}/appointments")
            elif op == "list clinical entries":
                await timed(doctor, op, "GET", f"{base}/patients/{patient_id}/clinical-entries")
            elif op == "create clinical entry":
                counter += 1
                await timed(
                    doctor,
                    op,
                    "POST",
                    f"{base}/patients/{patient_id}/clinical-entries",
                    json={
                        "occurredAt": datetime.now(UTC).isoformat(),
                        "description": f"load {n}-{counter}",
                    },
                    headers=csrf(doctor),
                )
            elif op == "upload 1 MiB attachment":
                response = await timed(
                    doctor,
                    op,
                    "POST",
                    f"{base}/clinical-entries/{entry_id}/attachments",
                    files={"file": (f"load-{n}.bin", payload, "application/octet-stream")},
                    headers=csrf(doctor),
                )
                if response is not None and response.status_code == 201:
                    attachment_id = response.json()["id"]
            else:
                await timed(doctor, op, "GET", f"{base}/attachments/{attachment_id}")
            if args.think_ms:
                await asyncio.sleep(rng.uniform(0, 2 * args.think_ms) / 1000)

    async def probe() -> None:
        async with httpx.AsyncClient(verify=not args.insecure, timeout=args.timeout) as client:
            while time.perf_counter() < deadline_holder["end"]:
                await timed(client, "healthz probe", "GET", f"{root}/healthz")
                await asyncio.sleep(0.1)

    async with contextlib.AsyncExitStack() as stack:
        contexts = await asyncio.gather(*(setup(n, stack) for n in range(args.clients)))
        ready = [ctx for ctx in contexts if ctx]
        if len(ready) < args.clients:
            print(
                f"setup failed for {args.clients - len(ready)} client(s); they are skipped",
                file=sys.stderr,
            )
        # Setup traffic is not part of the measurement.
        stats.reset()
        start = time.perf_counter()
        deadline_holder["end"] = start + args.duration
        await asyncio.gather(probe(), *(client_loop(ctx) for ctx in ready))
    elapsed = time.perf_counter() - start
    result = summarise(stats, args.server_log)
    result["clients"] = args.clients
    result["duration_s"] = round(elapsed, 1)
    result["think_ms"] = args.think_ms
    result["base_url"] = args.base_url
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    seed_p = sub.add_parser("seed", help="create the test accounts (inside the backend container)")
    seed_p.add_argument("--clients", type=int, default=20)
    run_p = sub.add_parser("run", help="run the load test")
    run_p.add_argument(
        "--base-url", required=True, help="API root, e.g. http://backend:8000/api/v1"
    )
    run_p.add_argument("--clients", type=int, default=20)
    run_p.add_argument("--duration", type=float, default=300.0, help="seconds (default 300)")
    run_p.add_argument("--upload-bytes", type=int, default=1024 * 1024)
    run_p.add_argument(
        "--sign-in-parallelism", type=int, default=4, help="clients signing in at once"
    )
    run_p.add_argument("--think-ms", type=float, default=0.0, help="mean think time per client")
    run_p.add_argument("--timeout", type=float, default=60.0, help="per-request timeout, seconds")
    run_p.add_argument("--insecure", action="store_true", help="do not verify the TLS certificate")
    run_p.add_argument("--server-log", help="captured server log, counted for pool timeouts")
    run_p.add_argument("--json", help="write the result to this file")
    args = parser.parse_args()
    if args.command == "seed":
        seed(args.clients)
        return
    result = asyncio.run(run(args))
    print_table(result)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)


if __name__ == "__main__":
    main()
