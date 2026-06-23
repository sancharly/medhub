import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { ForcedPasswordGate } from "./ForcedPasswordGate";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";

function renderGate(initialPath: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[initialPath]}>
          <Routes>
            <Route path="/login" element={<div>Login</div>} />
            <Route element={<ForcedPasswordGate />}>
              <Route path="/password" element={<div>Change Password</div>} />
              <Route path="/profile" element={<div>Profile</div>} />
              <Route path="/appointments" element={<div>Appointments</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ForcedPasswordGate", () => {
  it("redirects to /password when mustChangePassword is true", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "a@b.com",
          userType: "patient",
          mustChangePassword: true,
        })
      )
    );

    renderGate("/appointments");

    await waitFor(() =>
      expect(screen.getByText("Change Password")).toBeInTheDocument()
    );
  });

  it("allows navigation normally when mustChangePassword is false", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({
          id: "1",
          email: "a@b.com",
          userType: "patient",
          mustChangePassword: false,
        })
      )
    );

    renderGate("/appointments");

    await waitFor(() =>
      expect(screen.getByText("Appointments")).toBeInTheDocument()
    );
  });
});
