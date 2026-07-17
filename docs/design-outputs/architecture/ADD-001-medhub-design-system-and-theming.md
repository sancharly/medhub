---
id: "ADD-001"
type: architecture-doc
title: "MedHub design system: visual identity, design tokens, and light/dark theming"
status: approved
version: "1.0"
author: "Carlos Santiago Liceras"
created: "2026-07-17"
updated: "2026-07-17"
links:
  - target: "SR-037"
    relation: implements
  - target: "SR-038"
    relation: implements
  - target: "SR-039"
    relation: implements
tags: ["phase:ui-enhancement"]
---

# MedHub Design System — Visual Identity, Tokens, and Theming

Design-output specification for the UI design-system refactor (SR-037, SR-038, SR-039).
The theming *mechanism* decision is recorded in [ADR-0014](../../design/adr/0014-mui-css-variables-theming.md);
this document is the single source of truth for the *values*.

## 1. Visual identity: "Clinical Calm"

MedHub's identity is built on a **teal-tinted neutral scale** — not gray. Every neutral
(page background, borders, text) carries a faint green-blue undertone that ties the whole
interface to the single strong accent, a deep **clinical teal**. The result reads as calm,
precise, and unmistakably medical without resorting to hospital-blue clichés or copying the
stakeholder reference material.

- **Character:** trustworthy, calm, precise. Soft neutral page, white elevated cards,
  generous radii, low soft shadows, generous whitespace. Clinical content stays in the
  foreground; the chrome recedes.
- **One strong accent:** deep teal `#0E7C6B` (light) / luminous teal `#34D3B6` (dark) for
  primary actions, selection, focus, and active navigation. Everything else is neutral or a
  semantic status color.
- **Quiet second voice:** slate blue `#3E5C76` (light) / `#9DB4D0` (dark) for icon badges
  and non-status informational accents only — never for actions.
- **Status language:** tinted pills (soft tinted background + dark tinted text + leading
  icon) for appointment/consent/account states; never color alone (SR-038 AC-4).
- **Dark mode:** the same system, re-valued. Near-black teal-tinted page, slightly lighter
  card surfaces, elevation expressed by surface lightness + hairline borders instead of
  shadows. First-class, not inverted.

## 2. Color tokens

Primitive values below; semantic mapping onto MUI in §5. All essential pairs are
contrast-verified in §6.

### 2.1 Light scheme

| Token | Value | Role |
|---|---|---|
| `bg.page` | `#F4F7F6` | App/page background (teal-tinted neutral) |
| `bg.card` | `#FFFFFF` | Cards, tables, dialogs, menus (`background.paper`) |
| `bg.subtle` | `#ECF2F0` | Hover rows, table headers, wells |
| `bg.selected` | `#DFF1EC` | Selected nav item / selected row tint |
| `border.subtle` | `#E3EAE8` | Card outlines, dividers (decorative) |
| `border.input` | `#75847F` | Input outlines, interactive boundaries (3:1 vs card) |
| `text.primary` | `#16211F` | Headings, body |
| `text.secondary` | `#52605D` | Captions, labels, secondary cells |
| `text.disabled` | `#8A9793` | Disabled text (exempt from AA) |
| `primary.main` | `#0E7C6B` | Accent: buttons, links, focus, active nav (white text) |
| `primary.dark` | `#0A6154` | Hover/pressed |
| `primary.onSelected` | `#0A5D50` | Text/icon on `bg.selected` |
| `secondary.main` | `#3E5C76` | Icon badges, avatars (white text) |
| `success.main` | `#1F7A47` | Icons/borders; pill: bg `#E1F3E7`, text `#176A3E` |
| `warning.main` | `#9A6402` | Icons/borders; pill: bg `#FBEFD9`, text `#7A5308` |
| `error.main` | `#C03D33` | Text/buttons (white text); pill: bg `#FAE7E4`, text `#9E2F27` |
| `info.main` | `#266DA1` | Icons/borders; pill: bg `#E3EFF7`, text `#1D577F` |

