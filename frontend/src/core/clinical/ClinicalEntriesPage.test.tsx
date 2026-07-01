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
const DOCTOR_ID = "doc-1";

const doctorMe = {
  id: DOCTOR_ID,
  email: "doctor@test.com",
  userType: "DOCTOR",
  state: "ACTIVE",
  firstName: "Greg",
  surname: "House",
  dateOfBirth: null,
  createdAt: "2024-01-01T00:00:00Z",
  mustChangePassword: false,
};

const olderEntry = {
  id: "e1",
  patientId: PATIENT_ID,
  authorId: DOCTOR_ID,
  authorName: "Greg House",
  occurredAt: "2024-01-10T10:00:00Z",
  description: "Older entry",
  createdAt: "2024-01-10T10:00:00Z",
};

const newerEntry = {
  id: "e2",
  patientId: PATIENT_ID,
  authorId: DOCTOR_ID,
  authorName: "Greg House",
  occurredAt: "2024-06-15T10:00:00Z",
  description: "Newer entry",
  createdAt: "2024-06-15T10:00:00Z",
};

function mockMeAndModules(modules: string[] = []) {
  server.use(
    http.get(`${BASE}/me`, () => HttpResponse.json(doctorMe)),
    http.get(`${BASE}/me/modules`, () => HttpResponse.json({ modules }))
  );
}

