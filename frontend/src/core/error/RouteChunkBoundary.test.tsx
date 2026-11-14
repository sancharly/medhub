import { describe, it, expect, vi, afterEach } from "vitest";
import { Suspense } from "react";
import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppErrorBoundary } from "./AppErrorBoundary";
import { RouteChunkBoundary } from "./RouteChunkBoundary";
import { lazyRoute } from "./lazyRoute";
import { theme } from "../theme/theme";

// SR-027 AC 3, SR-026 AC 7, TASK-145: a route chunk that fails to load shows a clear message with a
// retry that imports it again, never a blank route.

const chunkError = () => new TypeError("Failed to fetch dynamically imported module: /assets/x.js");

function Page() {
  return <div>loaded page</div>;
}

function Boom(): never {
  throw new Error("render bug");
}

function Shell({ resetKey, children }: { resetKey: string; children: ReactNode }) {
  return (
    <MuiThemeProvider theme={theme}>
      <AppErrorBoundary>
        <RouteChunkBoundary resetKey={resetKey}>
          <Suspense fallback={<div>waiting</div>}>{children}</Suspense>
        </RouteChunkBoundary>
      </AppErrorBoundary>
    </MuiThemeProvider>
  );
}

afterEach(() => {
  vi.restoreAllMocks();
});

describe("lazy route and RouteChunkBoundary", () => {
  it("lazy route renders after its chunk loads", async () => {
    let release: (m: { default: () => JSX.Element }) => void = () => {};
    const Lazy = lazyRoute(() => new Promise<{ default: () => JSX.Element }>((r) => (release = r)));
    render(
      <Shell resetKey="/a">
        <Lazy />
      </Shell>
    );
    expect(screen.getByText("waiting")).toBeInTheDocument();
    release({ default: Page });
    expect(await screen.findByText("loaded page")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("failed chunk shows the retry message, retry recovers", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const factory = vi
      .fn<[], Promise<{ default: () => JSX.Element }>>()
      .mockRejectedValueOnce(chunkError())
      .mockResolvedValue({ default: Page });
    const Lazy = lazyRoute(factory);
    render(
      <Shell resetKey="/a">
        <Lazy />
      </Shell>
    );
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("This page could not be loaded.");
    expect(factory).toHaveBeenCalledTimes(1);

    await userEvent.setup().click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("loaded page")).toBeInTheDocument();
    expect(factory).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("a retry that fails again offers a page reload", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const reload = vi.fn();
    vi.spyOn(window, "location", "get").mockReturnValue({ ...window.location, reload });
    const factory = vi.fn<[], Promise<{ default: () => JSX.Element }>>(() =>
      Promise.reject(chunkError())
    );
    const Lazy = lazyRoute(factory);
    render(
      <Shell resetKey="/a">
        <Lazy />
      </Shell>
    );
    await screen.findByRole("alert");
    expect(screen.queryByRole("button", { name: "Reload" })).not.toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText(/application may have been updated/i)).toBeInTheDocument();
    expect(factory).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
    await userEvent.setup().click(screen.getByRole("button", { name: "Reload" }));
    expect(reload).toHaveBeenCalledTimes(1);
  });

  it("navigating to a failing route imports its chunk once", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const factory = vi.fn<[], Promise<{ default: () => JSX.Element }>>(() =>
      Promise.reject(chunkError())
    );
    const Bad = lazyRoute(factory);
    const { rerender } = render(
      <Shell resetKey="/a">
        <Page />
      </Shell>
    );
    rerender(
      <Shell resetKey="/bad">
        <Bad />
      </Shell>
    );
    await screen.findByRole("alert");
    await new Promise((r) => setTimeout(r, 50));
    expect(factory).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("alert")).toHaveTextContent("This page could not be loaded.");
    expect(screen.queryByText(/application may have been updated/i)).not.toBeInTheDocument();
  });

  it("moving to another route clears the failure", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const Bad = lazyRoute(() => Promise.reject(chunkError()));
    const { rerender } = render(
      <Shell resetKey="/bad">
        <Bad />
      </Shell>
    );
    await screen.findByRole("alert");
    rerender(
      <Shell resetKey="/good">
        <Page />
      </Shell>
    );
    expect(await screen.findByText("loaded page")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("an error thrown by the page itself is left to the app boundary", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const Lazy = lazyRoute(() => Promise.resolve({ default: Boom }));
    render(
      <Shell resetKey="/a">
        <Lazy />
      </Shell>
    );
    expect(await screen.findByText("Something went wrong")).toBeInTheDocument();
    expect(screen.queryByText(/could not be loaded/)).not.toBeInTheDocument();
  });
});
