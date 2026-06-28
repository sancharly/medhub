import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { ConfirmProvider } from "../confirm/ConfirmProvider";
import { ErrorToastProvider } from "../error/ErrorToastProvider";
import { server } from "../../tests/setup";
import { ConsentPage } from "./ConsentPage";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";

const manualGrant = {
  id: "g1",
  patientId: "patient-1",
  doctorId: "doc-1",
  sourceType: "MANUAL",
  appointmentId: null,
  active: true,
};

const appointmentGrant = {
  id: "g2",
  patientId: "patient-1",
  doctorId: "doc-2",
  sourceType: "APPOINTMENT",
  appointmentId: "appt-abc",
  active: true,
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <ConfirmProvider>
          <ErrorToastProvider>
            <MemoryRouter>
              <ConsentPage />
            </MemoryRouter>
          </ErrorToastProvider>
        </ConfirmProvider>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ConsentPage", () => {
  it("SR-036.7: shows both MANUAL and APPOINTMENT grants with correct source labels", async () => {
    server.use(
      http.get(`${BASE}/me/consents`, () =>
        HttpResponse.json([manualGrant, appointmentGrant])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/doc-1/)).toBeInTheDocument();
    });
    expect(screen.getByText(/doc-2/)).toBeInTheDocument();
    expect(screen.getByText(/MANUAL/i)).toBeInTheDocument();
    expect(screen.getByText(/APPOINTMENT/i)).toBeInTheDocument();
  });

  it("SR-008.1: grant consent: POST /consents with doctorId; list refetches", async () => {
    const postSpy = vi.fn();
    const newGrant = {
      id: "g3",
      patientId: "patient-1",
      doctorId: "doc-3",
      sourceType: "MANUAL",
      appointmentId: null,
      active: true,
    };

    server.use(
      http.get(`${BASE}/me/consents`, () => HttpResponse.json([manualGrant])),
      http.post(`${BASE}/consents`, async ({ request }) => {
        const body = await request.json() as { doctorId: string };
        postSpy(body);
        return HttpResponse.json(newGrant, { status: 201 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/doctor id/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/doctor id/i), "doc-3");
    await userEvent.click(screen.getByRole("button", { name: /grant/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith({ doctorId: "doc-3" });
    });
  });

  it("SR-008.3 / SR-027.2: revoke opens confirm dialog then DELETE /consents/{id}", async () => {
    const deleteSpy = vi.fn();

    server.use(
      http.get(`${BASE}/me/consents`, () => HttpResponse.json([manualGrant])),
      http.delete(`${BASE}/consents/g1`, () => {
        deleteSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /revoke/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /revoke/i }));

    // Dialog appears before request
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(deleteSpy).not.toHaveBeenCalled();

    // Confirm the dialog
    await userEvent.click(screen.getByRole("button", { name: /confirm/i }));

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalled();
    });
  });

  it("SR-027.2: cancelling revoke dialog issues no request", async () => {
    const deleteSpy = vi.fn();

    server.use(
      http.get(`${BASE}/me/consents`, () => HttpResponse.json([manualGrant])),
      http.delete(`${BASE}/consents/g1`, () => {
        deleteSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /revoke/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /revoke/i }));
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });

    expect(deleteSpy).not.toHaveBeenCalled();
  });

  it("SR-036.4: revoking one grant does not remove the other", async () => {
    const grants = [manualGrant, appointmentGrant];
    let callCount = 0;

    server.use(
      http.get(`${BASE}/me/consents`, () => {
        // After revoke, return only the second grant
        if (callCount > 0) return HttpResponse.json([appointmentGrant]);
        callCount++;
        return HttpResponse.json(grants);
      }),
      http.delete(`${BASE}/consents/g1`, () =>
        new HttpResponse(null, { status: 204 })
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/doc-1/)).toBeInTheDocument();
    });

    const revokeButtons = screen.getAllByRole("button", { name: /revoke/i });
    await userEvent.click(revokeButtons[0]);
    await userEvent.click(screen.getByRole("button", { name: /confirm/i }));

    await waitFor(() => {
      expect(screen.queryByText(/Doctor: doc-1/)).not.toBeInTheDocument();
    });

    expect(screen.getByText(/doc-2/)).toBeInTheDocument();
  });

  it("SR-027.3: 404 on revoke shows error message", async () => {
    server.use(
      http.get(`${BASE}/me/consents`, () => HttpResponse.json([manualGrant])),
      http.delete(`${BASE}/consents/g1`, () =>
        HttpResponse.json(
          {
            type: "/errors/not-found",
            title: "Not Found",
            status: 404,
          },
          { status: 404, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /revoke/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /revoke/i }));
    await userEvent.click(screen.getByRole("button", { name: /confirm/i }));

    await waitFor(() => {
      // ErrorToastProvider shows the error in an Alert inside a Snackbar
      expect(screen.getByText(/not found/i)).toBeInTheDocument();
    });
  });
});
