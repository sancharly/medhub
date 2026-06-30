import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { apiClient } from "../api";

export function ForcedPasswordGate() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  const mustChangePassword = me?.mustChangePassword ?? false;

  useEffect(() => {
    if (mustChangePassword && location.pathname !== "/password") {
      navigate("/password", { replace: true });
    }
  }, [mustChangePassword, navigate, location.pathname]);

  if (mustChangePassword && location.pathname !== "/password") {
    return null;
  }

  return <Outlet />;
}
