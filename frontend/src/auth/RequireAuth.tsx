import { useEffect } from "react";
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import { apiClient } from "../api";
import { AuthError } from "../api/client";

export function RequireAuth() {
  const navigate = useNavigate();
  const location = useLocation();

  const { data, error, isLoading, refetch } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
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

  // PRB-067: other errors (5xx after the client-wide retries) must not leave a
  // blank screen; offer a way to recover (SR-027 AC 3).
  // A failed background refetch of an already-loaded `/me` keeps the app mounted.
  if (error && !data) {
    return (
      <Alert
        severity="error"
        role="alert"
        action={
          <Button color="inherit" size="small" onClick={() => void refetch()}>
            Try again
          </Button>
        }
      >
        Could not load your account. Check your connection and try again.
      </Alert>
    );
  }

  return <Outlet />;
}
