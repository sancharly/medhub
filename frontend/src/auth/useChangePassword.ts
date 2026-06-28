import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api";
import { ApiError } from "../api/client";
import type { ChangePasswordRequest } from "../api/generated/types";

export interface ChangePasswordError {
  field?: string;
  message: string;
}

export function useChangePassword() {
  return useMutation<void, Error, ChangePasswordRequest>({
    mutationFn: (data) => apiClient.changePassword(data),
    throwOnError: false,
  });
}

export function extractChangePasswordError(
  error: Error | null
): ChangePasswordError | null {
  if (!error) return null;
  if (error instanceof ApiError) {
    if (error.problem.errors?.length) {
      const first = error.problem.errors[0];
      return { field: first.field, message: first.message ?? "" };
    }
    return { message: error.problem.detail ?? error.problem.title };
  }
  return { message: error.message };
}
