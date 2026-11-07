import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { server } from "../../tests/setup";
import { AttachmentUpload } from "./AttachmentUpload";

const BASE = "http://localhost/api/v1";

function renderUpload() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <AttachmentUpload entryId="e1" patientId="p1" />
    </QueryClientProvider>
  );
}

describe("AttachmentUpload", () => {
  it("shows the problem detail when the upload is refused", async () => {
    server.use(
      http.post(
        `${BASE}/clinical-entries/e1/attachments`,
        () =>
          HttpResponse.json(
            {
              type: "/errors/validation-error",
              title: "Validation Error",
              status: 400,
              detail: "The file name is longer than 255 bytes.",
              instance: "/api/v1/clinical-entries/e1/attachments",
              errors: [
                { field: "file", rule: "filename_max_bytes", message: "The file name is longer than 255 bytes." },
              ],
            },
            { status: 400, headers: { "Content-Type": "application/problem+json" } }
          )
      )
    );
    renderUpload();
    const user = userEvent.setup();
    await user.upload(screen.getByLabelText("Upload file"), new File(["x"], "long.pdf"));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("The file name is longer than 255 bytes.");
  });

  it("shows a generic message when the failure carries no problem document", async () => {
    server.use(
      http.post(`${BASE}/clinical-entries/e1/attachments`, () => new HttpResponse(null, { status: 500 }))
    );
    renderUpload();
    const user = userEvent.setup();
    await user.upload(screen.getByLabelText("Upload file"), new File(["x"], "a.pdf"));
    expect(await screen.findByRole("alert")).toHaveTextContent(/could not be uploaded/i);
  });

  it("shows no alert after a successful upload", async () => {
    let posted = false;
    server.use(
      http.post(`${BASE}/clinical-entries/e1/attachments`, () => {
        posted = true;
        return HttpResponse.json({ id: "a1", filename: "a.pdf" }, { status: 201 });
      })
    );
    renderUpload();
    const user = userEvent.setup();
    await user.upload(screen.getByLabelText("Upload file"), new File(["x"], "a.pdf"));
    await waitFor(() => expect(posted).toBe(true));
    expect(screen.queryByRole("alert")).toBeNull();
  });
});
