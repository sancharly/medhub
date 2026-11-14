import { useState, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api";
import { queryClient as qc, setAuthExpiredHandler } from "../api/queryClient";
import { useMe } from "./useMe";
import { useIdleTimer } from "./useIdleTimer";
import { IdleWarningDialog } from "./IdleWarningDialog";
import { roleTimeouts } from "./roleTimeouts";

export function SessionActivityProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const navigate = useNavigate();
  const [showWarning, setShowWarning] = useState(false);
  const [extension, setExtension] = useState<
    { receivedAt: number; deadline: number } | undefined
  >();

  const { data: me, dataUpdatedAt } = useMe();

  // The deadline is the time the server's relative expiry was received plus that expiry, so the
  // client clock and a client constant play no part (SR-030 AC 8). The newest of the `me`
  // response and the last extend response wins.
  const reported = me?.sessionExpiresInSeconds;
  const meDeadline =
    typeof reported === "number" ? dataUpdatedAt + reported * 1000 : undefined;
  const deadline =
    extension && extension.receivedAt >= dataUpdatedAt
      ? extension.deadline
      : meDeadline;

  const handleWarn = useCallback(() => {
    setShowWarning(true);
  }, []);

  const handleExpired = useCallback(() => {
    setShowWarning(false);
    navigate("/login?timeout=1");
  }, [navigate]);

  // A 401 on any mutation (the attachment upload included) ends the session once.
  useEffect(
    () =>
      setAuthExpiredHandler(() => {
        setShowWarning(false);
        navigate("/login?timeout=1");
        qc.clear();
      }),
    [navigate]
  );

  useIdleTimer({
    timeoutSeconds: reported ?? 0,
    warningLeadMinutes: roleTimeouts.warningLeadMinutes,
    onWarn: handleWarn,
    onExpired: handleExpired,
    deadlineOverride: deadline,
  });

  function handleExtended(newDeadline: number) {
    setShowWarning(false);
    setExtension({ receivedAt: Date.now(), deadline: newDeadline });
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
        expiresAt={deadline ?? 0}
        onExtended={handleExtended}
        onLogout={handleLogout}
      />
    </>
  );
}
