import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import { queryClient as qc } from "../api/queryClient";
import { useIdleTimer } from "./useIdleTimer";
import { IdleWarningDialog } from "./IdleWarningDialog";
import { getTimeoutMinutes } from "./roleTimeouts";
import { roleTimeouts } from "./roleTimeouts";

export function SessionActivityProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const navigate = useNavigate();
  const [showWarning, setShowWarning] = useState(false);
  const [expiresAt, setExpiresAt] = useState(
    () => Date.now() + 15 * 60 * 1000
  );
  const [deadlineOverride, setDeadlineOverride] = useState<
    number | undefined
  >();

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  const timeoutMinutes = me ? getTimeoutMinutes(me.userType) : 15;

  const handleWarn = useCallback(() => {
    const deadline = Date.now() + roleTimeouts.warningLeadMinutes * 60 * 1000;
    setExpiresAt(deadline);
    setShowWarning(true);
  }, []);

  const handleExpired = useCallback(() => {
    setShowWarning(false);
    navigate("/login?timeout=1");
  }, [navigate]);

  const { resetDeadline } = useIdleTimer({
    timeoutMinutes,
    warningLeadMinutes: roleTimeouts.warningLeadMinutes,
    onWarn: handleWarn,
    onExpired: handleExpired,
    deadlineOverride,
  });

  function handleExtended(newDeadline: number) {
    setShowWarning(false);
    setDeadlineOverride(newDeadline);
    resetDeadline();
  }

  async function handleLogout() {
    try {
      await apiClient.logout();
    } catch {
      // ignore
    }
    qc.clear();
    navigate("/login");
  }

  return (
    <>
      {children}
      <IdleWarningDialog
        open={showWarning}
        expiresAt={expiresAt}
        onExtended={handleExtended}
        onLogout={handleLogout}
      />
    </>
  );
}
