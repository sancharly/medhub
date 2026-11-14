// @vitest-environment node
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import openapiTS, { astToString, COMMENT_HEADER } from "openapi-typescript";

// The generated types must be what `npm run generate:types` produces from the committed schema
// (CLAUDE.md "Backend/Frontend Contract"; RISK-005 client-session row, PRB-017, TASK-146). CI
// repeats the check from the backend export (`openapi-lint`); this one runs with the unit tests.
const SCHEMA = fileURLToPath(new URL("../../../../backend/openapi/openapi.json", import.meta.url));
const GENERATED = fileURLToPath(new URL("./openapi.ts", import.meta.url));

async function regenerate(schema: unknown): Promise<string> {
  return COMMENT_HEADER + astToString(await openapiTS(schema as never));
}

describe("generated API types", () => {
  it("openapi.ts equals the output of the generator for backend/openapi/openapi.json", async () => {
    const schema = JSON.parse(readFileSync(SCHEMA, "utf8"));

    expect(await regenerate(schema)).toBe(readFileSync(GENERATED, "utf8"));
  });

  it("the check notices a schema change that was not regenerated", async () => {
    const schema = JSON.parse(readFileSync(SCHEMA, "utf8"));
    const [firstName] = Object.keys(schema.components.schemas);
    schema.components.schemas[`${firstName}Drifted`] = schema.components.schemas[firstName];

    expect(await regenerate(schema)).not.toBe(readFileSync(GENERATED, "utf8"));
  });
});
