import { Navigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import type { UserType } from "../api/generated/types";

interface RequireRoleProps {
  roles: readonly UserType[];
  children: React.ReactNode;
}

/**
 * Route-level role guard (TASK-142, PRB-014). Mounts the child only when the
 * signed-in user's role is listed. Renders nothing while `me` loads or if it
 * failed (deny by default); an unauthenticated user is sent to login by
 * `RequireAuth`, which wraps this guard.
 */
export function RequireRole({ roles, children }: RequireRoleProps) {
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  if (!me) return null;
  if (!roles.includes(me.userType)) return <Navigate to="/profile" replace />;
  return <>{children}</>;
}
