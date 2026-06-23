import { useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api";

export function useActivate(token: string) {
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (password: string) => apiClient.activate(token, password),
    onSuccess: () => {
      navigate("/login?activated=1");
    },
  });
}
