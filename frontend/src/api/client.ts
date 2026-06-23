import { withCsrf } from "./csrf";
import type {
  LoginRequest,
  LoginResponse,
  MeResponse,
  ChangePasswordRequest,
  ExtendSessionResponse,
  ProblemError,
} from "./generated/openapi";

export type { ProblemError };

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class AuthError extends Error {
  constructor(public readonly problem: ProblemError) {
    super(problem.title);
    this.name = "AuthError";
  }
}

export class ApiError extends Error {
  constructor(public readonly problem: ProblemError) {
    super(problem.title);
    this.name = "ApiError";
  }
}

export class ApiClient {
  private readonly baseUrl = "/api/v1";

  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const headers: HeadersInit = {};
    if (body !== undefined) {
      (headers as Record<string, string>)["Content-Type"] = "application/json";
    }

    const finalHeaders = MUTATING_METHODS.has(method)
      ? withCsrf(headers)
      : new Headers(headers);

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      credentials: "include",
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/problem+json")) {
        const problem: ProblemError = await response.json();
        if (
          response.status === 401 &&
          problem.type === "/errors/unauthenticated"
        ) {
          throw new AuthError(problem);
        }
        throw new ApiError(problem);
      }
      const problem: ProblemError = {
        type: "/errors/unknown",
        title: response.statusText || "Unknown error",
        status: response.status,
      };
      throw new ApiError(problem);
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return undefined as unknown as T;
    }

    const text = await response.text();
    if (!text) return undefined as unknown as T;
    return JSON.parse(text) as T;
  }

  login(data: LoginRequest): Promise<LoginResponse> {
    return this.request<LoginResponse>("POST", "/auth/login", data);
  }

  me(): Promise<MeResponse> {
    return this.request<MeResponse>("GET", "/users/me");
  }

  changePassword(data: ChangePasswordRequest): Promise<void> {
    return this.request<void>("PUT", "/users/me/password", data);
  }

  extendSession(): Promise<ExtendSessionResponse> {
    return this.request<ExtendSessionResponse>("POST", "/auth/session/extend");
  }

  logout(): Promise<void> {
    return this.request<void>("POST", "/auth/logout");
  }

  getActivation(token: string): Promise<void> {
    return this.request<void>("GET", `/activation/${token}`);
  }

  activate(token: string, password: string): Promise<void> {
    return this.request<void>("POST", `/activation/${token}`, { password });
  }
}
