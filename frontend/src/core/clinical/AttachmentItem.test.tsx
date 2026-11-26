import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { http, HttpResponse } from "msw";
import { server } from "../../tests/setup";
import type { Attachment } from "../../api/generated/types";
import { AttachmentItem } from "./AttachmentItem";

const BASE = "http://localhost/api/v1";
const VIEWER = /viewer/i;

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
}

/** Serves `/me/modules` and counts the requests it receives. */
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

// SR-017 AC 11: no control claims to open a viewer that does not exist; Download stays
// (CR-008 D-5, PRB-048). The real entry point arrives with issue #29.
describe("AttachmentItem", () => {
  it("shows the file name and a Download link to the attachment", () => {
    renderItem(attachment("application/pdf", "report.pdf"));

    expect(screen.getByText("report.pdf")).toBeInTheDocument();
    const download = screen.getByRole("link", { name: "Download" });
    expect(download).toHaveAttribute("href", "/api/v1/attachments/att-1");
    expect(download).toHaveAttribute("target", "_blank");
    expect(download).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });

  it("offers no viewer for a DICOM attachment even when the DICOM module is enabled", async () => {
    const state = serveModules(["dicom-viewer"]);
    renderItem(attachment("application/dicom", "scan.dcm"));
    // Let any module request settle, so a late viewer link would be seen.
    await new Promise((r) => setTimeout(r, 100));

    expect(screen.queryByRole("link", { name: VIEWER })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: VIEWER })).not.toBeInTheDocument();
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(1);
    expect(links[0]).toHaveAccessibleName("Download");
    expect(links[0]).toHaveAttribute("href", "/api/v1/attachments/att-1");
    expect(state.calls).toBe(0);
  });

  it("offers no viewer for a non-DICOM attachment, and keeps Download", async () => {
    serveModules(["dicom-viewer"]);
    renderItem(attachment("image/png", "photo.png"));
    await new Promise((r) => setTimeout(r, 100));

    expect(screen.queryByRole("link", { name: VIEWER })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: VIEWER })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Download" })).toBeInTheDocument();
  });

  it("does not request the user's module list", async () => {
    const state = serveModules(["dicom-viewer"]);
    renderItem(attachment("application/dicom"));
    await new Promise((r) => setTimeout(r, 100));

    expect(state.calls).toBe(0);
  });
});
