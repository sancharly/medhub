import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { queryClient } from "../api/queryClient";
import { routeRoles, type RoutePath } from "../core/nav/routeRoles";
import type { UserType } from "../api/generated/types";
import { App } from "./App";

const { mounted } = vi.hoisted(() => ({ mounted: vi.fn() }));

// Each page is replaced by a stub that records its mount: a mounted page is
// the point where its queries would fire.
vi.mock("../auth/LoginPage", () => ({ LoginPage: () => <div>login page</div> }));
vi.mock("../auth/ChangePasswordPage", () => ({
  ChangePasswordPage: () => (mounted("/password"), (<div>page:/password</div>)),
}));
vi.mock("../core/profile", () => ({
  ProfilePage: () => (mounted("/profile"), (<div>page:/profile</div>)),
}));
vi.mock("../core/patients", () => ({
  PatientListPage: () => (mounted("/patients"), (<div>page:/patients</div>)),
}));
vi.mock("../core/clinical", () => ({
  ClinicalEntriesPage: () => (
    mounted("/patients/:patientId/clinical-entries"),
    (<div>page:clinical</div>)
  ),
}));
vi.mock("../core/appointments", () => ({
  AppointmentsPage: () => (mounted("/appointments"), (<div>page:/appointments</div>)),
}));
vi.mock("../core/consent", () => ({
  ConsentPage: () => (mounted("/consent"), (<div>page:/consent</div>)),
}));
vi.mock("../core/admin/accounts", () => ({
  AccountsPage: () => (mounted("/admin/accounts"), (<div>page:/admin/accounts</div>)),
}));
vi.mock("../core/admin/groups", () => ({
  GroupsPage: () => (mounted("/admin/groups"), (<div>page:/admin/groups</div>)),
}));

const BASE = "http://localhost/api/v1";
// Expected matrix, written out by hand from the requirements and the server
// decision table (SR-005, SR-009, SR-010 AC 4, SR-011 AC 3, SR-032, SR-034;
// backend/tests/authz/test_decision_table.py). It must not be derived from
// routeRoles: the table is what is under test.
const ALL: UserType[] = ["PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"];
const EXPECTED: Record<string, UserType[]> = {
  "/password": ALL,
  "/profile": ALL,
  "/patients": ["DOCTOR"],
  "/patients/:patientId/clinical-entries": ["DOCTOR", "PATIENT"],
  "/appointments": ALL,
  "/consent": ["PATIENT"],
  "/admin/accounts": ["ADMIN", "SYSADMIN"],
  "/admin/groups": ["SYSADMIN"],
};
const paths = Object.keys(EXPECTED) as RoutePath[];
const concrete = (p: string) => p.replace(":patientId", "p1");

function meAs(userType: string) {
  server.use(
    http.get(`${BASE}/me`, () =>
      HttpResponse.json({ id: "1", email: "a@b.com", userType, mustChangePassword: false })
    )
  );
}

function visit(path: string) {
  window.history.pushState({}, "", path);
  return render(<App />);
}

const originalDefaults = queryClient.getDefaultOptions();
beforeEach(() => {
  mounted.mockClear();
  queryClient.clear();
  // Same retry policy, no backoff wait, so the tests stay fast.
  queryClient.setDefaultOptions({
    ...originalDefaults,
    queries: { ...originalDefaults.queries, retryDelay: 0 },
  });
});
afterEach(() => {
  window.history.pushState({}, "", "/");
  queryClient.setDefaultOptions(originalDefaults);
});

