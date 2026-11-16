import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { queryClient } from "../api/queryClient";
import { App } from "./App";

// SR-026 AC 7, TASK-145: routed pages other than the landing route load on first navigation, and they
// load only behind RequireAuth, ForcedPasswordGate and SessionActivityProvider. A module factory runs
// when the module is first imported, so `loaded` records which chunks were requested. The module
// registry is per test file: the tests below run in this order on purpose.
const { loaded } = vi.hoisted(() => ({ loaded: vi.fn() }));

vi.mock("../auth/LoginPage", () => ({ LoginPage: () => <div>login page</div> }));
vi.mock("../core/profile", () => ({ ProfilePage: () => <div>page:/profile</div> }));
vi.mock(
  "../auth/ChangePasswordPage",
  () => (loaded("password"), { ChangePasswordPage: () => <div>page:/password</div> })
);
vi.mock(
  "../core/patients",
  () => (loaded("patients"), { PatientListPage: () => <div>page:/patients</div> })
);
vi.mock(
  "../core/clinical",
  () => (loaded("clinical"), { ClinicalEntriesPage: () => <div>page:clinical</div> })
);
vi.mock(
  "../core/appointments",
  () => (loaded("appointments"), { AppointmentsPage: () => <div>page:/appointments</div> })
);
vi.mock(
  "../core/consent",
  () => (loaded("consent"), { ConsentPage: () => <div>page:/consent</div> })
);
vi.mock(
  "../core/admin/accounts",
  () => (loaded("admin"), { AccountsPage: () => <div>page:/admin/accounts</div> })
);
vi.mock(
  "../core/admin/groups",
  () => (loaded("admin"), { GroupsPage: () => <div>page:/admin/groups</div> })
);

const BASE = "http://localhost/api/v1";
const meAs = (userType: string) =>
  server.use(
    http.get(`${BASE}/me`, () =>
      HttpResponse.json({ id: "1", email: "a@b.com", userType, mustChangePassword: false })
    )
  );
const visit = (path: string) => {
  window.history.pushState({}, "", path);
  return render(<App />);
};

beforeEach(() => queryClient.clear());
afterEach(() => window.history.pushState({}, "", "/"));

describe("lazy routes", () => {
  it("an unauthenticated deep link loads no page chunk", async () => {
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
    expect(loaded).not.toHaveBeenCalled();
  });

  it("landing route does not import the other pages", async () => {
    meAs("SYSADMIN");
    visit("/profile");
    await screen.findByText("page:/profile");
    expect(loaded).not.toHaveBeenCalled();
  });

  it("a lazy page is requested on first navigation and renders", async () => {
    meAs("SYSADMIN");
    visit("/admin/accounts");
    await screen.findByText("page:/admin/accounts");
    await waitFor(() => expect(loaded).toHaveBeenCalledWith("admin"));
    expect(loaded).not.toHaveBeenCalledWith("patients");
  });
});
