import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse, delay } from "msw";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { theme } from "../core/theme/theme";
import { queryClient } from "../api/queryClient";
import { queryKeys } from "../api/queryKeys";
import { RequireAuth } from "./RequireAuth";
import { SessionActivityProvider } from "./SessionActivityProvider";
import { AttachmentUpload } from "../core/clinical/AttachmentUpload";
import { ChangePasswordPage } from "./ChangePasswordPage";

const BASE = "http://localhost/api/v1";

const me = (sessionExpiresInSeconds: number) => ({
  id: "1",
  email: "a@b.com",
  userType: "PATIENT",
  state: "ACTIVE",
  firstName: "A",
  surname: "B",
  dateOfBirth: null,
  createdAt: "2026-01-01T00:00:00Z",
  mustChangePassword: false,
  sessionExpiresInSeconds,
});

const unauthenticated = () =>
  HttpResponse.json(
    { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401, detail: "Authentication is required." },
    { status: 401, headers: { "Content-Type": "application/problem+json" } }
  );

const visited: string[] = [];
function LocationProbe() {
  const location = useLocation();
  visited.push(`${location.pathname}${location.search}`);
  return null;
}

function renderTree(children: React.ReactNode = <div>Home</div>) {
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/home"]}>
          <LocationProbe />
          <Routes>
            <Route path="/login" element={<div>Login Page</div>} />
            <Route element={<RequireAuth />}>
              <Route
                path="/home"
                element={<SessionActivityProvider>{children}</SessionActivityProvider>}
              />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

const minutes = (m: number) => m * 60 * 1000;

describe("SessionActivityProvider", () => {
  beforeEach(() => {
    visited.length = 0;
    queryClient.clear();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    queryClient.clear();
  });

  it.each([
    [30, 28],
    [7, 5],
  ])(
    "deadline follows the server-reported expiry (%i min), not 15 min: warning at %i min",
    async (reported, warnAt) => {
      server.use(http.get(`${BASE}/me`, () => HttpResponse.json(me(reported * 60))));
      renderTree();
      await screen.findByText("Home");

      act(() => {
        vi.advanceTimersByTime(minutes(warnAt) - 5000);
      });
      expect(screen.queryByRole("dialog")).toBeNull();

      act(() => {
        vi.advanceTimersByTime(10000);
      });
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
    }
  );

  it.each([10, -10])(
    "client clock skew of %i min between request and response does not move the deadline",
    async (skewMinutes) => {
      server.use(
        http.get(`${BASE}/me`, async () => {
          await delay(100);
          return HttpResponse.json(me(15 * 60));
        })
      );
      renderTree();
      // The client clock jumps while the request is in flight.
      vi.setSystemTime(Date.now() + minutes(skewMinutes));
      await screen.findByText("Home");

      // 15 min reported, warning 2 min before: 13 min after the response was received.
      act(() => {
        vi.advanceTimersByTime(minutes(13) - 5000);
      });
      expect(screen.queryByRole("dialog")).toBeNull();
      act(() => {
        vi.advanceTimersByTime(10000);
      });
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
    }
  );

  it("an expired session gives one redirect and no repeated me requests", async () => {
    let calls = 0;
    server.use(
      http.get(`${BASE}/me`, () => {
        calls += 1;
        return unauthenticated();
      })
    );
    renderTree();
    await screen.findByText("Login Page");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(calls).toBe(1);
    expect(visited.filter((l) => l.startsWith("/login"))).toHaveLength(1);
  });

  it("a mutation's AuthError redirects once and clears the cache (the upload included)", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))),
      http.post(`${BASE}/clinical-entries/e1/attachments`, async () => {
        await delay(50);
        return unauthenticated();
      })
    );
    renderTree(<AttachmentUpload entryId="e1" patientId="p1" />);
    const input = await screen.findByLabelText("Upload file");
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    // Two uploads in flight: both fail with 401, only one redirect may happen.
    await user.upload(input, new File(["x"], "a.pdf"));
    await user.upload(input, new File(["y"], "b.pdf"));

    await screen.findByText("Login Page");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
    await waitFor(() => expect(queryClient.getQueryData(queryKeys.me)).toBeUndefined());
  });
  it("the session ends at the reported deadline: warning at 13 min, sign-in at 15 min", async () => {
    server.use(http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))));
    renderTree();
    await screen.findByText("Home");

    act(() => {
      vi.advanceTimersByTime(minutes(13) + 1000);
    });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(visited.some((l) => l.startsWith("/login"))).toBe(false);

    act(() => {
      vi.advanceTimersByTime(minutes(2));
    });
    await waitFor(() => expect(visited).toContain("/login?timeout=1"));
  });

  it("a reported expiry of 0 is an expired session: one redirect to sign-in", async () => {
    server.use(http.get(`${BASE}/me`, () => HttpResponse.json(me(0))));
    renderTree();
    await screen.findByText("Login Page");
    expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
  });

  it("a wrong current password shows its message and does not sign the user out", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))),
      http.post(`${BASE}/auth/password`, () =>
        HttpResponse.json(
          {
            type: "/errors/validation-error",
            title: "Validation Error",
            status: 400,
            detail: "Current password is incorrect.",
            errors: [
              { field: "currentPassword", rule: "CURRENT_PASSWORD_INCORRECT", message: "Current password is incorrect." },
            ],
          },
          { status: 400, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );
    renderTree(<ChangePasswordPage />);
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    await user.type(await screen.findByLabelText(/current password/i), "wrong");
    await user.type(screen.getByLabelText(/^New password/i), "Abc123!@#xyz12");
    await user.type(screen.getByLabelText(/confirm new password/i), "Abc123!@#xyz12");
    await user.click(screen.getByRole("button", { name: /change password/i }));

    expect(await screen.findByTestId("server-error")).toHaveTextContent("Current password is incorrect.");
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(visited.some((l) => l.startsWith("/login"))).toBe(false);
  });
});
