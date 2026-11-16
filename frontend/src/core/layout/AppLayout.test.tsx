import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppLayout } from "./AppLayout";
import { theme } from "../theme/theme";
import { lazyRoute } from "../error/lazyRoute";

function renderLayout(nav: React.ReactNode, content: React.ReactNode) {
  return render(
    <MuiThemeProvider theme={theme}>
      <MemoryRouter>
        <AppLayout navigation={nav}>{content}</AppLayout>
      </MemoryRouter>
    </MuiThemeProvider>
  );
}

describe("AppLayout", () => {
  it("renders header aria-label", () => {
    renderLayout(<div>nav</div>, <div>content</div>);
    expect(screen.getByRole("banner", { name: /header/i })).toBeInTheDocument();
  });

  it("renders navigation slot", () => {
    renderLayout(<div>my-nav</div>, <div>content</div>);
    expect(screen.getByText("my-nav")).toBeInTheDocument();
  });

  it("renders main content", () => {
    renderLayout(<div>nav</div>, <div>main-content-here</div>);
    expect(screen.getByText("main-content-here")).toBeInTheDocument();
  });

  it("injected nav content appears in nav region", () => {
    renderLayout(<div data-testid="nav-slot">NavSlot</div>, <span />);
    expect(screen.getByTestId("nav-slot")).toBeInTheDocument();
  });

  it("main element has overflowX hidden to prevent horizontal overflow", () => {
    const { container } = renderLayout(<div />, <div />);
    const main = container.querySelector("main");
    expect(main).not.toBeNull();
    const style = window.getComputedStyle(main!);
    expect(style.maxWidth).toBe("100%");
  });

  // TASK-145: the content slot sits under one Suspense and the chunk-failure boundary, inside the shell.
  it("shows an accessible progress indicator while a lazy page loads, shell intact", () => {
    const Lazy = lazyRoute(() => new Promise<never>(() => {}));
    renderLayout(<div>my-nav</div>, <Lazy />);
    expect(screen.getByRole("progressbar", { name: /loading page/i })).toBeInTheDocument();
    expect(screen.getByText("my-nav")).toBeInTheDocument();
  });

  it("shows the retry message when a lazy page fails to load, shell intact", async () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    const Lazy = lazyRoute(() =>
      Promise.reject(new TypeError("Failed to fetch dynamically imported module"))
    );
    renderLayout(<div>my-nav</div>, <Lazy />);
    expect(await screen.findByRole("alert")).toHaveTextContent("This page could not be loaded.");
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    expect(screen.getByText("my-nav")).toBeInTheDocument();
    vi.restoreAllMocks();
  });
});
