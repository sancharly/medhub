import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { LoginPage } from "./LoginPage";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";

function renderLogin() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/login"]}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/appointments" element={<div>Appointments</div>} />
            <Route path="/patients" element={<div>Patients</div>} />
            <Route path="/admin/users" element={<div>Admin Users</div>} />
            <Route path="/password" element={<div>Change Password</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

const patientUser = { id: "1", email: "p@test.com", userType: "patient", mustChangePassword: false };

describe("LoginPage", () => {
  beforeEach(() => {
    Object.defineProperty(document, "cookie", { writable: true, value: "" });
  });

  it("navigates to role landing on success", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json({
          user: patientUser,
          mustChangePassword: false,
          evictedSession: false,
        })
      )
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "p@test.com");
    await userEvent.type(screen.getByLabelText(/password/i), "pass");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Appointments")).toBeInTheDocument();
    });
  });

  it("shows generic error for wrong password (no field flagged)", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "p@test.com");
    await userEvent.type(screen.getByLabelText(/password/i), "wrong");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByTestId("login-error")).toBeInTheDocument()
    );
    expect(screen.queryByRole("textbox", { name: /email/i })).not.toHaveAttribute("aria-invalid", "true");
  });

  it("shows generic error for unknown email (same message as wrong password)", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "nobody@nowhere.com");
    await userEvent.type(screen.getByLabelText(/password/i), "anything");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() =>
      expect(screen.getByTestId("login-error")).toBeInTheDocument()
    );
  });

  it("routes to /password when mustChangePassword is true", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json({
          user: patientUser,
          mustChangePassword: true,
          evictedSession: false,
        })
      )
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "p@test.com");
    await userEvent.type(screen.getByLabelText(/password/i), "pass");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Change Password")).toBeInTheDocument();
    });
  });

  it("does not write tokens to localStorage or sessionStorage", async () => {
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json({
          user: patientUser,
          mustChangePassword: false,
          evictedSession: false,
        })
      )
    );

    renderLogin();
    await userEvent.type(screen.getByLabelText(/email/i), "p@test.com");
    await userEvent.type(screen.getByLabelText(/password/i), "pass");
    await userEvent.click(screen.getByRole("button", { name: /sign in/i }));

    await waitFor(() => {
      expect(screen.getByText("Appointments")).toBeInTheDocument();
    });

    expect(localStorage.getItem("token")).toBeNull();
    expect(sessionStorage.getItem("token")).toBeNull();
    expect(document.cookie).not.toMatch(/\btoken=/i);
  });
});
