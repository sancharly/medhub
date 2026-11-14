import { describe, it, expect } from "vitest";
import { vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { MutationObserver } from "@tanstack/react-query";
import { AuthError } from "./client";
import { queryClient, setAuthExpiredHandler } from "./queryClient";

describe("queryClient defaults (PRB-067)", () => {
  it("does not retry the exact [me] query on mount", () => {
    expect(queryClient.getQueryDefaults(["me"]).retryOnMount).toBe(false);
  });

  // The [me] default matches by prefix; the consent list must keep retrying on mount.
  it("still retries [me, consents] on mount", async () => {
    queryClient.clear();
    let calls = 0;
    const queryFn = () => {
      calls += 1;
      return calls === 1 ? Promise.reject(new Error("boom")) : Promise.resolve("ok");
    };
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
    const opts = { queryKey: ["me", "consents"], queryFn, retry: false } as const;
    const first = renderHook(() => useQuery(opts), { wrapper });
    await waitFor(() => expect(first.result.current.isError).toBe(true));
    first.unmount();
    const second = renderHook(() => useQuery(opts), { wrapper });
    await waitFor(() => expect(second.result.current.data).toBe("ok"));
    expect(calls).toBe(2);
    queryClient.clear();
  });
});

describe("mutation AuthError handler (TASK-144, SR-030 AC 8)", () => {
  const unauthenticated = () =>
    new AuthError({ type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 });
  const fail = (error: unknown) =>
    new MutationObserver(queryClient, { mutationFn: () => Promise.reject(error) })
      .mutate()
      .catch(() => undefined);

  it("fires the handler once for concurrent AuthErrors and again after re-registration", async () => {
    const handler = vi.fn();
    const unregister = setAuthExpiredHandler(handler);
    await Promise.all([fail(unauthenticated()), fail(unauthenticated())]);
    expect(handler).toHaveBeenCalledTimes(1);

    setAuthExpiredHandler(handler);
    await fail(unauthenticated());
    expect(handler).toHaveBeenCalledTimes(2);
    unregister();
  });

  it("ignores errors that are not AuthError", async () => {
    const handler = vi.fn();
    const unregister = setAuthExpiredHandler(handler);
    await fail(new Error("boom"));
    expect(handler).not.toHaveBeenCalled();
    unregister();
  });
});