### 2.2 Dark scheme

| Token | Value | Role |
|---|---|---|
| `bg.page` | `#0E1413` | App/page background (near-black, teal-tinted) |
| `bg.card` | `#161C1B` | Cards, tables (`background.paper`) |
| `bg.elevated` | `#1C2422` | Menus, dialogs, popovers (highest surface) |
| `bg.selected` | `#123129` | Selected nav item / selected row tint |
| `border.subtle` | `#26302E` | Card outlines, dividers |
| `border.input` | `#5C6B67` | Input outlines, interactive boundaries (3:1 vs card) |
| `text.primary` | `#E6ECEA` | Headings, body |
| `text.secondary` | `#A9B6B2` | Captions, labels |
| `text.disabled` | `#6E7B77` | Disabled text |
| `primary.main` | `#34D3B6` | Accent (contrast text `#062E27`) |
| `primary.light` | `#7FE0CC` | Text/icon on `bg.selected`; hover text |
| `secondary.main` | `#9DB4D0` | Icon badges (contrast text `#12233A`) |
| `success.main` | `#5FC98A` | Icons/borders; pill: bg `#14291C`, text `#86D9A5` |
| `warning.main` | `#E0AC4A` | Icons/borders; pill: bg `#2E2312`, text `#EBC170` |
| `error.main` | `#F2837A` | Text/buttons (contrast text `#380D0A`); pill: bg `#331715`, text `#F49B93` |
| `info.main` | `#6FB2E3` | Icons/borders; pill: bg `#132535`, text `#8FC1EA` |

## 3. Typography

Two self-hosted variable families via Fontsource (bundled by Vite, **no CDN** — the app must
work in closed clinical networks). Note: the current theme names `"Inter"` but never loads
it; today the app silently falls back to Helvetica/Arial.

- **Display/headings: Manrope** (`@fontsource-variable/manrope`) — weights 600–700, slight
  negative letter-spacing (-0.01em) on h1–h4. Geometric-humanist, gives MedHub its face.
- **Body/UI/data: Inter** (`@fontsource-variable/inter`) — weights 400/500/600. In data
  tables and numeric cells enable tabular figures (`font-feature-settings: "tnum"`).
- **Scale (base 14 as today):** h1 28/700, h2 24/700, h3 20/650, h4 17/600 (Manrope);
  subtitle1 15/600, body1 14/400, body2 13/400, caption 12/400, overline 11/600 +0.06em
  uppercase (Inter). Line-height ≥1.5 for body text.

## 4. Shape, elevation, spacing

- **Radius:** `sm` 8px (inputs, small controls), `md` 12px (**MUI `shape.borderRadius`**:
  buttons, menus, alerts), `lg` 16px (cards, dialogs), `pill` 999px (status pills, chips).
- **Shadows (light):** soft, low-opacity, teal-black ambient — level 1
  `0 1px 2px rgba(15,23,22,.05)`; level 2 (card) `0 1px 2px rgba(15,23,22,.04), 0 4px 12px rgba(15,23,22,.06)`;
  level 3 (popover) `0 2px 4px rgba(15,23,22,.05), 0 10px 24px rgba(15,23,22,.09)`;
  level 4 (dialog) `0 4px 8px rgba(15,23,22,.06), 0 20px 48px rgba(15,23,22,.14)`.
  Map MUI `shadows[1..4]` to these; higher indices reuse level 4.
- **Shadows (dark):** near-none. Elevation = surface lightness step (`bg.card` →
  `bg.elevated`) + 1px `border.subtle` outline. Cards in both modes carry the 1px subtle
  border so structure never depends on shadow alone.
- **Spacing:** unchanged 8px unit. Page gutters 24px desktop / 16px phone; card padding
  24px; section gaps 32px. Minimum touch target ≥44×44px is **retained** (TASK-081).

## 5. Token layers → MUI mapping

