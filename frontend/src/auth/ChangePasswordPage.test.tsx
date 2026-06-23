import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../tests/setup";
import { ChangePasswordPage } from "./ChangePasswordPage";
import { theme } from "../core/theme/theme";

const BASE = "http://localhost/api/v1";

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/password"]}>
          <Routes>
            <Route path="/password" element={<ChangePasswordPage />} />
            <Route path="/profile" element={<div>Profile</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ChangePasswordPage", () => {
  it("live hints update when typing in new password field", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({ id: "1", email: "a@b.com", userType: "patient", mustChangePassword: true })
      )
    );

    renderPage();

    const newPwd = await screen.findByLabelText(/^New password/i);
    await userEvent.type(newPwd, "Abc123!@#xyzabcd");

    await waitFor(() => {
      expect(screen.getByText(/at least 12 characters/i)).toBeInTheDocument();
    });
  });

  it("server 400 for reused password shows history message", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({ id: "1", email: "a@b.com", userType: "patient", mustChangePassword: true })
      ),
      http.put(`${BASE}/users/me/password`, () =>
        HttpResponse.json(
          {
            type: "/errors/validation-error",
            title: "Validation failed",
            status: 400,
            errors: [{ field: "newPassword", message: "Password was used recently" }],
          },
          { status: 400, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();
    await userEvent.type(screen.getByLabelText(/current password/i), "OldPass1!");
    await userEvent.type(screen.getByLabelText(/^New password/i), "Abc123!@#xyz12");
    await userEvent.type(screen.getByLabelText(/confirm new password/i), "Abc123!@#xyz12");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));

    await waitFor(() =>
      expect(screen.getByTestId("server-error")).toBeInTheDocument()
    );
    expect(screen.getByTestId("server-error").textContent).toMatch(/recently/i);
  });

  it("new/confirm mismatch shows non-disclosing message and no submit", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({ id: "1", email: "a@b.com", userType: "patient", mustChangePassword: true })
      )
    );

    renderPage();
    await userEvent.type(screen.getByLabelText(/^New password/i), "Abc123!@#xyz12");
    await userEvent.type(screen.getByLabelText(/confirm new password/i), "Different1!@#xyz");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));

    expect(screen.getByTestId("mismatch-error")).toBeInTheDocument();
    expect(screen.getByTestId("mismatch-error").textContent).not.toMatch(/(weak|too short|policy)/i);
  });

  it("successful change navigates to profile", async () => {
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json({ id: "1", email: "a@b.com", userType: "patient", mustChangePassword: false })
      ),
      http.put(`${BASE}/users/me/password`, () => new HttpResponse(null, { status: 204 }))
    );

    renderPage();
    await userEvent.type(screen.getByLabelText(/current password/i), "OldPass1!");
    await userEvent.type(screen.getByLabelText(/^New password/i), "Abc123!@#xyz12");
    await userEvent.type(screen.getByLabelText(/confirm new password/i), "Abc123!@#xyz12");
    await userEvent.click(screen.getByRole("button", { name: /change password/i }));

    await waitFor(() =>
      expect(screen.getByText("Profile")).toBeInTheDocument()
    );
  });
});
