import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../../tests/setup";
import { ClinicalEntriesPage } from "./ClinicalEntriesPage";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";
const PATIENT_ID = "pat-1";

const olderEntry = {
  id: "e1",
  patientId: PATIENT_ID,
  authorName: "Dr. Smith",
  occurredAt: "2024-01-10T10:00:00Z",
  description: "Older entry",
  attachments: [],
};

const newerEntry = {
  id: "e2",
  patientId: PATIENT_ID,
  authorName: "Dr. Smith",
  occurredAt: "2024-06-15T10:00:00Z",
  description: "Newer entry",
  attachments: [],
};

function renderPage(userType = "DOCTOR") {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={[`/patients/${PATIENT_ID}/clinical-entries`]}>
          <Routes>
            <Route
              path="/patients/:patientId/clinical-entries"
              element={<ClinicalEntriesPage userType={userType as "DOCTOR" | "PATIENT"} />}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("ClinicalEntriesPage", () => {
  it("SR-012 AC-4 / SR-006-007: renders list in reverse-chronological order", async () => {
    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([olderEntry, newerEntry])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    const items = screen.getAllByRole("listitem");
    const newerIdx = items.findIndex((el) => el.textContent?.includes("Newer entry"));
    const olderIdx = items.findIndex((el) => el.textContent?.includes("Older entry"));
    expect(newerIdx).toBeLessThan(olderIdx);
  });

  it("SR-012 AC-1: create form submit POSTs to /patients/{id}/clinical-entries and list refetches", async () => {
    const postSpy = vi.fn();
    const newEntry = {
      id: "e3",
      patientId: PATIENT_ID,
      authorName: "Dr. Smith",
      occurredAt: "2024-07-01T09:00:00Z",
      description: "Created entry",
      attachments: [],
    };
    let callCount = 0;

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () => {
        if (callCount > 0) return HttpResponse.json([newerEntry, newEntry]);
        callCount++;
        return HttpResponse.json([newerEntry]);
      }),
      http.post(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () => {
        postSpy();
        return HttpResponse.json(newEntry, { status: 201 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/description/i), "Created entry");
    await userEvent.type(screen.getByLabelText(/date/i), "2024-07-01");
    await userEvent.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalled();
    });

    // List refetches after mutation
    await waitFor(() => {
      expect(screen.getByText("Created entry")).toBeInTheDocument();
    });
  });

  it("SR-012 AC-3: create request body contains no author or doctorId field", async () => {
    let capturedBody: Record<string, unknown> | null = null;

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([])
      ),
      http.post(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, async ({ request }) => {
        capturedBody = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json(
          {
            id: "e-new",
            patientId: PATIENT_ID,
            authorName: "Dr. Smith",
            occurredAt: "2024-07-01T00:00:00Z",
            description: "Test",
            attachments: [],
          },
          { status: 201 }
        );
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/description/i), "Test");
    await userEvent.type(screen.getByLabelText(/date/i), "2024-07-01");
    await userEvent.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      expect(capturedBody).not.toBeNull();
    });

    expect(capturedBody).not.toHaveProperty("author");
    expect(capturedBody).not.toHaveProperty("doctorId");
  });

  it("SR-012 AC-2: create blocked when description empty", async () => {
    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    const submitBtn = screen.getByRole("button", { name: /add entry/i });
    expect(submitBtn).toBeDisabled();
  });

  it("SR-013 AC-1: uploads file including DICOM", async () => {
    const postSpy = vi.fn();

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      ),
      http.post(`${BASE}/clinical-entries/e2/attachments`, () => {
        postSpy();
        return HttpResponse.json({
          id: "att-1",
          filename: "scan.dcm",
          contentType: "application/dicom",
        });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    const file = new File(["dicom data"], "scan.dcm", {
      type: "application/dicom",
    });
    const input = screen.getByLabelText(/upload file/i);
    await userEvent.upload(input, file);

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalled();
    });
  });

  it("SR-007 read-only: patient role sees no create form", async () => {
    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      )
    );

    renderPage("patient");

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    expect(screen.queryByLabelText(/description/i)).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /add entry/i })).not.toBeInTheDocument();
  });

  it("SR-027.3: 403 shows access-denied surface", async () => {
    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json(
          {
            type: "/errors/forbidden",
            title: "Forbidden",
            status: 403,
          },
          { status: 403, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/access|forbidden|denied/i);
  });
});
