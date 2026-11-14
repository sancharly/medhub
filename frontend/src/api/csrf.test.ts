import { describe, it, expect, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../tests/setup";
import { ApiClient } from "./client";
import { withCsrf } from "./csrf";

const BASE = "http://localhost/api/v1";

function setCookie(name: string, value: string) {
  document.cookie = `${name}=${value}; path=/`;
}

function clearCookies() {
  for (const entry of document.cookie.split("; ")) {
    const name = entry.split("=")[0];
    if (name) document.cookie = `${name}=; path=/; max-age=0`;
  }
}

afterEach(clearCookies);

// SR-031 AC 3, NFR-006 AC 3 (unit level, PRB-017, TASK-146).
describe("withCsrf", () => {
  it("copies the medhub_csrf cookie into X-CSRF-Token, whatever else the cookie jar holds", () => {
    setCookie("theme", "dark");
    setCookie("medhub_csrf", "tok-123");
    setCookie("zzz", "last");

    expect(withCsrf({}).get("X-CSRF-Token")).toBe("tok-123");
  });

  it("keeps the whole token when it contains an equals sign", () => {
    setCookie("medhub_csrf", "abc==");

    expect(withCsrf({}).get("X-CSRF-Token")).toBe("abc==");
  });

  it("does not take a cookie whose name only starts or ends like the CSRF cookie", () => {
    setCookie("medhub_csrf_other", "wrong-1");
    setCookie("xmedhub_csrf", "wrong-2");

    expect(withCsrf({}).has("X-CSRF-Token")).toBe(false);
  });

  it("tolerates an absent cookie: no header and no throw", () => {
    expect(document.cookie).toBe("");

    let headers: Headers | undefined;
    expect(() => {
      headers = withCsrf({ "Content-Type": "application/json" });
    }).not.toThrow();
    expect(headers!.has("X-CSRF-Token")).toBe(false);
  });

  it("keeps the headers it was given and does not change the object passed in", () => {
    setCookie("medhub_csrf", "tok");
    const given: Record<string, string> = { "Content-Type": "application/json" };

    const result = withCsrf(given);

    expect(result.get("Content-Type")).toBe("application/json");
    expect(result.get("X-CSRF-Token")).toBe("tok");
    expect(given).toEqual({ "Content-Type": "application/json" });
  });
});

// The method gate sits in the client: the header goes on POST, PUT, PATCH and DELETE, never on GET.
describe("the request helper and the CSRF header", () => {
  it("sends no X-CSRF-Token on GET even when the cookie is present", async () => {
    setCookie("medhub_csrf", "tok");
    let seen: Request | undefined;
    server.use(
      http.get(`${BASE}/groups`, ({ request }) => {
        seen = request;
        return HttpResponse.json([]);
      })
    );

    await new ApiClient().listGroups();

    expect(seen!.headers.has("X-CSRF-Token")).toBe(false);
  });

  it.each([
    ["POST", () => new ApiClient().login({ email: "a@b.com", password: "x" }), "post", "/auth/login"],
    [
      "PUT",
      () => new ApiClient().setGroupModuleEnabled("g1", "dicom-viewer", true),
      "put",
      "/groups/g1/modules/dicom-viewer",
    ],
    ["DELETE", () => new ApiClient().removeGroupMember("g1", "a1"), "delete", "/groups/g1/members/a1"],
  ] as const)("sends X-CSRF-Token on %s", async (_method, call, verb, path) => {
    setCookie("medhub_csrf", "tok-" + verb);
    let seen: Request | undefined;
    server.use(
      http[verb](`${BASE}${path}`, ({ request }) => {
        seen = request;
        return HttpResponse.json({});
      })
    );

    await call();

    expect(seen!.headers.get("X-CSRF-Token")).toBe("tok-" + verb);
  });

  it("sends X-CSRF-Token on PATCH (no public method uses PATCH, so the private helper is called)", async () => {
    setCookie("medhub_csrf", "tok-patch");
    let seen: Request | undefined;
    server.use(
      http.patch(`${BASE}/anything`, ({ request }) => {
        seen = request;
        return HttpResponse.json({});
      })
    );
    const client = new ApiClient() as unknown as {
      request: (method: string, path: string, body?: unknown) => Promise<unknown>;
    };

    await client.request("PATCH", "/anything", { a: 1 });

    expect(seen!.headers.get("X-CSRF-Token")).toBe("tok-patch");
  });

  it("sends a mutating request without the header, and without error, when the cookie is absent", async () => {
    let seen: Request | undefined;
    server.use(
      http.post(`${BASE}/auth/logout`, ({ request }) => {
        seen = request;
        return new HttpResponse(null, { status: 204 });
      })
    );

    await expect(new ApiClient().logout()).resolves.toBeUndefined();

    expect(seen!.headers.has("X-CSRF-Token")).toBe(false);
  });
});
