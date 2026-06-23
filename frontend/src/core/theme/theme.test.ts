import { describe, it, expect } from "vitest";
import { theme } from "./theme";

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
    expect(theme.spacing(1)).toBe("8px");
  });
});
