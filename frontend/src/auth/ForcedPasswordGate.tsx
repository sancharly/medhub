import { useNavigate, useLocation, Outlet } from "react-router-dom";
import { useEffect } from "react";
import { useMe } from "./useMe";

export function ForcedPasswordGate() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: me } = useMe();

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
