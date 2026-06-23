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

  useEffect(() => {
    if (me?.mustChangePassword && location.pathname !== "/password") {
      navigate("/password", { replace: true });
    }
  }, [me, navigate, location.pathname]);

  if (me?.mustChangePassword && location.pathname !== "/password") {
    return null;
  }

  return <Outlet />;
}
