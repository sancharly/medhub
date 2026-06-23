import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../../tests/setup";
import { PatientListPage } from "./PatientListPage";
import { theme } from "../theme/theme";

const BASE = "http://localhost/api/v1";

const mockPatients = [
  { id: "p1", firstName: "Alice", surname: "Smith", dateOfBirth: "1990-01-15" },
  { id: "p2", firstName: "Bob", surname: "Jones", dateOfBirth: "1985-06-20" },
  { id: "p3", firstName: "Carol", surname: "White", dateOfBirth: "1975-11-05" },
];

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter initialEntries={["/patients"]}>
          <Routes>
            <Route path="/patients" element={<PatientListPage />} />
            <Route
              path="/patients/:id/clinical-entries"
              element={<div data-testid="clinical-page">Clinical Entries</div>}
            />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("PatientListPage", () => {
  it("SR-006 AC-1: renders all 3 returned patients with name and surname", async () => {
    server.use(
      http.get(`${BASE}/clinical-entries/patients`, () =>
        HttpResponse.json(mockPatients)
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });
    expect(screen.getByText(/Bob/)).toBeInTheDocument();
    expect(screen.getByText(/Carol/)).toBeInTheDocument();
    expect(screen.getByText(/Smith/)).toBeInTheDocument();
    expect(screen.getByText(/Jones/)).toBeInTheDocument();
    expect(screen.getByText(/White/)).toBeInTheDocument();
  });

  it("SR-006 AC-1 edge: empty list shows empty-state message, no error", async () => {
    server.use(
      http.get(`${BASE}/clinical-entries/patients`, () => HttpResponse.json([]))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/no patients/i)).toBeInTheDocument();
    });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("SR-006 AC-3 / SR-031.5: renders exactly the server-returned set, no client-side filtering", async () => {
    server.use(
      http.get(`${BASE}/clinical-entries/patients`, () =>
        HttpResponse.json(mockPatients)
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    // All 3 patients from mock are rendered — no more, no fewer
    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(mockPatients.length);
  });

  it("SR-027.3: clicking a patient navigates to /patients/{id}/clinical-entries", async () => {
    server.use(
      http.get(`${BASE}/clinical-entries/patients`, () =>
        HttpResponse.json(mockPatients)
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Alice/)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText(/Alice/));

    await waitFor(() => {
      expect(screen.getByTestId("clinical-page")).toBeInTheDocument();
    });
  });

  it("SR-027.3: shows error detail on 500", async () => {
    server.use(
      http.get(`${BASE}/clinical-entries/patients`, () =>
        HttpResponse.json(
          {
            type: "/errors/internal",
            title: "Internal Server Error",
            status: 500,
            detail: "Unexpected failure",
          },
          { status: 500, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("alert")).toHaveTextContent(/error|failed|unavailable/i);
  });
});
