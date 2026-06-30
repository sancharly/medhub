import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api";

export function useActivate(token: string) {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: ({ accountId, password, confirmPassword }: { accountId: string; password: string; confirmPassword: string }) =>
      apiClient.activate(token, accountId, password, confirmPassword),
    onSuccess: () => {
      navigate("/login?activated=1");
    },
  });
}
