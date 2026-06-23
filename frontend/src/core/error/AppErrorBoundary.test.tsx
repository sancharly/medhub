import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppErrorBoundary } from "./AppErrorBoundary";
import { theme } from "../theme/theme";

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
  );
}

function Bomb({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) throw new Error("Test render error");
  return <div>Safe content</div>;
}

describe("AppErrorBoundary", () => {
  it("renders children normally when no error", () => {
    render(
      <Wrapper>
        <AppErrorBoundary>
          <div>Child content</div>
        </AppErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByText("Child content")).toBeInTheDocument();
  });

  it("shows fallback when child throws", () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <Wrapper>
        <AppErrorBoundary>
          <Bomb shouldThrow={true} />
        </AppErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByTestId("error-fallback")).toBeInTheDocument();
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    consoleSpy.mockRestore();
  });

  it("shows Try again button and shell remains intact", async () => {
    const consoleSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <Wrapper>
        <div data-testid="shell">shell</div>
        <AppErrorBoundary>
          <Bomb shouldThrow={true} />
        </AppErrorBoundary>
      </Wrapper>
    );
    expect(screen.getByTestId("shell")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
    consoleSpy.mockRestore();
  });
});
