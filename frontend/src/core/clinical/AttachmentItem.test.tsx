import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { delay, http, HttpResponse } from "msw";
import { server } from "../../tests/setup";
import { queryKeys } from "../../api/queryKeys";
import type { Attachment } from "../../api/generated/types";
import { AttachmentItem } from "./AttachmentItem";

const BASE = "http://localhost/api/v1";

function attachment(contentType: string, filename = "file.bin"): Attachment {
  return { id: "att-1", filename, contentType } as Attachment;
}

function renderItem(item: Attachment) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={client}>
      <AttachmentItem attachment={item} />
    </QueryClientProvider>
  );
  return client;
}

function serveModules(modules: string[]) {
  const state = { calls: 0 };
  server.use(
    http.get(`${BASE}/me/modules`, () => {
      state.calls += 1;
      return HttpResponse.json({ modules });
    })
  );
  return state;
}

const VIEWER = { name: "Open in viewer" };

// SR-015 AC 3 and AC 4 at unit level (PRB-017, TASK-146). The refresh of the list (AC 5) is
// covered by modules/useMyModules.test.tsx.
describe("AttachmentItem", () => {
  it("shows the file name and a Download link to the attachment", async () => {
    const state = serveModules([]);
    renderItem(attachment("application/pdf", "report.pdf"));
    await waitFor(() => expect(state.calls).toBe(1));

    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    const download = screen.getByRole("link", { name: "Download" });
    expect(download).toHaveAttribute("href", "/api/v1/attachments/att-1");
    expect(download).toHaveAttribute("target", "_blank");
    expect(download).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });

  it("offers the viewer for a DICOM attachment when the DICOM module is enabled for the user", async () => {
    serveModules(["dicom-viewer"]);
    renderItem(attachment("application/dicom", "scan.dcm"));

    const viewer = await screen.findByRole("link", VIEWER);
    expect(viewer).toHaveAttribute("href", "/api/v1/attachments/att-1");
    expect(viewer).toHaveAttribute("target", "_blank");
    expect(viewer).toHaveAttribute("rel", expect.stringContaining("noopener"));
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });

  it("offers no viewer for a DICOM attachment when the user's module list is empty", async () => {
    const state = serveModules([]);
    renderItem(attachment("application/dicom"));
    await waitFor(() => expect(state.calls).toBe(1));
    await waitFor(() => expect(screen.getByText("file.bin")).toBeInTheDocument());

    expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });

  it("offers no viewer when only other modules are enabled", async () => {
    const state = serveModules(["some-other-module"]);
    renderItem(attachment("application/dicom"));
    await waitFor(() => expect(state.calls).toBe(1));
    await waitFor(() => expect(screen.getByText("file.bin")).toBeInTheDocument());

    expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument();
  });

  it("offers no viewer for a non-DICOM attachment even when the DICOM module is enabled, and keeps Download", async () => {
    serveModules(["dicom-viewer"]);
    const client = renderItem(attachment("image/png", "photo.png"));
    await waitFor(() => expect(client.getQueryData(queryKeys.myModules)).toEqual(["dicom-viewer"]));

    expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });

  it("offers no viewer while the module list is still loading", async () => {
    server.use(
      http.get(`${BASE}/me/modules`, async () => {
        await delay(200);
        return HttpResponse.json({ modules: ["dicom-viewer"] });
      })
    );
    renderItem(attachment("application/dicom"));

    expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument();
    expect(await screen.findByRole("link", VIEWER)).toBeInTheDocument();
  });

  it("offers no viewer when the module list cannot be loaded", async () => {
    server.use(http.get(`${BASE}/me/modules`, () => new HttpResponse(null, { status: 500 })));
    const client = renderItem(attachment("application/dicom"));

    // The hook retries once after a second, so the error state arrives later.
    await waitFor(() => expect(client.getQueryState(queryKeys.myModules)?.status).toBe("error"), {
      timeout: 4000,
    });

    expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });

  it("removes the viewer once the module is no longer in the user's list", async () => {
    serveModules(["dicom-viewer"]);
    const client = renderItem(attachment("application/dicom"));
    expect(await screen.findByRole("link", VIEWER)).toBeInTheDocument();

    serveModules([]);
    await client.refetchQueries({ queryKey: queryKeys.myModules });

    await waitFor(() => expect(screen.queryByRole("link", VIEWER)).not.toBeInTheDocument());
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });
});
