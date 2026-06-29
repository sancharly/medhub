import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../../tests/setup";
import { ProfilePage } from "./ProfilePage";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <ProfilePage />
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ProfilePage", () => {
  it("SR-003 AC-2 / SR-007 AC-1: renders name, surname, email, userType from GET /me", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "p@test.com",
          userType: "PATIENT",
          firstName: "Jane",
          surname: "Doe",
          mustChangePassword: false,
        })
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Jane")).toBeInTheDocument();
    });
    expect(screen.getByText("Doe")).toBeInTheDocument();
    expect(screen.getByText("p@test.com")).toBeInTheDocument();
    expect(screen.getByText(/patient/i)).toBeInTheDocument();
  });

  it("SR-003 AC-3: only calls /me, never /accounts/{id}", async () => {
    const accountsRequested = vi.fn();

    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "p@test.com",
          userType: "PATIENT",
          firstName: "Jane",
          surname: "Doe",
          mustChangePassword: false,
        })
      ),
      http.get(`${BASE}/accounts/:id`, () => {
        accountsRequested();
        return HttpResponse.json({});
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Jane")).toBeInTheDocument();
    });

    expect(accountsRequested).not.toHaveBeenCalled();
  });

  it("SR-027.3: shows error detail on 500", async () => {
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(
          {
            type: "/errors/internal",
            title: "Internal Server Error",
            status: 500,
            detail: "Unexpected failure",
          },
          { status: 500, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/error|failed|unavailable/i);
  });
});
