import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { ConfirmProvider } from "../confirm/ConfirmProvider";
import { server } from "../../tests/setup";
import { AppointmentsPage } from "./AppointmentsPage";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";

const patientMe = {
  id: "user-1",
  email: "p@test.com",
  userType: "PATIENT",
  state: "ACTIVE",
};

const doctorMe = {
  id: "doc-1",
  email: "doc@test.com",
  userType: "DOCTOR",
  state: "ACTIVE",
};

const pendingAppointment = {
  id: "appt-1",
  doctorId: "doc-1",
  patientId: "user-1",
  scheduledAt: "2025-03-15T10:00:00Z",
  state: "PENDING",
  createdAt: "2025-03-01T00:00:00Z",
};

const confirmedAppointment = {
  id: "appt-2",
  doctorId: "doc-1",
  patientId: "user-1",
  scheduledAt: "2025-04-01T14:00:00Z",
  state: "CONFIRMED",
  createdAt: "2025-03-01T00:00:00Z",
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <ConfirmProvider>
          <MemoryRouter>
            <AppointmentsPage />
          </MemoryRouter>
        </ConfirmProvider>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("AppointmentsPage", () => {
  it("SR-035.4/5: patient sees Pending appointment with Confirm and Decline buttons", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () =>
        HttpResponse.json([pendingAppointment])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/doc-1/)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /decline/i })).toBeInTheDocument();
  });

  it("SR-035.5: patient confirming calls POST /appointments/{id}/confirm", async () => {
    const confirmSpy = vi.fn();

    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () =>
        HttpResponse.json([pendingAppointment])
      ),
      http.post(`${BASE}/appointments/appt-1/confirm`, () => {
        confirmSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /confirm/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /confirm/i }));

    await waitFor(() => {
      expect(confirmSpy).toHaveBeenCalled();
    });
  });

  it("SR-035.7: patient can decline a CONFIRMED appointment", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () =>
        HttpResponse.json([confirmedAppointment])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/doc-1/)).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: /decline/i })).toBeInTheDocument();
  });

  it("SR-035.9: doctor sees state chip but no confirm/decline controls", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(doctorMe)),
      http.get(`${BASE}/appointments`, () =>
        HttpResponse.json([pendingAppointment])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/PENDING/i)).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /confirm/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /decline/i })).not.toBeInTheDocument();
  });

  it("SR-010.2: create form: missing fields shows error / blocked (doctor role)", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(doctorMe)),
      http.get(`${BASE}/appointments`, () => HttpResponse.json([]))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /schedule/i })).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole("button", { name: /schedule/i });
    expect(submitBtn).toBeDisabled();
  });

  it("SR-035.9: patient does not see create appointment form", async () => {
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () => HttpResponse.json([]))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Appointments/)).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /schedule/i })).not.toBeInTheDocument();
  });

  it("SR-011: renders exactly the server-returned appointments, no widening", async () => {
    const appts = [pendingAppointment, confirmedAppointment];
    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () => HttpResponse.json(appts))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText(/doc-1/).length).toBeGreaterThan(0);
    });

    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(appts.length);
  });

  it("SR-027.2: decline requires confirmation dialog", async () => {
    const declineSpy = vi.fn();

    server.use(
      http.get(`${BASE}/me`, () => HttpResponse.json(patientMe)),
      http.get(`${BASE}/appointments`, () =>
        HttpResponse.json([pendingAppointment])
      ),
      http.post(`${BASE}/appointments/appt-1/decline`, () => {
        declineSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /decline/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /decline/i }));

    // Dialog should appear before any request
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(declineSpy).not.toHaveBeenCalled();
  });
});
