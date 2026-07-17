import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import {
  theme,
  COLOR_SCHEME_MODE_STORAGE_KEY,
  COLOR_SCHEME_ATTRIBUTES,
  COLOR_SCHEME_PAGE_BACKGROUND,
} from "./theme";

describe("MUI theme", () => {
  it("minimum touch target is >=44px for ButtonBase", () => {
    const buttonBase = theme.components?.MuiButtonBase?.styleOverrides?.root as {
      minHeight: number;
      minWidth: number;
    };
    expect(buttonBase.minHeight).toBeGreaterThanOrEqual(44);
    expect(buttonBase.minWidth).toBeGreaterThanOrEqual(44);
  });

  it("minimum touch target is >=44px for IconButton", () => {
    const iconButton = theme.components?.MuiIconButton?.styleOverrides?.root as {
      minHeight: number;
      minWidth: number;
    };
    expect(iconButton.minHeight).toBeGreaterThanOrEqual(44);
    expect(iconButton.minWidth).toBeGreaterThanOrEqual(44);
  });

  it("has primary color defined", () => {
    expect(theme.palette.primary.main).toBeTruthy();
  });

  it("uses 8px spacing unit", () => {
    // Under CSS variables, resolved spacing is a var() expression with an 8px
    // fallback rather than a literal string (ADR-0014) — same 8px unit, new token source.
    expect(theme.spacing(1)).toBe("var(--mui-spacing, 8px)");
  });

  describe("colorSchemes", () => {
    it.each(["light", "dark"] as const)("%s scheme defines background and text tokens", (scheme) => {
      const palette = theme.colorSchemes[scheme]?.palette;
      expect(palette?.background.default).toBeTruthy();
      expect(palette?.background.paper).toBeTruthy();
      expect(palette?.text.primary).toBeTruthy();
      expect(palette?.text.secondary).toBeTruthy();
      expect(palette?.primary.main).toBeTruthy();
    });

    it("light scheme matches ADD-001 §2.1 hex values", () => {
      const palette = theme.colorSchemes.light?.palette;
      expect(palette?.background.default).toBe("#F4F7F6");
      expect(palette?.background.paper).toBe("#FFFFFF");
      expect(palette?.text.primary).toBe("#16211F");
      expect(palette?.text.secondary).toBe("#52605D");
      expect(palette?.primary.main).toBe("#0E7C6B");
      expect(palette?.success.main).toBe("#1F7A47");
      expect(palette?.warning.main).toBe("#9A6402");
      expect(palette?.error.main).toBe("#C03D33");
      expect(palette?.info.main).toBe("#266DA1");
    });

    it("dark scheme matches ADD-001 §2.2 hex values", () => {
      const palette = theme.colorSchemes.dark?.palette;
      expect(palette?.background.default).toBe("#0E1413");
      expect(palette?.background.paper).toBe("#161C1B");
      expect(palette?.text.primary).toBe("#E6ECEA");
      expect(palette?.text.secondary).toBe("#A9B6B2");
      expect(palette?.primary.main).toBe("#34D3B6");
      expect(palette?.success.main).toBe("#5FC98A");
      expect(palette?.warning.main).toBe("#E0AC4A");
      expect(palette?.error.main).toBe("#F2837A");
      expect(palette?.info.main).toBe("#6FB2E3");
    });
  });

  describe("component identity overrides (TASK-150)", () => {
    it("MuiChip is pill-shaped", () => {
      const chipRoot = theme.components?.MuiChip?.styleOverrides?.root as { borderRadius: number };
      expect(chipRoot.borderRadius).toBe(999);
    });

    it.each(["success", "warning", "error", "info"] as const)(
      "MuiAlert standard variant resolves %s severity to the statusPill token",
      (severity) => {
        type AlertOwnerState = { variant: string; colorSeverity: string };
        type AlertRootFn = (props: {
          theme: typeof theme;
          ownerState: AlertOwnerState;
        }) => Record<string, unknown>;
        const rootFn = theme.components?.MuiAlert?.styleOverrides?.root as AlertRootFn;
        const style = rootFn({ theme, ownerState: { variant: "standard", colorSeverity: severity } });
        const pill = theme.vars.palette.statusPill[severity];
        expect(style.backgroundColor).toBe(pill.bg);
        expect(style.color).toBe(pill.text);
      }
    );

    it("MuiOutlinedInput shows a visible accent focus ring", () => {
      type OutlinedInputRootFn = (props: { theme: typeof theme }) => {
        "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
          borderColor: string;
          borderWidth: number;
        };
      };
      const rootFn = theme.components?.MuiOutlinedInput?.styleOverrides?.root as OutlinedInputRootFn;
      const style = rootFn({ theme });
      const focusRule = style["&.Mui-focused .MuiOutlinedInput-notchedOutline"];
      expect(focusRule.borderColor).toBe(theme.vars.palette.primary.main);
      expect(focusRule.borderWidth).toBeGreaterThan(1);
    });
  });

  describe("no-flash inline script (frontend/index.html)", () => {
    const indexHtmlPath = resolve(__dirname, "../../../index.html");
    const indexHtml = readFileSync(indexHtmlPath, "utf-8");

    it("shares the mode storage key, attribute names, and page-background hex with theme.ts", () => {
      expect(indexHtml).toContain(COLOR_SCHEME_MODE_STORAGE_KEY);
      expect(indexHtml).toContain(COLOR_SCHEME_ATTRIBUTES.light);
      expect(indexHtml).toContain(COLOR_SCHEME_ATTRIBUTES.dark);
      expect(indexHtml).toContain(COLOR_SCHEME_PAGE_BACKGROUND.light);
      expect(indexHtml).toContain(COLOR_SCHEME_PAGE_BACKGROUND.dark);
    });
  });
});
