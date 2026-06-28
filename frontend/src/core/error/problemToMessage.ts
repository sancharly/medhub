import type { ProblemError } from "../../api/generated/types";

export interface MappedError {
  summary: string;
  fieldErrors?: Array<{ field: string; message: string }>;
}

export function problemToMessage(problem: ProblemError): MappedError {
  const summary = problem.detail || problem.title;
  const result: MappedError = { summary };
  if (problem.errors && problem.errors.length > 0) {
    result.fieldErrors = problem.errors as Array<{ field: string; message: string }>;
  }
  return result;
}
