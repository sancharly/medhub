import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api";
import { queryClient } from "../api/queryClient";
import type { LoginRequest, LoginResponse } from "../api/generated/types";

export function useLogin() {
  return useMutation<LoginResponse, Error, LoginRequest>({
    mutationFn: (data) => apiClient.login(data),
    onSuccess: (data) => {
      queryClient.setQueryData(["me"], data.user);
    },
  });
}
