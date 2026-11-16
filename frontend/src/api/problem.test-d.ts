// Type-level test: `npm run typecheck` fails if the generated ProblemDetail schema
// loses a field that ProblemError uses (TASK-143, SR-031).
import type { components } from "./generated/openapi";
import type { ProblemError } from "./problem";

type Schema = components["schemas"]["ProblemDetail"];

// Every field ProblemError builds on or overrides must exist in the schema: `Pick` only accepts
// keys of the schema, so if it drops one of them this alias, and with it `npm run typecheck`, fails.
export type SchemaFields = Pick<Schema, "type" | "title" | "status" | "instance" | "detail" | "errors">;
// ...and ProblemError exposes all of them.
export const exposed: (keyof SchemaFields)[] = [] as (keyof ProblemError)[];

// A field the schema never had is not on ProblemError either.
// @ts-expect-error `bogus` is not a ProblemDetail field
export type Bogus = ProblemError["bogus"];

// `detail` is optional on ProblemError (synthetic errors omit it).
export const synthetic: ProblemError = { type: "/errors/unknown", title: "x", status: 500 };
