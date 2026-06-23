import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { useQuery, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "../tests/setup";

function TestComponent() {
  const { data, isLoading } = useQuery({
    queryKey: ["test"],
    queryFn: () => fetch("http://localhost/api/v1/test").then((r) => r.json()),
  });
  if (isLoading) return <div>loading</div>;
  return <div>{(data as { value: string }).value}</div>;
}

describe("QueryProvider", () => {
  it("child useQuery resolves through provider against MSW mock", async () => {
    server.use(
      http.get("http://localhost/api/v1/test", () =>
        HttpResponse.json({ value: "hello from msw" })
      )
    );

    const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    render(
      <QueryClientProvider client={client}>
        <TestComponent />
      </QueryClientProvider>
    );

    await waitFor(() =>
      expect(screen.getByText("hello from msw")).toBeInTheDocument()
    );
  });
});
