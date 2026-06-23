import { describe, it, expect, beforeEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { ApiClient, ApiError, AuthError } from "./client";
import type { ProblemError } from "./client";

const BASE = "http://localhost/api/v1";

function makeClient() {
  return new ApiClient();
}

describe("ApiClient GET", () => {
  it("sends credentials:include but no X-CSRF-Token", async () => {
    let capturedRequest: Request | undefined;
    server.use(
      http.get(`${BASE}/users/me`, ({ request }) => {
        capturedRequest = request;
        return HttpResponse.json({ id: "1", email: "a@b.com", userType: "patient", mustChangePassword: false });
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
      value: "csrftoken=test-csrf-value",
    });
  });

  it("attaches X-CSRF-Token from cookie on POST", async () => {
    let capturedRequest: Request | undefined;
    server.use(
      http.post(`${BASE}/auth/login`, async ({ request }) => {
        capturedRequest = request;
        return HttpResponse.json({
          user: { id: "1", email: "a@b.com", userType: "patient", mustChangePassword: false },
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

  it("surfaces 401 /errors/unauthenticated as AuthError", async () => {
    const problem: ProblemError = {
      type: "/errors/unauthenticated",
      title: "Unauthenticated",
      status: 401,
    };
    server.use(
      http.get(`${BASE}/users/me`, () =>
        HttpResponse.json(problem, {
          status: 401,
          headers: { "Content-Type": "application/problem+json" },
        })
      )
    );

    const err = await makeClient()
      .me()
      .catch((e) => e);

    expect(err).toBeInstanceOf(AuthError);
    expect((err as AuthError).problem.type).toBe("/errors/unauthenticated");
  });
});
