import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { AppNavigation } from "./AppNavigation";
import { navConfig } from "./navConfig";
import { theme } from "../theme/theme";

function renderNav(userType: "patient" | "sysadmin" | "doctor" | "admin") {
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
    renderNav("patient");
    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Appointments")).toBeInTheDocument();
    expect(screen.getByText("Consent")).toBeInTheDocument();
  });

  it("patient does not see admin entries", () => {
    renderNav("patient");
    expect(screen.queryByText("Accounts")).not.toBeInTheDocument();
    expect(screen.queryByText("Groups")).not.toBeInTheDocument();
  });

  it("sysadmin sees admin entries", () => {
    renderNav("sysadmin");
    expect(screen.getByText("Accounts")).toBeInTheDocument();
    expect(screen.getByText("Groups")).toBeInTheDocument();
  });

  it("labels come from navConfig", () => {
    renderNav("doctor");
    const doctorLabels = navConfig
      .filter((e) => e.roles.includes("doctor"))
      .map((e) => e.label);
    doctorLabels.forEach((label) => {
      expect(screen.getByText(label)).toBeInTheDocument();
    });
  });
});