describe("route-level role guards (TASK-142, PRB-014)", () => {
  // AC 3: the table equals the expected matrix, so adding or dropping a role fails here.
  it("routeRoles equals the expected matrix", () => {
    expect(Object.fromEntries(Object.entries(routeRoles).map(([k, v]) => [k, [...v]]))).toEqual(
      EXPECTED
    );
  });

  // AC 1 (SR-005, SR-009 defence in depth) and AC 2 (allowed flows unchanged): every route x every role,
  // entered as a deep link.
  describe.each(paths)("%s", (path) => {
    it.each(ALL)("%s", async (role) => {
      meAs(role);
      visit(concrete(path));
      const allowed = EXPECTED[path].includes(role);
      if (allowed) {
        await waitFor(() => expect(mounted).toHaveBeenCalledWith(path));
        expect(window.location.pathname).toBe(concrete(path));
      } else {
        await waitFor(() => expect(window.location.pathname).toBe("/profile"));
        await screen.findByText("page:/profile");
        expect(mounted).not.toHaveBeenCalledWith(path);
      }
    });
  });

  // AC 1: the redirect target is itself allowed for every role.
  it("redirects an unknown path to /profile", async () => {
    meAs("PATIENT");
    visit("/nowhere");
    await screen.findByText("page:/profile");
    expect(window.location.pathname).toBe("/profile");
  });

  // Unauthenticated user goes to login (RequireAuth), no protected page mounts.
  it("sends an unauthenticated deep link to login", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );
    visit("/admin/accounts");
    await screen.findByText("login page");
    expect(mounted).not.toHaveBeenCalled();
  });

  // No flash of protected content while me loads.
  it("mounts nothing while me is loading", async () => {
    let release: () => void = () => {};
    const gate = new Promise<void>((r) => (release = r));
    server.use(
      http.get(`${BASE}/me`, async () => {
        await gate;
        return HttpResponse.json({
          id: "1",
          email: "a@b.com",
          userType: "PATIENT",
          mustChangePassword: false,
        });
      })
    );
    visit("/admin/accounts");
    await new Promise((r) => setTimeout(r, 50));
    expect(mounted).not.toHaveBeenCalled();
    release();
    await screen.findByText("page:/profile");
    expect(mounted).not.toHaveBeenCalledWith("/admin/accounts");
  });

  // me failing (non-auth error): deny by default, nothing mounts.
  it("mounts nothing when me fails with 403", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(
          { type: "/errors/forbidden", title: "Forbidden", status: 403 },
          { status: 403, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );
    visit("/admin/accounts");
    await waitFor(() => expect(queryClient.getQueryState(["me"])?.status).toBe("error"));
    await act(async () => {
      await new Promise((r) => setTimeout(r, 50));
    });
    expect(mounted).not.toHaveBeenCalled();
  });

  const problem500 = () =>
    HttpResponse.json(
      { type: "/errors/internal", title: "Server error", status: 500 },
      { status: 500, headers: { "Content-Type": "application/problem+json" } }
    );

  // PRB-067: a failing /me is retried a bounded number of times, not in a loop, then an alert shows (SR-027 AC 3).
  it("requests /me a bounded number of times when it fails with 500 and shows an alert", async () => {
    let calls = 0;
    server.use(
      http.get(`${BASE}/me`, () => {
        calls += 1;
        return problem500();
      })
    );
    visit("/admin/accounts");
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not load your account");
    await act(async () => {
      await new Promise((r) => setTimeout(r, 500));
    });
    // 1 request plus the 3 retries of the client-wide policy.
    expect(calls).toBe(4);
    expect(mounted).not.toHaveBeenCalled();
  });

  // R3-1: a failed background refetch of a loaded /me must not replace the app with the alert.
  it("keeps the page mounted when a refetch of a loaded /me fails with 500", async () => {
    let healthy = true;
    server.use(
      http.get(`${BASE}/me`, () =>
        healthy
          ? HttpResponse.json({
              id: "1",
              email: "a@b.com",
              userType: "SYSADMIN",
              mustChangePassword: false,
            })
          : problem500()
      )
    );
    visit("/admin/accounts");
    await waitFor(() => expect(mounted).toHaveBeenCalledWith("/admin/accounts"));
    healthy = false;
    await act(async () => {
      await queryClient.refetchQueries({ queryKey: ["me"] });
    });
    await waitFor(() => expect(queryClient.getQueryState(["me"])?.status).toBe("error"));
    expect(screen.getByText("page:/admin/accounts")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  // R2-1: recovery after a transient failure, without a reload.
  it("recovers when Try again is clicked after /me failed with 500", async () => {
    let healthy = false;
    server.use(
      http.get(`${BASE}/me`, () =>
        healthy
          ? HttpResponse.json({
              id: "1",
              email: "a@b.com",
              userType: "SYSADMIN",
              mustChangePassword: false,
            })
          : problem500()
      )
    );
    visit("/admin/accounts");
    await screen.findByRole("alert");
    expect(mounted).not.toHaveBeenCalled();
    healthy = true;
    await userEvent.setup().click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(mounted).toHaveBeenCalledWith("/admin/accounts"));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  // A 401 is a 4xx: no retry, straight to login.
  it("does not retry a 401 on /me", async () => {
    let calls = 0;
    server.use(
      http.get(`${BASE}/me`, () => {
        calls += 1;
        return HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        );
      })
    );
    visit("/admin/accounts");
    await screen.findByText("login page");
    expect(calls).toBe(1);
  });
});
