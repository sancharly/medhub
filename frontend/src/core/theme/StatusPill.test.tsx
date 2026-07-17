import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { StatusPill, type StatusPillSeverity } from "./StatusPill";
import { theme } from "./theme";

const SEVERITIES: StatusPillSeverity[] = ["success", "warning", "error", "info"];

function renderPill(severity: StatusPillSeverity, label: string) {
  return render(
    <MuiThemeProvider theme={theme}>
      <StatusPill severity={severity} label={label} />
    </MuiThemeProvider>
  );
}

describe("StatusPill", () => {
  it.each(SEVERITIES)("renders the label and a leading icon for %s severity", (severity) => {
    renderPill(severity, `${severity} status`);
    expect(screen.getByText(`${severity} status`)).toBeInTheDocument();
    // MUI Chip renders the `icon` prop inside an element with the MuiChip-icon class.
    const icon = document.querySelector(".MuiChip-icon");
    expect(icon).not.toBeNull();
  });

  it("uses a distinct icon per severity so state is not conveyed by color alone", () => {
    const rendered = SEVERITIES.map((severity) => {
      const { container, unmount } = renderPill(severity, severity);
      const iconShape = container.querySelector(".MuiChip-icon path")?.getAttribute("d");
      unmount();
      return iconShape;
    });
    expect(rendered.every((shape) => shape)).toBe(true);
    expect(new Set(rendered).size).toBe(SEVERITIES.length);
  });
});
