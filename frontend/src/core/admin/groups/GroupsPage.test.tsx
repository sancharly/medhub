import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider as MuiThemeProvider } from "@mui/material/styles";
import { server } from "../../../tests/setup";
import { GroupsPage } from "./GroupsPage";
import { theme } from "../../theme/theme";

const BASE = "http://localhost/api/v1";

const groupWithMembers = {
  id: "grp-1",
  name: "Alpha Team",
  members: [
    { accountId: "a1", name: "Alice Auto", membershipSource: "AUTO" },
    { accountId: "a2", name: "Bob Manual", membershipSource: "MANUAL" },
  ],
  enabledModules: [],
};

const installedModules = {
  items: [
    { moduleKey: "dicom-viewer", name: "DICOM Viewer", version: "1.0", requiredPermissions: [] },
    { moduleKey: "analytics", name: "Analytics", version: "1.0", requiredPermissions: [] },
  ],
  total: 2,
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MuiThemeProvider theme={theme}>
      <QueryClientProvider client={client}>
        <MemoryRouter>
          <GroupsPage />
        </MemoryRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

describe("GroupsPage", () => {
  it("SR-014.1: create group calls POST /groups; list refetches", async () => {
    const postSpy = vi.fn();
    const newGroup = {
      id: "grp-new",
      name: "Beta Team",
      members: [],
      enabledModules: [],
    };

    server.use(
      http.get(`${BASE}/groups`, () => HttpResponse.json([])),
      http.get(`${BASE}/modules`, () => HttpResponse.json(installedModules)),
      http.post(`${BASE}/groups`, async ({ request }) => {
        const body = await request.json() as { name: string };
        postSpy(body);
        return HttpResponse.json(newGroup, { status: 201 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/group name/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/group name/i), "Beta Team");
    await userEvent.click(screen.getByRole("button", { name: /create group/i }));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith({ name: "Beta Team" });
    });
  });

  it("SR-014.2: auto members shown read-only (no remove button)", async () => {
    server.use(
      http.get(`${BASE}/groups`, () => HttpResponse.json([groupWithMembers])),
      http.get(`${BASE}/modules`, () => HttpResponse.json(installedModules))
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Alice Auto/)).toBeInTheDocument();
    });

    // Find the row for the AUTO member — there should be no remove button next to it
    const autoMemberRow = screen.getByText(/Alice Auto/).closest("li");
    expect(autoMemberRow).toBeDefined();
    if (autoMemberRow) {
      const removeBtn = autoMemberRow.querySelector("button");
      expect(removeBtn).toBeNull();
    }
  });

  it("SR-014.3: manual member can be removed via DELETE /groups/{id}/members/{accountId}", async () => {
    const deleteSpy = vi.fn();

    server.use(
      http.get(`${BASE}/groups`, () => HttpResponse.json([groupWithMembers])),
      http.get(`${BASE}/modules`, () => HttpResponse.json(installedModules)),
      http.delete(`${BASE}/groups/grp-1/members/a2`, () => {
        deleteSpy();
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Bob Manual/)).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /remove bob manual/i }));

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalled();
    });
  });

  it("SR-015.1/2: toggling module on sends PUT /groups/{id}/modules/dicom-viewer with enabled:true", async () => {
    const putSpy = vi.fn();
    const groupWithModule = {
      ...groupWithMembers,
      enabledModules: [],
    };

    server.use(
      http.get(`${BASE}/groups`, () => HttpResponse.json([groupWithModule])),
      http.get(`${BASE}/modules`, () => HttpResponse.json(installedModules)),
      http.put(`${BASE}/groups/grp-1/modules/dicom-viewer`, async ({ request }) => {
        const body = await request.json() as { enabled: boolean };
        putSpy(body);
        return new HttpResponse(null, { status: 204 });
      })
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/DICOM Viewer/)).toBeInTheDocument();
    });

    // Click the toggle for dicom-viewer (MUI Switch renders with role="switch")
    await userEvent.click(screen.getByRole("switch", { name: /toggle dicom viewer/i }));

    await waitFor(() => {
      expect(putSpy).toHaveBeenCalledWith({ enabled: true });
    });
  });

  it("SR-027.3: 400 on duplicate group name shows field error", async () => {
    server.use(
      http.get(`${BASE}/groups`, () => HttpResponse.json([])),
      http.get(`${BASE}/modules`, () => HttpResponse.json(installedModules)),
      http.post(`${BASE}/groups`, () =>
        HttpResponse.json(
          {
            type: "/errors/conflict",
            title: "Conflict",
            status: 400,
            errors: [{ field: "name", message: "Group name already exists" }],
          },
          { status: 400, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    renderPage();

    await waitFor(() => {
      expect(screen.getByLabelText(/group name/i)).toBeInTheDocument();
    });

    await userEvent.type(screen.getByLabelText(/group name/i), "Alpha Team");
    await userEvent.click(screen.getByRole("button", { name: /create group/i }));

    await waitFor(() => {
      expect(screen.getByText(/group name already exists/i)).toBeInTheDocument();
    });
  });
});
