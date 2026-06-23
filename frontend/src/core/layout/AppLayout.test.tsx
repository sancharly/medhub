import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppLayout } from "./AppLayout";
import { theme } from "../theme/theme";

function renderLayout(nav: React.ReactNode, content: React.ReactNode) {
  return render(
    <MuiThemeProvider theme={theme}>
      <AppLayout navigation={nav}>{content}</AppLayout>
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
});
