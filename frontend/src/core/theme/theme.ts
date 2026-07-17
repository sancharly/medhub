import { createTheme } from "@mui/material/styles";
import type { Shadows } from "@mui/material/styles";

// MedHub design tokens ("Clinical Calm") — single source of truth.
// See docs/design-outputs/architecture/ADD-001-medhub-design-system-and-theming.md
// and docs/design/adr/0014-mui-css-variables-theming.md.

declare module "@mui/material/styles" {
  // Enables CSS-variables typing (theme.colorSchemes, theme.vars, …) per MUI's
  // TypeScript guide for cssVariables-based theming.
  interface CssThemeVariables {
    enabled: true;
  }
  interface TypeBackground {
    /** Hover rows, table headers, wells. */
    subtle: string;
    /** Selected nav item / selected row tint. */
    selected: string;
    /** Highest surface: menus, dialogs, popovers (dark-mode elevation step). */
    elevated: string;
  }
  interface Palette {
    border: {
      /** Decorative card outlines/dividers (mirrors `divider`). */
      subtle: string;
      /** Input outlines and interactive boundaries (3:1 contrast). */
      input: string;
    };
    /** Tinted status-pill background/text pairs, contrast-verified per ADD-001 §6. */
    statusPill: {
      success: { bg: string; text: string };
      warning: { bg: string; text: string };
      error: { bg: string; text: string };
      info: { bg: string; text: string };
    };
  }
  interface PaletteOptions {
    border?: Palette["border"];
    statusPill?: Palette["statusPill"];
  }
  interface PaletteColor {
    /** Text/icon color on `background.selected` (light-mode primary only). */
    onSelected?: string;
  }
  interface SimplePaletteColorOptions {
    onSelected?: string;
  }
}

// Mode string used by MUI's native localStorage persistence — this is the ONLY
// key the app writes to localStorage for theming (SR-039 AC-6). Shared with the
// no-flash inline script in frontend/index.html; theme.test.ts asserts both stay
// in sync.
export const COLOR_SCHEME_MODE_STORAGE_KEY = "mui-mode";

// Matches the `cssVariables.colorSchemeSelector` value below: MUI renders this as
// boolean attributes `data-light` / `data-dark` on <html>. Shared with index.html.
export const COLOR_SCHEME_SELECTOR = "data";
export const COLOR_SCHEME_ATTRIBUTES = {
  light: "data-light",
  dark: "data-dark",
} as const;

const lightTokens = {
  bgPage: "#F4F7F6",
  bgCard: "#FFFFFF",
  bgSubtle: "#ECF2F0",
  bgSelected: "#DFF1EC",
  borderSubtle: "#E3EAE8",
  borderInput: "#75847F",
  textPrimary: "#16211F",
  textSecondary: "#52605D",
  textDisabled: "#8A9793",
  primaryMain: "#0E7C6B",
  primaryDark: "#0A6154",
  primaryOnSelected: "#0A5D50",
  secondaryMain: "#3E5C76",
  success: { main: "#1F7A47", pillBg: "#E1F3E7", pillText: "#176A3E" },
  warning: { main: "#9A6402", pillBg: "#FBEFD9", pillText: "#7A5308" },
  error: { main: "#C03D33", pillBg: "#FAE7E4", pillText: "#9E2F27" },
  info: { main: "#266DA1", pillBg: "#E3EFF7", pillText: "#1D577F" },
} as const;

const darkTokens = {
  bgPage: "#0E1413",
  bgCard: "#161C1B",
  bgElevated: "#1C2422",
  bgSelected: "#123129",
  borderSubtle: "#26302E",
  borderInput: "#5C6B67",
  textPrimary: "#E6ECEA",
  textSecondary: "#A9B6B2",
  textDisabled: "#6E7B77",
  primaryMain: "#34D3B6",
  primaryContrastText: "#062E27",
  primaryLight: "#7FE0CC",
  secondaryMain: "#9DB4D0",
  secondaryContrastText: "#12233A",
  success: { main: "#5FC98A", pillBg: "#14291C", pillText: "#86D9A5" },
  warning: { main: "#E0AC4A", pillBg: "#2E2312", pillText: "#EBC170" },
  error: {
    main: "#F2837A",
    contrastText: "#380D0A",
    pillBg: "#331715",
    pillText: "#F49B93",
  },
  info: { main: "#6FB2E3", pillBg: "#132535", pillText: "#8FC1EA" },
} as const;

// Page background per scheme — used by the no-flash inline script in index.html.
export const COLOR_SCHEME_PAGE_BACKGROUND = {
  light: lightTokens.bgPage,
  dark: darkTokens.bgPage,
} as const;

const manropeFontFamily = '"Manrope Variable", "Manrope", "Helvetica", "Arial", sans-serif';
const interFontFamily = '"Inter Variable", "Inter", "Roboto", "Helvetica", "Arial", sans-serif';

// Elevation (light-mode formulas, ADD-001 §4). MUI's `shadows` array is a single
// theme-wide token, not scheme-scoped, so dark mode ("near-none": surface lightness
// step + 1px border.subtle instead of shadow) is expressed in TASK-150's Paper/Card/
// Dialog styleOverrides via `theme.applyStyles("dark", { boxShadow: "none" })`, not
// by swapping this array.
const shadowLevel1 = "0 1px 2px rgba(15,23,22,.05)";
const shadowLevel2 = "0 1px 2px rgba(15,23,22,.04), 0 4px 12px rgba(15,23,22,.06)";
const shadowLevel3 = "0 2px 4px rgba(15,23,22,.05), 0 10px 24px rgba(15,23,22,.09)";
const shadowLevel4 = "0 4px 8px rgba(15,23,22,.06), 0 20px 48px rgba(15,23,22,.14)";