function mockEmptyAttachments(entryId = "e2") {
  server.use(
    http.get(`${BASE}/clinical-entries/${entryId}/attachments`, () => HttpResponse.json([]))
  );
}

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
    mockMeAndModules();
    mockEmptyAttachments("e1");
    mockEmptyAttachments("e2");
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
    mockMeAndModules();
    mockEmptyAttachments("e2");
    mockEmptyAttachments("e3");
    const postSpy = vi.fn();
    const newEntry = {
      id: "e3",
      patientId: PATIENT_ID,
      authorId: DOCTOR_ID,
      authorName: "Greg House",
      occurredAt: "2024-07-01T09:00:00Z",
      description: "Created entry",
      createdAt: "2024-07-01T09:00:00Z",
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
    await userEvent.type(screen.getByLabelText(/^date/i), "2024-07-01");
    await userEvent.type(screen.getByLabelText(/^time/i), "09:00");
    await userEvent.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalled();
    });

    // List refetches after mutation
    await waitFor(() => {
      expect(screen.getByText("Created entry")).toBeInTheDocument();
    });
  });

  it("SR-012 AC-3: create request body contains no author or doctorId field, and carries full date+time", async () => {
    mockMeAndModules();
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
            authorId: DOCTOR_ID,
            occurredAt: "2024-07-01T09:30:00.000Z",
            description: "Test",
            createdAt: "2024-07-01T09:30:00.000Z",
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
    await userEvent.type(screen.getByLabelText(/^date/i), "2024-07-01");
    await userEvent.type(screen.getByLabelText(/^time/i), "09:30");
    await userEvent.click(screen.getByRole("button", { name: /add entry/i }));

    await waitFor(() => {
      expect(capturedBody).not.toBeNull();
    });

    expect(capturedBody).not.toHaveProperty("author");
    expect(capturedBody).not.toHaveProperty("doctorId");
    const sentOccurredAt = (capturedBody as unknown as { occurredAt: string }).occurredAt;
    const expected = new Date("2024-07-01T09:30").toISOString();
    expect(sentOccurredAt).toBe(expected);
  });

  it("SR-012 AC-2: create blocked when description, date, or time are missing", async () => {
    mockMeAndModules();
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

    await userEvent.type(screen.getByLabelText(/description/i), "Test");
    expect(submitBtn).toBeDisabled();

    await userEvent.type(screen.getByLabelText(/^date/i), "2024-07-01");
    expect(submitBtn).toBeDisabled();
  });

  it("SR-013 AC-1: uploads multiple files including DICOM in one selection", async () => {
    mockMeAndModules();
    const postSpy = vi.fn();
    const uploaded: Record<string, unknown>[] = [];

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      ),
      http.get(`${BASE}/clinical-entries/e2/attachments`, () => HttpResponse.json(uploaded)),
      http.post(`${BASE}/clinical-entries/e2/attachments`, () => {
        postSpy();
        const callNum = postSpy.mock.calls.length;
        const [filename, contentType] =
          callNum === 1 ? ["scan.dcm", "application/dicom"] : ["note.txt", "text/plain"];
        const attachment = {
          id: `att-${callNum}`,
          clinicalEntryId: "e2",
          patientId: PATIENT_ID,
          filename,
          contentType,
          size: 10,
          checksum: "abc",
          createdAt: "2024-06-15T10:00:00Z",
        };
        uploaded.push(attachment);
        return HttpResponse.json(attachment);
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    const dicomFile = new File(["dicom data"], "scan.dcm", {
      type: "application/dicom",
    });
    const otherFile = new File(["note"], "note.txt", { type: "text/plain" });
    const input = screen.getByLabelText(/upload file/i);
    expect(input).toHaveAttribute("multiple");
    await userEvent.upload(input, [dicomFile, otherFile]);

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledTimes(2);
    });

    await waitFor(() => {
      expect(screen.getByText("scan.dcm")).toBeInTheDocument();
      expect(screen.getByText("note.txt")).toBeInTheDocument();
    });
  });

  it("SR-013 AC-3 / SR-015/016: DICOM attachment offers 'Open in viewer' only when module is enabled", async () => {
    const postSpy = vi.fn();
    const uploaded: Record<string, unknown>[] = [];

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      ),
      http.get(`${BASE}/clinical-entries/e2/attachments`, () => HttpResponse.json(uploaded)),
      http.post(`${BASE}/clinical-entries/e2/attachments`, () => {
        postSpy();
        const attachment = {
          id: "att-dicom",
          clinicalEntryId: "e2",
          patientId: PATIENT_ID,
          filename: "scan.dcm",
          contentType: "application/dicom",
          size: 10,
          checksum: "abc",
          createdAt: "2024-06-15T10:00:00Z",
        };
        uploaded.push(attachment);
        return HttpResponse.json(attachment);
      })
    );

    // Module disabled — no viewer link
    mockMeAndModules([]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    const dicomFile = new File(["dicom data"], "scan.dcm", { type: "application/dicom" });
    await userEvent.upload(screen.getByLabelText(/upload file/i), dicomFile);

    await waitFor(() => {
      expect(screen.getByText("scan.dcm")).toBeInTheDocument();
    });
    expect(screen.queryByText(/open in viewer/i)).not.toBeInTheDocument();
  });

  it("SR-013 AC-3 / SR-015/016: viewer link appears when DICOM module is enabled", async () => {
    const postSpy = vi.fn();
    const uploaded: Record<string, unknown>[] = [];

    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      ),
      http.get(`${BASE}/clinical-entries/e2/attachments`, () => HttpResponse.json(uploaded)),
      http.post(`${BASE}/clinical-entries/e2/attachments`, () => {
        postSpy();
        const attachment = {
          id: "att-dicom",
          clinicalEntryId: "e2",
          patientId: PATIENT_ID,
          filename: "scan.dcm",
          contentType: "application/dicom",
          size: 10,
          checksum: "abc",
          createdAt: "2024-06-15T10:00:00Z",
        };
        uploaded.push(attachment);
        return HttpResponse.json(attachment);
      })
    );

    mockMeAndModules(["dicom-viewer"]);
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    const dicomFile = new File(["dicom data"], "scan.dcm", { type: "application/dicom" });
    await userEvent.upload(screen.getByLabelText(/upload file/i), dicomFile);

    await waitFor(() => {
      expect(screen.getByText(/open in viewer/i)).toBeInTheDocument();
    });
  });

  it("SR-012 AC-4: shows the authoring doctor's name, not the raw authorId", async () => {
    mockMeAndModules();
    mockEmptyAttachments("e2");
    server.use(
      http.get(`${BASE}/patients/${PATIENT_ID}/clinical-entries`, () =>
        HttpResponse.json([newerEntry])
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Newer entry")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/Author:\s*Greg House/)).toBeInTheDocument();
    });
    expect(screen.queryByText(DOCTOR_ID)).not.toBeInTheDocument();
  });

  it("SR-007 read-only: patient role sees no create form", async () => {
    mockMeAndModules();
    mockEmptyAttachments("e2");
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
    mockMeAndModules();
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
