import { useEffect } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import { AuthError } from "../api/client";

export function RequireAuth() {
  const navigate = useNavigate();
  const location = useLocation();

  const { error, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
    retry: false,
  });

  useEffect(() => {
    if (error instanceof AuthError) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`, {
        replace: true,
      });
    }
  }, [error, navigate, location.pathname]);

  if (isLoading) return null;
  if (error instanceof AuthError) return null;

  return <Outlet />;
}
