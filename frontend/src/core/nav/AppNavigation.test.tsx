import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppNavigation } from "./AppNavigation";
import { navConfig } from "./navConfig";
import { theme } from "../theme/theme";

function renderNav(userType: "PATIENT" | "SYSADMIN" | "DOCTOR" | "ADMIN") {
  return render(
    <MuiThemeProvider theme={theme}>
      <MemoryRouter>
        <AppNavigation userType={userType} />
      </MemoryRouter>
    </MuiThemeProvider>
  );
}

describe("AppNavigation role filtering", () => {
  it("patient sees patient entries", () => {
    renderNav("PATIENT");
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Appointments")).toBeInTheDocument();
    expect(screen.getByText("Consent")).toBeInTheDocument();
  });

  it("patient does not see admin entries", () => {
    renderNav("PATIENT");
    expect(screen.queryByText("Accounts")).not.toBeInTheDocument();
    expect(screen.queryByText("Groups")).not.toBeInTheDocument();
  });

  it("sysadmin sees admin entries", () => {
    renderNav("SYSADMIN");
    expect(screen.getByText("Accounts")).toBeInTheDocument();
    expect(screen.getByText("Groups")).toBeInTheDocument();
  });

  it("labels come from navConfig", () => {
    renderNav("DOCTOR");
    const doctorLabels = navConfig
      .filter((e) => e.roles.includes("DOCTOR"))
      .map((e) => e.label);
    doctorLabels.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });
});
