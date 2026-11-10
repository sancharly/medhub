import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse, delay } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "../tests/setup";
import { RequireRole } from "./RequireRole";

const BASE = "http://localhost/api/v1";
const childRendered = vi.fn();

function Child() {
  // Stands for the guarded page: if it renders, its queries would fire.
  childRendered();
  return <div>Guarded child</div>;
}

function meAs(userType: string) {
  server.use(
    http.get(`${BASE}/me`, () =>
      HttpResponse.json({ id: "1", email: "a@b.com", userType, mustChangePassword: false })
    )
  );
}

function renderGuard(roles: Parameters<typeof RequireRole>[0]["roles"]) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={["/admin/accounts"]}>
        <Routes>
          <Route path="/profile" element={<div>Profile page</div>} />
          <Route
            path="/admin/accounts"
            element={
              <RequireRole roles={roles}>
                <Child />
              </RequireRole>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

beforeEach(() => childRendered.mockClear());

describe("RequireRole", () => {
  // TASK-142 AC 2: admin flows unchanged.
  it("renders the child for an allowed role", async () => {
    meAs("ADMIN");
    renderGuard(["ADMIN", "SYSADMIN"]);
    expect(await screen.findByText("Guarded child")).toBeInTheDocument();
  });

  // TASK-142 AC 1 (SR-005, SR-009): PATIENT or DOCTOR at /admin/accounts is redirected, child never mounts.
  it.each(["PATIENT", "DOCTOR"])(
    "redirects %s to /profile without mounting the child",
    async (role) => {
      meAs(role);
      renderGuard(["ADMIN", "SYSADMIN"]);
      expect(await screen.findByText("Profile page")).toBeInTheDocument();
      expect(childRendered).not.toHaveBeenCalled();
    }
  );

  // TASK-142 implementation detail: no flash while me loads.
  it("renders nothing and does not mount the child while me is loading", async () => {
    server.use(
      http.get(`${BASE}/me`, async () => {
        await delay("infinite");
        return HttpResponse.json({});
      })
    );
    const { container } = renderGuard(["ADMIN"]);
    await new Promise((r) => setTimeout(r, 50));
    expect(container).toBeEmptyDOMElement();
    expect(childRendered).not.toHaveBeenCalled();
  });

  // Deny by default when me fails.
  it("renders nothing and does not mount the child when me fails", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(
          { type: "/errors/forbidden", title: "Forbidden", status: 403 },
          { status: 403, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );
    const { container } = renderGuard(["ADMIN"]);
    await waitFor(() => expect(container).toBeEmptyDOMElement());
    await new Promise((r) => setTimeout(r, 50));
    expect(container).toBeEmptyDOMElement();
    expect(childRendered).not.toHaveBeenCalled();
  });

  // Unknown role string is denied.
  it("denies an unknown role string", async () => {
    meAs("AUDITOR");
    renderGuard(["ADMIN", "SYSADMIN"]);
    expect(await screen.findByText("Profile page")).toBeInTheDocument();
    expect(childRendered).not.toHaveBeenCalled();
  });
});
