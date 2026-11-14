import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useLocation, useNavigate, type NavigateFunction } from "react-router-dom";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
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
let navigateProbe: NavigateFunction;
function LocationProbe() {
  const location = useLocation();
  navigateProbe = useNavigate();
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

// A mounted observer of a clinical query, to catch a cache clear that recreates it.
function ClinicalProbe() {
  const { data } = useQuery({
    queryKey: ["clinical", "e1"],
    queryFn: () => new Promise<string>(() => undefined),
    staleTime: Infinity,
  });
  return <div>{data}</div>;
}

const minutes = (m: number) => m * 60 * 1000;

describe("SessionActivityProvider", () => {
  beforeEach(() => {
    visited.length = 0;
    queryClient.clear();
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // The client ends the session at its own timeout (PRB-089); tests that care override this.
    server.use(http.post(`${BASE}/auth/logout`, () => new HttpResponse(null, { status: 204 })));
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
    let meCalls = 0;
    server.use(
      http.get(`${BASE}/me`, () => {
        meCalls += 1;
        return HttpResponse.json(me(15 * 60));
      }),
      http.post(`${BASE}/clinical-entries/e1/attachments`, async () => {
        await delay(50);
        return unauthenticated();
      })
    );
    renderTree(
      <>
        <AttachmentUpload entryId="e1" patientId="p1" />
        <ClinicalProbe />
      </>
    );
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
    // Nothing recreates the cleared queries or asks the server again (SR-030 AC 8).
    expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    expect(meCalls).toBe(1);
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

  describe("deadline only from server responses, the timeout ends the session", () => {
    const mouseActivity = () => {
      window.dispatchEvent(new MouseEvent("mousemove"));
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
      window.dispatchEvent(new MouseEvent("click"));
      window.dispatchEvent(new Event("scroll"));
    };

    function ClinicalView() {
      const { data } = useQuery({
        queryKey: ["clinical", "e1"],
        queryFn: () => new Promise<string>(() => undefined),
        staleTime: Infinity,
      });
      return <div>{data}</div>;
    }

    function useLogoutHandler(respond: () => Response) {
      const calls = { logout: 0, me: 0 };
      server.use(
        http.get(`${BASE}/me`, () => {
          calls.me += 1;
          return HttpResponse.json(me(15 * 60));
        }),
        http.post(`${BASE}/auth/logout`, () => {
          calls.logout += 1;
          return respond();
        })
      );
      return calls;
    }

    it("reading without requests is warned at 13 min and signed out at 15 min", async () => {
      server.use(http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))));
      renderTree();
      await screen.findByText("Home");

      for (let i = 0; i < 12; i++) {
        act(() => {
          vi.advanceTimersByTime(minutes(1));
          mouseActivity();
        });
      }
      expect(screen.queryByRole("dialog")).toBeNull();
      act(() => {
        vi.advanceTimersByTime(minutes(1) + 1000);
        mouseActivity();
      });
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
      expect(visited.some((l) => l.startsWith("/login"))).toBe(false);

      act(() => {
        vi.advanceTimersByTime(minutes(2));
      });
      await waitFor(() => expect(visited).toContain("/login?timeout=1"));
    });

    it("Extend re-arms from expiresInSeconds", async () => {
      server.use(
        http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))),
        http.post(`${BASE}/auth/session/extend`, () =>
          HttpResponse.json({ expiresInSeconds: 20 * 60 })
        )
      );
      renderTree();
      await screen.findByText("Home");
      act(() => {
        vi.advanceTimersByTime(minutes(13) + 1000);
      });
      await screen.findByRole("dialog");

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      await user.click(screen.getByRole("button", { name: /stay signed in/i }));
      await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());

      // 20 min reported at receipt: warning 18 min later, not at the old 15 min deadline.
      act(() => {
        vi.advanceTimersByTime(minutes(17));
      });
      expect(screen.queryByRole("dialog")).toBeNull();
      expect(visited.some((l) => l.startsWith("/login"))).toBe(false);
      act(() => {
        vi.advanceTimersByTime(minutes(1) + 1000);
      });
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
    });

    it("a refreshed me re-arms", async () => {
      server.use(http.get(`${BASE}/me`, () => HttpResponse.json(me(15 * 60))));
      renderTree();
      await screen.findByText("Home");

      act(() => {
        vi.advanceTimersByTime(minutes(10));
      });
      await act(async () => {
        await queryClient.invalidateQueries({ queryKey: queryKeys.me, exact: true });
        // Let the query's change notification reach the provider before time moves on.
        await vi.advanceTimersByTimeAsync(10);
      });

      // The old warning time (13 min) passes without a warning.
      act(() => {
        vi.advanceTimersByTime(minutes(5));
      });
      expect(screen.queryByRole("dialog")).toBeNull();
      // 10 + 13 = 23 min.
      act(() => {
        vi.advanceTimersByTime(minutes(8) + 1000);
      });
      expect(await screen.findByRole("dialog")).toBeInTheDocument();
    });

    it("timeout logs out, clears the cache and redirects once", async () => {
      const calls = useLogoutHandler(() => new HttpResponse(null, { status: 204 }));
      renderTree();
      await screen.findByText("Home");
      queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");

      act(() => {
        vi.advanceTimersByTime(minutes(15) + 1000);
      });
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(calls.logout).toBe(1);
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
      expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
      expect(calls.me).toBe(1);
    });

    it.each([
      ["a 401", () => unauthenticated()],
      ["a network error", () => HttpResponse.error()],
    ])("timeout still clears and redirects when logout fails with %s", async (_label, respond) => {
      const calls = useLogoutHandler(respond);
      renderTree();
      await screen.findByText("Home");
      queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");

      act(() => {
        vi.advanceTimersByTime(minutes(15) + 1000);
      });
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(calls.logout).toBe(1);
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
      expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
      expect(calls.me).toBe(1);
    });

    it("redirects without waiting for logout to answer", async () => {
      useLogoutHandler(() => new HttpResponse(null, { status: 204 }));
      server.use(
        http.post(`${BASE}/auth/logout`, async () => {
          await delay("infinite");
          return new HttpResponse(null, { status: 204 });
        })
      );
      renderTree();
      await screen.findByText("Home");

      act(() => {
        vi.advanceTimersByTime(minutes(15) + 1000);
      });

      expect(await screen.findByText("Login Page")).toBeInTheDocument();
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
    });

    it("Back after a timeout shows no clinical data", async () => {
      let releaseMe: () => void = () => undefined;
      const meGate = new Promise<void>((resolve) => {
        releaseMe = resolve;
      });
      let meCalls = 0;
      server.use(
        http.get(`${BASE}/me`, async () => {
          meCalls += 1;
          if (meCalls > 1) await meGate;
          return HttpResponse.json(me(15 * 60));
        }),
        http.post(`${BASE}/auth/logout`, () => new HttpResponse(null, { status: 204 }))
      );
      renderTree(<ClinicalView />);
      await waitFor(() => expect(queryClient.getQueryData(queryKeys.me)).toBeDefined());
      act(() => {
        queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");
      });
      expect(await screen.findByText("Patient has hypertension")).toBeInTheDocument();

      act(() => {
        vi.advanceTimersByTime(minutes(15) + 1000);
      });
      await screen.findByText("Login Page");

      act(() => {
        navigateProbe(-1);
      });
      await waitFor(() => expect(visited[visited.length - 1]).toBe("/home"));

      // `me` has not answered: RequireAuth renders nothing, and the cache holds no clinical text.
      expect(screen.queryByText("Patient has hypertension")).toBeNull();
      expect(screen.queryByText("Login Page")).toBeNull();
      expect(queryClient.getQueryData(["clinical", "e1"])).toBeUndefined();

      releaseMe();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000);
      });
      expect(screen.queryByText("Patient has hypertension")).toBeNull();
    });

    it("clock jump with the warning open: one logout, an empty cache and one redirect", async () => {
      const calls = useLogoutHandler(() => new HttpResponse(null, { status: 204 }));
      renderTree();
      await screen.findByText("Home");
      queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");
      act(() => {
        vi.advanceTimersByTime(minutes(13) + 1000);
      });
      await screen.findByRole("dialog");

      // A suspended tab or a sleeping laptop: the clock jumps past the deadline, so the dialog's
      // overdue tick is due before the expiry timeout.
      vi.setSystemTime(Date.now() + minutes(5));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(600);
      });
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(calls.logout).toBe(1);
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
      expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
      expect(calls.me).toBe(1);
    });

    it("the dialog's tick and the expiry timer firing in one pass log out once", async () => {
      const calls = useLogoutHandler(() => new HttpResponse(null, { status: 204 }));
      renderTree();
      await screen.findByText("Home");
      act(() => {
        vi.advanceTimersByTime(minutes(13) + 1000);
      });
      await screen.findByRole("dialog");

      // Both are overdue in the same pass and no render happens between them.
      vi.setSystemTime(Date.now() + minutes(5));
      act(() => {
        vi.advanceTimersByTime(minutes(3));
      });
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(calls.logout).toBe(1);
      expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);
    });

    it("extend 401 then Back shows no clinical data", async () => {
      let releaseMe: () => void = () => undefined;
      const meGate = new Promise<void>((resolve) => {
        releaseMe = resolve;
      });
      let meCalls = 0;
      let logoutCalls = 0;
      server.use(
        http.get(`${BASE}/me`, async () => {
          meCalls += 1;
          if (meCalls > 1) await meGate;
          return HttpResponse.json(me(15 * 60));
        }),
        http.post(`${BASE}/auth/session/extend`, () => unauthenticated()),
        http.post(`${BASE}/auth/logout`, () => {
          logoutCalls += 1;
          return new HttpResponse(null, { status: 204 });
        })
      );
      renderTree(<ClinicalView />);
      await waitFor(() => expect(queryClient.getQueryData(queryKeys.me)).toBeDefined());
      act(() => {
        queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");
      });
      expect(await screen.findByText("Patient has hypertension")).toBeInTheDocument();
      act(() => {
        vi.advanceTimersByTime(minutes(13) + 1000);
      });
      await screen.findByRole("dialog");

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      await user.click(screen.getByRole("button", { name: /stay signed in/i }));
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000);
      });
      expect(logoutCalls).toBe(1);
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
      expect(visited.filter((l) => l === "/login?timeout=1")).toHaveLength(1);

      act(() => {
        navigateProbe(-1);
      });
      await waitFor(() => expect(visited[visited.length - 1]).toBe("/home"));
      expect(screen.queryByText("Patient has hypertension")).toBeNull();
      expect(queryClient.getQueryData(["clinical", "e1"])).toBeUndefined();

      releaseMe();
      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000);
      });
      expect(screen.queryByText("Patient has hypertension")).toBeNull();
    });

    it("Log out now logs out once, clears the cache and does not ask the server again", async () => {
      const calls = useLogoutHandler(() => new HttpResponse(null, { status: 204 }));
      renderTree(<ClinicalProbe />);
      await waitFor(() => expect(queryClient.getQueryData(queryKeys.me)).toBeDefined());
      act(() => {
        queryClient.setQueryData(["clinical", "e1"], "Patient has hypertension");
      });
      act(() => {
        vi.advanceTimersByTime(minutes(13) + 1000);
      });
      await screen.findByRole("dialog");

      const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
      await user.click(screen.getByRole("button", { name: /log out now/i }));
      await screen.findByText("Login Page");
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2000);
      });

      expect(calls.logout).toBe(1);
      expect(queryClient.getQueryCache().getAll()).toHaveLength(0);
      expect(calls.me).toBe(1);
    });
  });
});
