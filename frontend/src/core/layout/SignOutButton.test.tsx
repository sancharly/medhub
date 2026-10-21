import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../../tests/setup";
import { SignOutButton } from "./SignOutButton";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";

function renderButton() {
  return render(
    <MuiThemeProvider theme={theme}>
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/app" element={<SignOutButton />} />
        </Routes>
      </MemoryRouter>
    </MuiThemeProvider>
  );
}

describe("SignOutButton", () => {
  it("renders with an accessible name", () => {
    renderButton();
    expect(screen.getByRole("button", { name: /sign out/i })).toBeInTheDocument();
  });

  it("clicking calls the logout endpoint and navigates to /login", async () => {
    let logoutCalled = false;
    server.use(
      http.post(`${BASE}/auth/logout`, () => {
        logoutCalled = true;
        return new HttpResponse(null, { status: 204 });
      })
    );

    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => expect(screen.getByText("Login Page")).toBeInTheDocument());
    expect(logoutCalled).toBe(true);
  });

  it("navigates to /login even if the logout request fails", async () => {
    server.use(
      http.post(`${BASE}/auth/logout`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    const user = userEvent.setup();
    renderButton();

    await user.click(screen.getByRole("button", { name: /sign out/i }));

    await waitFor(() => expect(screen.getByText("Login Page")).toBeInTheDocument());
  });
});
