import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api";
import { queryClient } from "../api/queryClient";
import { queryKeys } from "../api/queryKeys";
import type { LoginRequest, LoginResponse } from "../api/generated/types";

export function useLogin() {
  return useMutation<LoginResponse, Error, LoginRequest>({
    mutationFn: (data) => apiClient.login(data),
    // The login response does not report the session expiry, and a failed `me` from a previous
    // session must not stay cached: drop it so the next reader fetches the full `me` (SR-030 AC 8).
    onSuccess: () => {
      queryClient.resetQueries({ queryKey: queryKeys.me, exact: true });
    },
  });
}
