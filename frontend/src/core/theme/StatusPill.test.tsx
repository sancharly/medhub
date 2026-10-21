import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { StatusPill, type StatusPillSeverity } from "./StatusPill";
import { theme } from "./theme";

const SEVERITIES: StatusPillSeverity[] = ["success", "warning", "error", "info"];
const SCHEMES = ["light", "dark"] as const;

function renderPill(scheme: (typeof SCHEMES)[number], severity: StatusPillSeverity, label: string) {
  return render(
    <MuiThemeProvider theme={theme} defaultMode={scheme}>
      <StatusPill severity={severity} label={label} />
    </MuiThemeProvider>
  );
}

// SR-038 AC-4: status is never conveyed by color alone. Exercised under both
// `defaultMode` schemes — jsdom doesn't resolve CSS variables to pixel
// colors, so these assert on the structural markers (icon + label presence,
// distinct icon shapes) that hold regardless of scheme, per each scheme's
// resolved `data-{scheme}` attribute on <html>.
describe.each(SCHEMES)("StatusPill in %s scheme", (scheme) => {
  it.each(SEVERITIES)("renders the label and a leading icon for %s severity", async (severity) => {
    renderPill(scheme, severity, `${severity} status`);
    expect(await screen.findByText(`${severity} status`)).toBeInTheDocument();
    expect(document.documentElement).toHaveAttribute(`data-${scheme}`);
    // MUI Chip renders the `icon` prop inside an element with the MuiChip-icon class.
    const icon = document.querySelector(".MuiChip-icon");
    expect(icon).not.toBeNull();
  });

  it("uses a distinct icon per severity so state is not conveyed by color alone", async () => {
    const rendered: Array<string | undefined> = [];
    for (const severity of SEVERITIES) {
      const { container, unmount } = renderPill(scheme, severity, severity);
      await screen.findByText(severity);
      const iconShape = container.querySelector(".MuiChip-icon path")?.getAttribute("d") ?? undefined;
      unmount();
      rendered.push(iconShape);
    }
    expect(rendered.every((shape) => shape)).toBe(true);
    expect(new Set(rendered).size).toBe(SEVERITIES.length);
  });
});