const shadows = [
  "none",
  shadowLevel1,
  shadowLevel2,
  shadowLevel3,
  shadowLevel4,
  ...Array(20).fill(shadowLevel4),
] as unknown as Shadows;

export const theme = createTheme({
  cssVariables: {
    colorSchemeSelector: COLOR_SCHEME_SELECTOR,
  },
  colorSchemes: {
    light: {
      palette: {
        mode: "light",
        primary: {
          main: lightTokens.primaryMain,
          dark: lightTokens.primaryDark,
          contrastText: "#FFFFFF",
          onSelected: lightTokens.primaryOnSelected,
        },
        secondary: {
          main: lightTokens.secondaryMain,
          contrastText: "#FFFFFF",
        },
        success: { main: lightTokens.success.main },
        warning: { main: lightTokens.warning.main },
        error: { main: lightTokens.error.main, contrastText: "#FFFFFF" },
        info: { main: lightTokens.info.main },
        background: {
          default: lightTokens.bgPage,
          paper: lightTokens.bgCard,
          subtle: lightTokens.bgSubtle,
          selected: lightTokens.bgSelected,
          elevated: lightTokens.bgCard,
        },
        text: {
          primary: lightTokens.textPrimary,
          secondary: lightTokens.textSecondary,
          disabled: lightTokens.textDisabled,
        },
        divider: lightTokens.borderSubtle,
        border: {
          subtle: lightTokens.borderSubtle,
          input: lightTokens.borderInput,
        },
        statusPill: {
          success: { bg: lightTokens.success.pillBg, text: lightTokens.success.pillText },
          warning: { bg: lightTokens.warning.pillBg, text: lightTokens.warning.pillText },
          error: { bg: lightTokens.error.pillBg, text: lightTokens.error.pillText },
          info: { bg: lightTokens.info.pillBg, text: lightTokens.info.pillText },
        },
      },
    },
    dark: {
      palette: {
        mode: "dark",
        primary: {
          main: darkTokens.primaryMain,
          light: darkTokens.primaryLight,
          contrastText: darkTokens.primaryContrastText,
        },
        secondary: {
          main: darkTokens.secondaryMain,
          contrastText: darkTokens.secondaryContrastText,
        },
        success: { main: darkTokens.success.main },
        warning: { main: darkTokens.warning.main },
        error: { main: darkTokens.error.main, contrastText: darkTokens.error.contrastText },
        info: { main: darkTokens.info.main },
        background: {
          default: darkTokens.bgPage,
          paper: darkTokens.bgCard,
          subtle: darkTokens.bgElevated,
          selected: darkTokens.bgSelected,
          elevated: darkTokens.bgElevated,
        },
        text: {
          primary: darkTokens.textPrimary,
          secondary: darkTokens.textSecondary,
          disabled: darkTokens.textDisabled,
        },
        divider: darkTokens.borderSubtle,
        border: {
          subtle: darkTokens.borderSubtle,
          input: darkTokens.borderInput,
        },
        statusPill: {
          success: { bg: darkTokens.success.pillBg, text: darkTokens.success.pillText },
          warning: { bg: darkTokens.warning.pillBg, text: darkTokens.warning.pillText },
          error: { bg: darkTokens.error.pillBg, text: darkTokens.error.pillText },
          info: { bg: darkTokens.info.pillBg, text: darkTokens.info.pillText },
        },
      },
    },
  },
  typography: {
    fontFamily: interFontFamily,
    fontSize: 14,
    h1: { fontFamily: manropeFontFamily, fontWeight: 700, fontSize: "1.75rem", letterSpacing: "-0.01em" },
    h2: { fontFamily: manropeFontFamily, fontWeight: 700, fontSize: "1.5rem", letterSpacing: "-0.01em" },
    h3: { fontFamily: manropeFontFamily, fontWeight: 650, fontSize: "1.25rem", letterSpacing: "-0.01em" },
    h4: { fontFamily: manropeFontFamily, fontWeight: 600, fontSize: "1.0625rem", letterSpacing: "-0.01em" },
    subtitle1: { fontFamily: interFontFamily, fontWeight: 600, fontSize: "0.9375rem", lineHeight: 1.5 },
    body1: { fontFamily: interFontFamily, fontWeight: 400, fontSize: "0.875rem", lineHeight: 1.5 },
    body2: { fontFamily: interFontFamily, fontWeight: 400, fontSize: "0.8125rem", lineHeight: 1.5 },
    caption: { fontFamily: interFontFamily, fontWeight: 400, fontSize: "0.75rem", lineHeight: 1.5 },
    overline: {
      fontFamily: interFontFamily,
      fontWeight: 600,
      fontSize: "0.6875rem",
      letterSpacing: "0.06em",
      textTransform: "uppercase",
    },
  },
  shape: {
    borderRadius: 12,
  },
  shadows,
  spacing: 8,
  components: {
    MuiButtonBase: {
      styleOverrides: {
        root: {
          minHeight: 44,
          minWidth: 44,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minHeight: 44,
          minWidth: 44,
        },
      },
    },
  },
});
