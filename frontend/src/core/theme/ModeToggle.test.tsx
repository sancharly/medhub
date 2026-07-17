import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "./ThemeProvider";
import { ModeToggle } from "./ModeToggle";
import { COLOR_SCHEME_MODE_STORAGE_KEY } from "./theme";

function mockMatchMedia(prefersDark: boolean) {
  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => ({
      matches: query.includes("dark") ? prefersDark : !prefersDark,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
}

describe("ModeToggle", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockMatchMedia(false); // system prefers light by default
  });

  it("renders with an accessible name describing the action", async () => {
    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    expect(
      await screen.findByRole("button", { name: /switch to (dark|light) mode/i })
    ).toBeInTheDocument();
  });

  it("clicking switches the <html> color-scheme attribute without losing a sibling's in-progress input", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <input aria-label="note" />
        <ModeToggle />
      </ThemeProvider>
    );
    const input = screen.getByLabelText("note");
    await user.type(input, "draft text");
    expect(input).toHaveValue("draft text");

    const toggle = await screen.findByRole("button", { name: /switch to dark mode/i });
    await user.click(toggle);

    expect(input).toHaveValue("draft text");
    expect(document.documentElement).toHaveAttribute("data-dark");
  });

  it("persists an explicit choice to localStorage and restores it on the next render of the provider", async () => {
    const user = userEvent.setup();
    const { unmount } = render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    const toggle = await screen.findByRole("button", { name: /switch to dark mode/i });
    await user.click(toggle);
    expect(window.localStorage.getItem(COLOR_SCHEME_MODE_STORAGE_KEY)).toBe("dark");
    unmount();

    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    expect(
      await screen.findByRole("button", { name: /switch to light mode/i })
    ).toBeInTheDocument();
  });

  it("resolves dark mode from the OS preference when no explicit choice is stored", async () => {
    mockMatchMedia(true);
    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    expect(
      await screen.findByRole("button", { name: /switch to light mode/i })
    ).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute("data-dark");
  });
});
