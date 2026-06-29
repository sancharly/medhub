import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { RequireAuth } from "./RequireAuth";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";

function renderWithAuth(initialPath: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[initialPath]}>
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route element={<RequireAuth />}>
              <Route path="/dashboard" element={<div>Dashboard</div>} />
              <Route path="/profile" element={<div>Profile</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("RequireAuth", () => {
  it("redirects unauthenticated user to /login preserving destination", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderWithAuth("/dashboard");

    await waitFor(() =>
      expect(screen.getByText("Login Page")).toBeInTheDocument()
    );
  });

  it("renders children for authenticated user", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "a@b.com",
          userType: "PATIENT",
          mustChangePassword: false,
        })
      )
    );

    renderWithAuth("/dashboard");

    await waitFor(() =>
      expect(screen.getByText("Dashboard")).toBeInTheDocument()
    );
  });
});
