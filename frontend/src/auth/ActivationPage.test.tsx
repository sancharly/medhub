import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { ActivationPage } from "./ActivationPage";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";
const TOKEN = "valid-token-abc";
const EXPIRED = "expired-token-xyz";

function renderActivation(token: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/activation/${token}`]}>
          <Routes>
            <Route path="/activation/:token" element={<ActivationPage />} />
            <Route path="/login" element={<div>Login</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ActivationPage", () => {
  it("valid token shows password form", async () => {
    server.use(
      http.get(`${BASE}/activation/${TOKEN}`, () => new HttpResponse(null, { status: 200 }))
    );

    renderActivation(TOKEN);

    await waitFor(() =>
      expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument()
    );
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
  });

  it("expired/invalid token shows no-form message", async () => {
    server.use(
      http.get(`${BASE}/activation/${EXPIRED}`, () =>
        HttpResponse.json(
          { type: "/errors/not-found", title: "Not Found", status: 404 },
          { status: 404, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderActivation(EXPIRED);

    await waitFor(() =>
      expect(screen.getByTestId("invalid-token-message")).toBeInTheDocument()
    );
    expect(screen.queryByLabelText(/password/i)).not.toBeInTheDocument();
  });

  it("mismatched passwords shows non-disclosing message and disables submit", async () => {
    server.use(
      http.get(`${BASE}/activation/${TOKEN}`, () => new HttpResponse(null, { status: 200 }))
    );

    renderActivation(TOKEN);

    await waitFor(() =>
      expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument()
    );

    await userEvent.type(screen.getByLabelText(/^Password/i), "Abc123!@#xyz");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "Different1!xyz");
    await userEvent.click(screen.getByRole("button", { name: /set password/i }));

    expect(screen.getByTestId("mismatch-error")).toBeInTheDocument();
    expect(screen.getByTestId("mismatch-error").textContent).not.toMatch(/password.*(too|weak|rule)/i);
  });

  it("server 400 validation-error shows field-level message", async () => {
    server.use(
      http.get(`${BASE}/activation/${TOKEN}`, () => new HttpResponse(null, { status: 200 })),
      http.post(`${BASE}/activation/${TOKEN}`, () =>
        HttpResponse.json(
          {
            type: "/errors/validation-error",
            title: "Validation failed",
            status: 400,
            errors: [{ field: "password", message: "Password must contain at least one special character" }],
          },
          { status: 400, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderActivation(TOKEN);
    await waitFor(() => expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument());

    await userEvent.type(screen.getByLabelText(/^Password/i), "Abcdefgh12345");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "Abcdefgh12345");
    await userEvent.click(screen.getByRole("button", { name: /set password/i }));

    await waitFor(() =>
      expect(screen.getByTestId("field-error")).toBeInTheDocument()
    );
    expect(screen.getByTestId("field-error").textContent).toMatch(/special/i);
  });

  it("successful activation routes to /login without session", async () => {
    server.use(
      http.get(`${BASE}/activation/${TOKEN}`, () => new HttpResponse(null, { status: 200 })),
      http.post(`${BASE}/activation/${TOKEN}`, () => new HttpResponse(null, { status: 204 }))
    );

    renderActivation(TOKEN);
    await waitFor(() => expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument());

    await userEvent.type(screen.getByLabelText(/^Password/i), "Abc123!@#valid");
    await userEvent.type(screen.getByLabelText(/confirm password/i), "Abc123!@#valid");
    await userEvent.click(screen.getByRole("button", { name: /set password/i }));

    await waitFor(() => expect(screen.getByText("Login")).toBeInTheDocument());

    expect(localStorage.getItem("token")).toBeNull();
    expect(sessionStorage.getItem("token")).toBeNull();
    expect(document.cookie).not.toMatch(/\btoken=/i);
  });
});
