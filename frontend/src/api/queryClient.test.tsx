import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";
import { queryClient } from "./queryClient";

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