```
Primitive (hex/px values, §2–§4)
   ↓ expressed as
Semantic MUI theme slots, per color scheme
   (colorSchemes.{light,dark}.palette.{background,text,divider,primary,…},
    typography, shape, shadows, spacing)
   ↓ emitted as
CSS variables (cssVariables: true → var(--mui-palette-…)), consumed by
   component styleOverrides in the theme + `sx`/`styled` in screens
```

- One `createTheme({ cssVariables: {...}, colorSchemes: { light, dark } })` call in
  `frontend/src/core/theme/theme.ts` is the single token definition (SR-037 AC-1).
- Global component restyling lives in `theme.components` styleOverrides (Button, Card,
  Paper, AppBar, Drawer, Table, Chip, TextField, Dialog, Alert, Tabs …) so screens need no
  per-screen styling; status pills are a shared component/Chip variant fed by the pill
  tokens (SR-037 AC-2/AC-3).
- Screens must not hard-code colors/radii/shadows/fonts; anything screen-specific uses
  `theme.palette.*` / `theme.vars.*` references only.

## 6. Contrast verification (WCAG 2.1 AA — SR-038 AC-3)

Ratios computed with the WCAG 2.1 relative-luminance formula (script re-runnable; an
automated version becomes a unit test in TASK-153). Requirement: ≥4.5:1 normal text,
≥3:1 large text/icons/interactive boundaries. **43/43 pairs pass.** Essential pairs:

| Pair (light) | Ratio | | Pair (dark) | Ratio |
|---|---|---|---|---|
| text.primary / card | 16.52 | | text.primary / card | 14.43 |
| text.secondary / card | 6.58 | | text.secondary / card | 8.24 |
| text.secondary / page | 6.11 | | text.secondary / elevated | 7.56 |
| primary as text / card | 5.10 | | primary as text / card | 9.16 |
| white / primary button | 5.10 | | on-primary / primary button | 7.80 |
| input outline / card (3:1) | 3.92 | | input outline / card (3:1) | 3.09 |
| selected text / selected bg | 6.65 | | selected text / selected bg | 8.98 |
| success pill text / pill bg | 5.74 | | success pill text / pill bg | 9.15 |
| warning pill text / pill bg | 6.01 | | warning pill text / pill bg | 9.08 |
| error pill text / pill bg | 6.10 | | error pill text / pill bg | 7.81 |
| info pill text / pill bg | 6.60 | | info pill text / pill bg | 8.17 |
| error text / card | 5.31 | | error text / card | 6.83 |
| secondary as text / card | 7.01 | | secondary / card | 8.12 |
| focus ring / page (3:1) | 4.74 | | focus ring / page (3:1) | 9.87 |

`text.disabled` and decorative `border.subtle` are intentionally below 4.5:1 (WCAG-exempt:
disabled/decorative). Any future token change must re-run the contrast test before merge.

## 7. Mode toggle, default, persistence (SR-039)

- Toggle: labeled `IconButton` in the persistent app chrome header, wired to MUI
  `useColorScheme()`; keyboard-operable, `aria-label` reflecting the action.
- Default: `defaultMode: "system"` — follows OS preference until an explicit choice exists.
- Persistence: MUI's native localStorage persistence of the color-scheme mode
  (client-side only, no PHI, no backend change).
- No flash: inline pre-hydration script in `frontend/index.html` reads the stored mode /
  `prefers-color-scheme`, sets the color-scheme attribute on `<html>` and a matching
  `background-color`, before the bundle loads. Mode switch is instant, no reload, no state
  loss (attribute + CSS variables only, no React remount).

## 8. Known limitations

- Preference is per browser/device (accepted in SR-039); no cross-device roaming.
- Full WCAG audit of non-token content (images, third-party DICOM viewer canvas) is out of
  scope here; the DICOM viewer module keeps its own rendering surface.
- Implementation risks and mitigations are carried in TASK-149…TASK-153.
