import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ThemeProvider } from "./ThemeProvider";
import { ModeToggle } from "./ModeToggle";
import { COLOR_SCHEME_MODE_STORAGE_KEY } from "./theme";

/**
 * Mocks `window.matchMedia("(prefers-color-scheme: dark)")`. MUI's
 * useColorScheme listens via the deprecated `addListener` API (for Safari/iOS
 * compatibility), invoking the handler with the MediaQueryList itself. The
 * returned `triggerChange` helper flips `matches` and re-invokes every
 * registered listener, simulating a live OS preference change (SR-039 AC-3).
 */
function mockMatchMedia(prefersDark: boolean) {
  let currentPrefersDark = prefersDark;
  const darkQueryListeners: Array<(mql: { matches: boolean }) => void> = [];

  Object.defineProperty(window, "matchMedia", {
    writable: true,
    configurable: true,
    value: vi.fn().mockImplementation((query: string) => {
      const isDarkQuery = query.includes("dark");
      const mql = {
        get matches() {
          return isDarkQuery ? currentPrefersDark : !currentPrefersDark;
        },
        media: query,
        onchange: null,
        addListener: vi.fn((cb: (mql: { matches: boolean }) => void) => {
          if (isDarkQuery) darkQueryListeners.push(cb);
        }),
        removeListener: vi.fn(),
        addEventListener: vi.fn((event: string, cb: (mql: { matches: boolean }) => void) => {
          if (isDarkQuery && event === "change") darkQueryListeners.push(cb);
        }),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      };
      return mql;
    }),
  });

  return {
    triggerChange(newPrefersDark: boolean) {
      currentPrefersDark = newPrefersDark;
      darkQueryListeners.forEach((cb) => cb({ matches: newPrefersDark }));
    },
  };
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

  it("SR-039 AC-1: is operable by keyboard (Enter activates the toggle)", async () => {
    const user = userEvent.setup();
    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    const toggle = await screen.findByRole("button", { name: /switch to dark mode/i });

    toggle.focus();
    expect(toggle).toHaveFocus();
    await user.keyboard("{Enter}");

    expect(await screen.findByRole("button", { name: /switch to light mode/i })).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute("data-dark");
  });

  it("SR-039 AC-3: follows a live OS preference change while no explicit choice exists", async () => {
    const mq = mockMatchMedia(false); // system starts light
    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    expect(await screen.findByRole("button", { name: /switch to dark mode/i })).toBeInTheDocument();

    act(() => {
      mq.triggerChange(true); // system switches to dark
    });

    expect(await screen.findByRole("button", { name: /switch to light mode/i })).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute("data-dark");
  });

  it("SR-039 AC-4: an explicit choice overrides a conflicting system preference across remount", async () => {
    const user = userEvent.setup();
    mockMatchMedia(false); // system prefers light

    const { unmount } = render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );
    const toggle = await screen.findByRole("button", { name: /switch to dark mode/i });
    await user.click(toggle); // explicit choice: dark
    expect(window.localStorage.getItem(COLOR_SCHEME_MODE_STORAGE_KEY)).toBe("dark");
    unmount();

    // System preference now conflicts with the stored explicit choice.
    mockMatchMedia(true);
    render(
      <ThemeProvider>
        <ModeToggle />
      </ThemeProvider>
    );

    expect(await screen.findByRole("button", { name: /switch to light mode/i })).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute("data-dark");
    expect(document.documentElement).not.toHaveAttribute("data-light");
  });
});
