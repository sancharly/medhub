import { describe, it, expect } from "vitest";
import { problemToMessage } from "./problemToMessage";
import type { ProblemError } from "../../api/generated/openapi";

describe("problemToMessage", () => {
  it("uses detail as summary when present", () => {
    const problem: ProblemError = {
      type: "/errors/validation",
      title: "Validation Error",
      status: 422,
      detail: "Email is required",
    };
    expect(problemToMessage(problem).summary).toBe("Email is required");
  });

  it("falls back to title when detail is absent", () => {
    const problem: ProblemError = {
      type: "/errors/not-found",
      title: "Not Found",
      status: 404,
    };
    expect(problemToMessage(problem).summary).toBe("Not Found");
  });

  it("expands errors[] into fieldErrors", () => {
    const problem: ProblemError = {
      type: "/errors/validation",
      title: "Validation Error",
      status: 422,
      errors: [
        { field: "email", message: "Must be valid email" },
        { field: "password", message: "Too short" },
      ],
    };
    const result = problemToMessage(problem);
    expect(result.fieldErrors).toHaveLength(2);
    expect(result.fieldErrors![0].field).toBe("email");
    expect(result.fieldErrors![1].field).toBe("password");
  });

  it("returns no fieldErrors when errors array is absent", () => {
    const problem: ProblemError = {
      type: "/errors/not-found",
      title: "Not Found",
      status: 404,
    };
    expect(problemToMessage(problem).fieldErrors).toBeUndefined();
  });
});
