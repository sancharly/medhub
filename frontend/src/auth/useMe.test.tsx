/// <reference types="vite/client" />
import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { useMe } from "./useMe";

const BASE = "http://localhost/api/v1";

describe("useMe", () => {
  it("does not retry a failed request (one retry policy, SR-030 AC 8)", async () => {
    let calls = 0;
    server.use(
      http.get(`${BASE}/me`, () => {
        calls += 1;
        return new HttpResponse(null, { status: 500 });
      })
    );
    // A client whose default would retry three times: useMe must override it.
    const client = new QueryClient({ defaultOptions: { queries: { retry: 3, retryDelay: 1 } } });
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    );
    const { result } = renderHook(() => useMe(), { wrapper });
    await waitFor(() => expect(result.current.isError).toBe(true));
    await new Promise((r) => setTimeout(r, 50));
    expect(calls).toBe(1);
  });
});

// Static check (SR-030 AC 8): one reader of the `me` query.
describe("the me query has one reader", () => {
  const sources = import.meta.glob("/src/**/*.{ts,tsx}", {
    query: "?raw",
    import: "default",
    eager: true,
  }) as Record<string, string>;
  const production = Object.entries(sources).filter(
    ([path]) => !/\.test\.|\.test-d\.|\/generated\/|\/tests\//.test(path)
  );

  it("only useMe calls apiClient.me()", () => {
    const callers = production.filter(([, src]) => /apiClient\.me\(/.test(src)).map(([p]) => p);
    expect(callers).toEqual(["/src/auth/useMe.ts"]);
  });

  it("only queryKeys.ts spells the me key", () => {
    const spellers = production
      .filter(([, src]) => /\[\s*"me"/.test(src))
      .map(([p]) => p);
    expect(spellers).toEqual(["/src/api/queryKeys.ts"]);
  });
});
