import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { ConfirmProvider } from "../../confirm/ConfirmProvider";
import { server } from "../../../tests/setup";
import { AccountsPage } from "./AccountsPage";
import { theme } from "../../theme/theme";

const BASE = "http://localhost/api/v1";

const adminMe = {
  id: "admin-1",
  email: "admin@test.com",
  userType: "admin",
  mustChangePassword: false,
};

const sysadminMe = {
  id: "sys-1",
  email: "sys@test.com",
  userType: "sysadmin",
  mustChangePassword: false,
};

const accounts = [
  {
    id: "u1",
    firstName: "Alice",
    surname: "Smith",
    email: "alice@test.com",
    userType: "patient",
    state: "ACTIVE",
  },
  {
    id: "u2",
    firstName: "Bob",
    surname: "Jones",
    email: "bob@test.com",
    userType: "doctor",
    state: "INACTIVE",
  },
];

function renderPage(meResponse = adminMe) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });

  server.use(
    http.get(`${BASE}/users/me`, () => HttpResponse.json(meResponse))
  );

  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <ConfirmProvider>
          <MemoryRouter>
            <AccountsPage />
          </MemoryRouter>
        </ConfirmProvider>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("AccountsPage", () => {
  it("SR-009 AC-1/2: account list shows non-clinical fields only; no clinical data", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json(accounts))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    // Clinical fields must not appear
    expect(screen.queryByText(/diagnosis/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/medication/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/prescription/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/condition/i)).not.toBeInTheDocument();

    // Non-clinical fields present
    expect(screen.getByText(/alice@test.com/i)).toBeInTheDocument();
    expect(screen.getByText(/patient/i)).toBeInTheDocument();
  });

  it("SR-032.4: admin creator user-type select does not offer System Administrator", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json([]))
    );

    renderPage(adminMe);

    await waitFor(() => {
      expect(screen.getByLabelText(/user type/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/user type/i);
    await userEvent.click(select);

    await waitFor(() => {
      expect(screen.queryByRole("option", { name: /system administrator/i })).not.toBeInTheDocument();
    });
  });

  it("SR-032.5: sysadmin creator can select System Administrator", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json([]))
    );

    renderPage(sysadminMe);

    await waitFor(() => {
      expect(screen.getByLabelText(/user type/i)).toBeInTheDocument();
    });

    const select = screen.getByLabelText(/user type/i);
    await userEvent.click(select);

    await waitFor(() => {
      expect(screen.getByRole("option", { name: /system administrator/i })).toBeInTheDocument();
    });
  });

  it("SR-032.2: create with missing fields shows error", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json([]))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /create account/i })).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /create account/i })).toBeDisabled();
  });

  it("SR-032.3: duplicate email 409 mapped to email field error", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json([])),
      http.post(`${BASE}/accounts`, () =>
        HttpResponse.json(
          {
            type: "/errors/conflict",
            title: "Conflict",
            status: 409,
            errors: [{ field: "email", message: "Email already in use" }],
          },
          { status: 409, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/first name/i), "John");
    await userEvent.type(screen.getByLabelText(/surname/i), "Doe");
    await userEvent.type(screen.getByLabelText(/email/i), "dup@test.com");

    // Select user type
    const select = screen.getByLabelText(/user type/i);
    await userEvent.click(select);
    await waitFor(() => expect(screen.getByRole("option", { name: /patient/i })).toBeInTheDocument());
    await userEvent.click(screen.getByRole("option", { name: /patient/i }));

    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByText(/email already in use/i)).toBeInTheDocument();
    });
  });

  it("SR-034.6 / ADR-0013: delete dialog shows email + type + lost-code warning text", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json(accounts))
    );

    renderPage(sysadminMe);

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText(/alice@test.com/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/patient/i)).toBeInTheDocument();
    expect(within(dialog).getByText(/unrecoverable/i)).toBeInTheDocument();
  });

  it("SR-027.2: cancelling delete dialog issues no request", async () => {
    const deleteSpy = vi.fn();

    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json(accounts)),
      http.delete(`${BASE}/accounts/u1`, () => {
        deleteSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage(sysadminMe);

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole("button", { name: /delete/i });
    await userEvent.click(deleteButtons[0]);

    await waitFor(() => {
      expect(screen.getByRole("dialog")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(deleteSpy).not.toHaveBeenCalled();
  });

  it("SR-034.1: Deactivate disabled for acting sysadmin's own row", async () => {
    const selfAccount = {
      id: "sys-1",
      firstName: "System",
      surname: "Admin",
      email: "sys@test.com",
      userType: "sysadmin",
      state: "ACTIVE",
    };

    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json([selfAccount, ...accounts]))
    );

    renderPage(sysadminMe);

    await waitFor(() => {
      expect(screen.getByText(/sys@test.com/i)).toBeInTheDocument();
    });

    const rows = screen.getAllByRole("row");
    const selfRow = rows.find((row) => within(row).queryByText(/sys@test.com/i));
    expect(selfRow).toBeDefined();

    const deactivateBtn = within(selfRow!).getByRole("button", { name: /deactivate/i });
    expect(deactivateBtn).toBeDisabled();
  });

  it("SR-034 sysadmin-only: lifecycle actions absent for admin role", async () => {
    server.use(
      http.get(`${BASE}/accounts`, () => HttpResponse.json(accounts))
    );

    renderPage(adminMe);

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /deactivate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /delete/i })).not.toBeInTheDocument();
  });
});
