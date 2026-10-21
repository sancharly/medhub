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
      expect(palette?.background.default).toBe("#F4F6FB");
      expect(palette?.background.paper).toBe("#FFFFFF");
      expect(palette?.text.primary).toBe("#171F2B");
      expect(palette?.text.secondary).toBe("#525C6C");
      expect(palette?.primary.main).toBe("#2563EB");
      expect(palette?.success.main).toBe("#1F7A47");
      expect(palette?.warning.main).toBe("#9A6402");
      expect(palette?.error.main).toBe("#C03D33");
      expect(palette?.info.main).toBe("#266DA1");
    });

    it("dark scheme matches ADD-001 §2.2 hex values", () => {
      const palette = theme.colorSchemes.dark?.palette;
      expect(palette?.background.default).toBe("#0E131B");
      expect(palette?.background.paper).toBe("#161B24");
      expect(palette?.text.primary).toBe("#E6EAF2");
      expect(palette?.text.secondary).toBe("#A9B2C1");
      expect(palette?.primary.main).toBe("#5AA2FF");
      expect(palette?.success.main).toBe("#5FC98A");
      expect(palette?.warning.main).toBe("#E0AC4A");
      expect(palette?.error.main).toBe("#F2837A");
      expect(palette?.info.main).toBe("#6FB2E3");
    });
  });

  describe("token structure parity (SR-038 AC-1, TASK-153)", () => {
    // Both schemes must define every token *required* by the shared structure
    // (Palette/TypeBackground interfaces in theme.ts). Scheme-only extras like
    // light's `primary.onSelected` or dark's `primary.light` are intentional
    // (ADD-001 §2) and are not part of this parity check.
    const REQUIRED_KEY_PATHS = [
      "background.default",
      "background.paper",
      "background.subtle",
      "background.selected",
      "background.elevated",
      "text.primary",
      "text.secondary",
      "text.disabled",
      "border.subtle",
      "border.input",
      "primary.main",
      "secondary.main",
      "success.main",
      "warning.main",
      "error.main",
      "info.main",
      "statusPill.success.bg",
      "statusPill.success.text",
      "statusPill.warning.bg",
      "statusPill.warning.text",
      "statusPill.error.bg",
      "statusPill.error.text",
      "statusPill.info.bg",
      "statusPill.info.text",
    ];

    function missingPaths(palette: unknown): string[] {
      return REQUIRED_KEY_PATHS.filter((path) => {
        const value = path
          .split(".")
          .reduce<unknown>(
            (obj, key) => (obj && typeof obj === "object" ? (obj as Record<string, unknown>)[key] : undefined),
            palette
          );
        return value === undefined || value === null || value === "";
      });
    }

    it("light scheme defines every required token key path", () => {
      expect(missingPaths(theme.colorSchemes.light?.palette)).toEqual([]);
    });

    it("dark scheme defines every required token key path", () => {
      expect(missingPaths(theme.colorSchemes.dark?.palette)).toEqual([]);
    });
  });

  describe("WCAG 2.1 AA contrast (SR-038 AC-3, ADD-001 §6, TASK-153)", () => {
    // Relative-luminance / contrast-ratio formulas per WCAG 2.1 §1.4.3,
    // implemented here (not imported) so this test independently catches any
    // token change that breaks contrast. Token *values* still come from
    // theme.ts — the single source of truth — never duplicated as literals.
    function hexToRgb(hex: string): [number, number, number] {
      const clean = hex.replace("#", "");
      const value = parseInt(clean, 16);
      return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
    }

    function relativeLuminance(hex: string): number {
      const [r, g, b] = hexToRgb(hex).map((channel) => {
        const s = channel / 255;
        return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * r + 0.7152 * g + 0.0722 * b;
    }

    function contrastRatio(hexA: string, hexB: string): number {
      const lA = relativeLuminance(hexA);
      const lB = relativeLuminance(hexB);
      const lighter = Math.max(lA, lB);
      const darker = Math.min(lA, lB);
      return (lighter + 0.05) / (darker + 0.05);
    }

    type Palette = NonNullable<typeof theme.colorSchemes.light>["palette"];

    // Essential pairs from ADD-001 §6. `fg`/`bg` read live token values off
    // the theme so a future palette edit is re-checked automatically.
    const PAIRS: Array<{
      name: string;
      threshold: number;
      fg: (p: Palette, scheme: "light" | "dark") => string;
      bg: (p: Palette, scheme: "light" | "dark") => string;
    }> = [
      { name: "text.primary / card", threshold: 4.5, fg: (p) => p.text.primary, bg: (p) => p.background.paper },
      { name: "text.secondary / card", threshold: 4.5, fg: (p) => p.text.secondary, bg: (p) => p.background.paper },
      {
        name: "text.secondary / page-or-elevated",
        threshold: 4.5,
        fg: (p) => p.text.secondary,
        bg: (p, scheme) => (scheme === "light" ? p.background.default : p.background.elevated),
      },
      { name: "primary as text / card", threshold: 4.5, fg: (p) => p.primary.main, bg: (p) => p.background.paper },
      {
        name: "contrastText / primary button",
        threshold: 4.5,
        fg: (p) => p.primary.contrastText,
        bg: (p) => p.primary.main,
      },
      { name: "input outline / card", threshold: 3, fg: (p) => p.border.input, bg: (p) => p.background.paper },
      {
        name: "selected text / selected bg",
        threshold: 4.5,
        fg: (p, scheme) => (scheme === "light" ? p.primary.onSelected! : p.primary.light!),
        bg: (p) => p.background.selected,
      },
      {
        name: "success pill text / pill bg",
        threshold: 4.5,
        fg: (p) => p.statusPill.success.text,
        bg: (p) => p.statusPill.success.bg,
      },
      {
        name: "warning pill text / pill bg",
        threshold: 4.5,
        fg: (p) => p.statusPill.warning.text,
        bg: (p) => p.statusPill.warning.bg,
      },
      {
        name: "error pill text / pill bg",
        threshold: 4.5,
        fg: (p) => p.statusPill.error.text,
        bg: (p) => p.statusPill.error.bg,
      },
      {
        name: "info pill text / pill bg",
        threshold: 4.5,
        fg: (p) => p.statusPill.info.text,
        bg: (p) => p.statusPill.info.bg,
      },
      { name: "error text / card", threshold: 4.5, fg: (p) => p.error.main, bg: (p) => p.background.paper },
      { name: "secondary as text / card", threshold: 4.5, fg: (p) => p.secondary.main, bg: (p) => p.background.paper },
      { name: "focus ring / page", threshold: 3, fg: (p) => p.primary.main, bg: (p) => p.background.default },
    ];

    it.each(["light", "dark"] as const)("%s scheme: every essential pair meets its WCAG 2.1 AA threshold", (scheme) => {
      const palette = theme.colorSchemes[scheme]?.palette as Palette;
      for (const pair of PAIRS) {
        const ratio = contrastRatio(pair.fg(palette, scheme), pair.bg(palette, scheme));
        expect(ratio, `${scheme} "${pair.name}" ratio ${ratio.toFixed(2)} < ${pair.threshold}`).toBeGreaterThanOrEqual(
          pair.threshold
        );
      }
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

    it("reads the persisted mode via localStorage.getItem with the exact exported storage key", () => {
      const getItemCall = new RegExp(
        `localStorage\\.getItem\\(["']${COLOR_SCHEME_MODE_STORAGE_KEY}["']\\)`
      );
      expect(indexHtml).toMatch(getItemCall);
    });
  });
});
