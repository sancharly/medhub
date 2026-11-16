import type { components } from "./generated/openapi";

/**
 * RFC 7807 problem document as the client uses it. Derived from the generated
 * `ProblemDetail` schema; `detail` is optional because client-synthesised errors
 * (non-problem responses) have none, and `errors` carries the field-level shape the
 * UI reads (the schema leaves its items untyped). Hand-written, outside the generated files.
 */
export type ProblemError = Omit<components["schemas"]["ProblemDetail"], "detail" | "errors"> & {
  detail?: string;
  errors?: Array<{ field?: string; rule?: string; message?: string }>;
};
