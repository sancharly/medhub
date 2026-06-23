import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { IdleWarningDialog } from "./IdleWarningDialog";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";

function renderDialog(props: {
  open: boolean;
  expiresAt: number;
  onExtended?: (d: number) => void;
  onLogout?: () => void;
}) {
  return render(
    <MuiThemeProvider theme={theme}>
      <MemoryRouter initialEntries={["/app"]}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route
            path="/app"
            element={
              <IdleWarningDialog
                open={props.open}
                expiresAt={props.expiresAt}
                onExtended={props.onExtended ?? vi.fn()}
                onLogout={props.onLogout ?? vi.fn()}
              />
            }
          />
        </Routes>
      </MemoryRouter>
    </MuiThemeProvider>
  );
}

describe("IdleWarningDialog", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    Object.defineProperty(document, "cookie", { writable: true, value: "csrftoken=csrf-test" });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("shows countdown when open", () => {
    const expiresAt = Date.now() + 2 * 60 * 1000;
    renderDialog({ open: true, expiresAt });
    expect(screen.getByTestId("countdown")).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("Stay signed in calls extend and invokes onExtended", async () => {
    const onExtended = vi.fn();
    const newExpiry = Date.now() + 30 * 60 * 1000;

    server.use(
      http.post(`${BASE}/auth/session/extend`, () =>
        HttpResponse.json({
          expiresAt: new Date(newExpiry).toISOString(),
        })
      )
    );

    renderDialog({
      open: true,
      expiresAt: Date.now() + 2 * 60 * 1000,
      onExtended,
    });

    await userEvent.click(screen.getByRole("button", { name: /stay signed in/i }));

    await waitFor(() => expect(onExtended).toHaveBeenCalled());
    const arg = onExtended.mock.calls[0][0] as number;
    expect(arg).toBeGreaterThan(Date.now());
  });

  it("Log out now calls onLogout", async () => {
    const onLogout = vi.fn();
    renderDialog({
      open: true,
      expiresAt: Date.now() + 2 * 60 * 1000,
      onLogout,
    });

    await userEvent.click(screen.getByRole("button", { name: /log out now/i }));
    expect(onLogout).toHaveBeenCalled();
  });

  it("extend 401 redirects to login", async () => {
    server.use(
      http.post(`${BASE}/auth/session/extend`, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderDialog({
      open: true,
      expiresAt: Date.now() + 2 * 60 * 1000,
    });

    await userEvent.click(screen.getByRole("button", { name: /stay signed in/i }));

    await waitFor(() => {
      expect(screen.getByText("Login Page")).toBeInTheDocument();
    });
  });
});
