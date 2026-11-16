import { describe, it, expect, vi, afterEach } from "vitest";
import { act, render, renderHook, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { delay, http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { queryKeys } from "../api/queryKeys";
import { AttachmentItem } from "../core/clinical/AttachmentItem";
import { GroupModules } from "../core/admin/groups/GroupModules";
import { GroupMembers } from "../core/admin/groups/GroupMembers";
import { useMyModules } from "./useMyModules";

const BASE = "http://localhost/api/v1";

const dicomAttachment = {
  id: "att-1",
  filename: "scan.dcm",
  contentType: "application/dicom",
} as never;

function makeClient() {
  // Mirrors the production defaults that matter here: no focus refetch, retries off.
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });
}

function wrap(client: QueryClient) {
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

/** Serves `/me/modules` from a mutable list and counts the requests. */
function serveModules(initial: string[], latencyMs = 0) {
  const state = { modules: initial, calls: 0, fail: false };
  server.use(
    http.get(`${BASE}/me/modules`, async () => {
      state.calls += 1;
      const modules = state.modules; // the server reads the list here, before the latency
      if (latencyMs) await delay(latencyMs);
      if (state.fail) return new HttpResponse(null, { status: 500 });
      return HttpResponse.json({ modules });
    })
  );
  return state;
}

/** `waitFor` inside `act`, on real timers (Testing Library's `waitFor` polls with the faked setInterval). */
function settle(check: () => void) {
  return act(() => vi.waitFor(check));
}

afterEach(() => {
  vi.useRealTimers();
});

describe("useMyModules (SR-015 AC 5, RISK-004)", () => {
  it("module disabled elsewhere disappears within 60 s", async () => {
    // Only the interval and the clock are faked: MSW keeps real timers. Waits that do not depend
    // on a DOM change use `vi.waitFor`, because Testing Library's `waitFor` polls with setInterval.
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] });
    const state = serveModules(["dicom-viewer"]);
    render(<AttachmentItem attachment={dicomAttachment} />, { wrapper: wrap(makeClient()) });
    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();

    // Another administrator disables the module; this user does nothing.
    state.modules = [];
    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });

    await waitFor(() => expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument());
  });

  it("module enabled elsewhere appears within 60 s", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] });
    const state = serveModules([]);
    render(<AttachmentItem attachment={dicomAttachment} />, { wrapper: wrap(makeClient()) });
    await settle(() => expect(state.calls).toBe(1));
    expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument();

    state.modules = ["dicom-viewer"];
    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });

    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();
  });

  it("remount (next navigation) refetches", async () => {
    const state = serveModules(["dicom-viewer"]);
    const client = makeClient();
    const first = render(<AttachmentItem attachment={dicomAttachment} />, {
      wrapper: wrap(client),
    });
    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();
    first.unmount();

    // Well inside staleTime: only refetchOnMount "always" can trigger the request.
    state.modules = [];
    render(<AttachmentItem attachment={dicomAttachment} />, { wrapper: wrap(client) });

    await waitFor(() => expect(state.calls).toBe(2));
    await waitFor(() => expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument());
  });

  it("failed refetch keeps the last known modules", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] });
    const state = serveModules(["dicom-viewer"]);
    const client = makeClient();
    render(<AttachmentItem attachment={dicomAttachment} />, { wrapper: wrap(client) });
    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();

    state.fail = true;
    const callsBefore = state.calls;
    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    // retry: 1 waits one second, so wait for the final error, not for the first failed request.
    await act(() =>
      vi.waitFor(() => expect(client.getQueryState(queryKeys.myModules)?.status).toBe("error"), {
        timeout: 4000,
      })
    );

    expect(state.calls).toBe(callsBefore + 2);
    expect(screen.getByText("Open in viewer")).toBeInTheDocument();
  });

  it("the change shows within 60 s when the server and the network are slow", async () => {
    // The server reads the list, then 1 s passes before the response arrives. TanStack Query
    // restarts the interval when a response arrives, so a 60 s interval would show a change that
    // lands just after a read only after 60 s plus both latencies (SR-015 AC 5).
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval", "Date"] });
    const state = serveModules(["dicom-viewer"], 1000);
    render(<AttachmentItem attachment={dicomAttachment} />, { wrapper: wrap(makeClient()) });
    expect(await screen.findByText("Open in viewer", {}, { timeout: 3000 })).toBeInTheDocument();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    await settle(() => expect(state.calls).toBe(2));
    state.modules = []; // the change lands right after the server read of this poll
    await act(() => new Promise((r) => setTimeout(r, 1500))); // its (old) response arrives
    expect(screen.getByText("Open in viewer")).toBeInTheDocument();

    // 50 s after that response is the next poll; the change is 50 s old plus the latencies.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(50_000);
    });
    await act(() => new Promise((r) => setTimeout(r, 1500)));

    expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument();
  });

  it("a failed refetch leaves the cached list in place", async () => {
    const state = serveModules(["dicom-viewer"]);
    const client = makeClient();
    renderHook(() => useMyModules(), { wrapper: wrap(client) });
    await waitFor(() => expect(client.getQueryData(queryKeys.myModules)).toEqual(["dicom-viewer"]));

    state.fail = true;
    // retry: 1, so the refetch settles after one second.
    await act(async () => {
      await client.refetchQueries({ queryKey: queryKeys.myModules });
    });

    expect(client.getQueryState(queryKeys.myModules)?.status).toBe("error");
    expect(client.getQueryData(queryKeys.myModules)).toEqual(["dicom-viewer"]);
  });

  it("admin module mutation invalidates myModules", async () => {
    const state = serveModules(["dicom-viewer"]);
    server.use(http.put(`${BASE}/groups/grp-1/modules/dicom-viewer`, () => new HttpResponse(null, { status: 204 })));
    const client = makeClient();
    const user = userEvent.setup();
    render(
      <>
        <AttachmentItem attachment={dicomAttachment} />
        <GroupModules
          groupId="grp-1"
          enabledModules={["dicom-viewer"]}
          installedModules={[
            { moduleKey: "dicom-viewer", name: "DICOM Viewer", version: "1.0", requiredPermissions: [] },
          ]}
        />
      </>,
      { wrapper: wrap(client) }
    );
    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();
    expect(state.calls).toBe(1);

    state.modules = [];
    await user.click(screen.getByRole("switch", { name: "Toggle DICOM Viewer" }));

    await waitFor(() => expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument());
    expect(state.calls).toBe(2);
  });

  it("admin add-member mutation invalidates myModules", async () => {
    const state = serveModules([]);
    server.use(http.post(`${BASE}/groups/grp-1/members`, () => new HttpResponse(null, { status: 204 })));
    const user = userEvent.setup();
    render(
      <>
        <AttachmentItem attachment={dicomAttachment} />
        <GroupMembers groupId="grp-1" members={[]} />
      </>,
      { wrapper: wrap(makeClient()) }
    );
    await waitFor(() => expect(state.calls).toBe(1));
    expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument();

    state.modules = ["dicom-viewer"];
    await user.type(screen.getByLabelText("Account ID or email"), "a9");
    await user.click(screen.getByRole("button", { name: "Add member" }));

    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();
    expect(state.calls).toBe(2);
  });

  it("admin remove-member mutation invalidates myModules", async () => {
    const state = serveModules(["dicom-viewer"]);
    server.use(http.delete(`${BASE}/groups/grp-1/members/a2`, () => new HttpResponse(null, { status: 204 })));
    const client = makeClient();
    const user = userEvent.setup();
    render(
      <>
        <AttachmentItem attachment={dicomAttachment} />
        <GroupMembers
          groupId="grp-1"
          members={[{ accountId: "a2", name: "Bob Manual", membershipSource: "MANUAL" }]}
        />
      </>,
      { wrapper: wrap(client) }
    );
    expect(await screen.findByText("Open in viewer")).toBeInTheDocument();

    state.modules = [];
    await user.click(screen.getByRole("button", { name: "Remove Bob Manual" }));

    await waitFor(() => expect(screen.queryByText("Open in viewer")).not.toBeInTheDocument());
  });
});

// Static check (SR-015 AC 5): one reader of the module list and one spelling of its key.
describe("the my-modules query has one reader", () => {
  const sources = import.meta.glob("/src/**/*.{ts,tsx}", {
    query: "?raw",
    import: "default",
    eager: true,
  }) as Record<string, string>;
  const production = Object.entries(sources).filter(
    ([path]) => !/\.test\.|\.test-d\.|\/generated\/|\/tests\//.test(path)
  );

  it("only useMyModules calls apiClient.listMyModules()", () => {
    const callers = production
      .filter(([, src]) => /apiClient\.listMyModules\(/.test(src))
      .map(([p]) => p);
    expect(callers).toEqual(["/src/modules/useMyModules.ts"]);
  });

  it("only queryKeys.ts spells the myModules key", () => {
    const spellers = production.filter(([, src]) => /"myModules"/.test(src)).map(([p]) => p);
    expect(spellers).toEqual(["/src/api/queryKeys.ts"]);
  });
});
