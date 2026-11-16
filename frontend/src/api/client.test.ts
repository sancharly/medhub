import { describe, it, expect, beforeEach, vi } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { ApiClient, ApiError, AuthError } from "./client";
import type { ProblemError } from "./problem";

const BASE = "http://localhost/api/v1";

function makeClient() {
  return new ApiClient();
}

describe("ApiClient GET", () => {
  it("sends credentials:include but no X-CSRF-Token", async () => {
    let capturedRequest: Request | undefined;
    server.use(
      http.get(`${BASE}/me`, ({ request }) => {
        capturedRequest = request;
        return HttpResponse.json({ id: "1", email: "a@b.com", userType: "PATIENT", mustChangePassword: false });
      })
    );

    await makeClient().me();

    expect(capturedRequest).toBeDefined();
    expect(capturedRequest!.headers.get("X-CSRF-Token")).toBeNull();
  });
});

describe("ApiClient POST", () => {
  beforeEach(() => {
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "medhub_csrf=test-csrf-value",
    });
  });

  it("attaches X-CSRF-Token from cookie on POST", async () => {
    let capturedRequest: Request | undefined;
    server.use(
      http.post(`${BASE}/auth/login`, async ({ request }) => {
        capturedRequest = request;
        return HttpResponse.json({
          user: { id: "1", email: "a@b.com", userType: "PATIENT", mustChangePassword: false },
          mustChangePassword: false,
          evictedSession: false,
        });
      })
    );

    await makeClient().login({ email: "a@b.com", password: "pass" });

    expect(capturedRequest!.headers.get("X-CSRF-Token")).toBe(
      "test-csrf-value"
    );
  });
});

describe("ApiClient error handling", () => {
  it("parses application/problem+json 4xx into ApiError", async () => {
    const problem: ProblemError = {
      type: "/errors/validation-error",
      title: "Validation failed",
      status: 422,
      detail: "Email is required",
    };
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json(problem, {
          status: 422,
          headers: { "Content-Type": "application/problem+json" },
        })
      )
    );

    await expect(
      makeClient().login({ email: "", password: "" })
    ).rejects.toBeInstanceOf(ApiError);
  });

  it("parses application/problem+json 5xx into ApiError", async () => {
    const problem: ProblemError = {
      type: "/errors/internal",
      title: "Internal Server Error",
      status: 500,
    };
    server.use(
      http.post(`${BASE}/auth/login`, () =>
        HttpResponse.json(problem, {
          status: 500,
          headers: { "Content-Type": "application/problem+json" },
        })
      )
    );

    await expect(
      makeClient().login({ email: "a@b.com", password: "x" })
    ).rejects.toBeInstanceOf(ApiError);
  });

  it("surfaces 401 /errors/unauthenticated as AuthError (relative type)", async () => {
    const problem: ProblemError = {
      type: "/errors/unauthenticated",
      title: "Unauthenticated",
      status: 401,
    };
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(problem, {
          status: 401,
          headers: { "Content-Type": "application/problem+json" },
        })
      )
    );

    const err = await makeClient().me().catch((e) => e);
    expect(err).toBeInstanceOf(AuthError);
  });

  it("surfaces 401 with full-URL type as AuthError (production backend format)", async () => {
    const problem: ProblemError = {
      type: "https://medhub.example/errors/unauthenticated",
      title: "Unauthenticated",
      status: 401,
    };
    server.use(
      http.get(`${BASE}/me`, () =>
        HttpResponse.json(problem, {
          status: 401,
          headers: { "Content-Type": "application/problem+json" },
        })
      )
    );

    const err = await makeClient().me().catch((e) => e);
    expect(err).toBeInstanceOf(AuthError);
  });
});

describe("ApiClient uploadAttachment", () => {
  const URL = `${BASE}/clinical-entries/e1/attachments`;
  const file = () => new File(["hello"], "note.txt", { type: "text/plain" });
  const attachment = {
    id: "a1",
    clinicalEntryId: "e1",
    filename: "note.txt",
    contentType: "text/plain",
    sizeBytes: 5,
    createdAt: "2026-01-01T00:00:00Z",
  };

  beforeEach(() => {
    Object.defineProperty(document, "cookie", {
      writable: true,
      value: "medhub_csrf=test-csrf-value",
    });
  });

  it("sends FormData through request with the CSRF header", async () => {
    // Inspect what reaches fetch rather than the serialized body: under jsdom,
    // Node's fetch cannot serialize jsdom's FormData (it hangs on Node 20 and
    // fails on Node 24), while a browser sets the multipart boundary itself.
    const fetchSpy = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(HttpResponse.json(attachment, { status: 201 }));
    try {
      const result = await makeClient().uploadAttachment("e1", file());

      expect(result).toEqual(attachment);
      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const [url, init] = fetchSpy.mock.calls[0];
      expect(String(url)).toBe("/api/v1/clinical-entries/e1/attachments");
      expect(init?.method).toBe("POST");
      const headers = new Headers(init?.headers);
      expect(headers.get("X-CSRF-Token")).toBe("test-csrf-value");
      // No hand-set content type: the browser adds multipart/form-data with its boundary.
      expect(headers.get("content-type")).toBeNull();
      expect(init?.body).toBeInstanceOf(FormData);
      expect(((init?.body as FormData).get("file") as File).name).toBe("note.txt");
    } finally {
      fetchSpy.mockRestore();
    }
  });

  it("raises AuthError on a 401 unauthenticated problem", async () => {
    server.use(
      http.post(URL, () =>
        HttpResponse.json(
          { type: "/errors/unauthenticated", title: "Unauthenticated", status: 401 },
          { status: 401, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    const err = await makeClient().uploadAttachment("e1", file()).catch((e) => e);
    expect(err).toBeInstanceOf(AuthError);
  });

  it.each([
    [413, "/errors/payload-too-large", "The file is larger than 150 MiB."],
    [400, "/errors/validation-error", "The file type is not allowed."],
  ])("surfaces the server detail of a problem+json %i", async (status, type, detail) => {
    server.use(
      http.post(URL, () =>
        HttpResponse.json(
          { type, title: "Refused", status, detail },
          { status, headers: { "Content-Type": "application/problem+json" } }
        )
      )
    );

    const err = await makeClient().uploadAttachment("e1", file()).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).not.toBeInstanceOf(AuthError);
    expect((err as ApiError).problem.detail).toBe(detail);
    expect((err as ApiError).problem.status).toBe(status);
  });

  it("raises a generic ApiError for a non-problem 500", async () => {
    server.use(
      http.post(URL, () => new HttpResponse("boom", { status: 500, statusText: "Server Error" }))
    );

    const err = await makeClient().uploadAttachment("e1", file()).catch((e) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect((err as ApiError).problem).toMatchObject({
      type: "/errors/unknown",
      status: 500,
    });
  });
});
