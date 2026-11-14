import { useEffect, useRef, useCallback } from "react";

interface UseIdleTimerOptions {
  warningLeadMinutes: number;
  onWarn: () => void;
  onExpired: () => void;
  /**
   * Deadline (ms) derived from a server response (SR-030 AC 8); no timers run until it is known.
   * Nothing else re-arms the timers: user input is not tracked (PRB-087).
   */
  deadlineOverride?: number;
}

export function useIdleTimer({
  warningLeadMinutes,
  onWarn,
  onExpired,
  deadlineOverride,
}: UseIdleTimerOptions) {
  const warnTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const expireTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const clearTimers = useCallback(() => {
    if (warnTimerRef.current) clearTimeout(warnTimerRef.current);
    if (expireTimerRef.current) clearTimeout(expireTimerRef.current);
  }, []);

  useEffect(() => {
    if (deadlineOverride === undefined) return;

    const expireIn = deadlineOverride - Date.now();
    const warnIn = expireIn - warningLeadMinutes * 60 * 1000;

    // A deadline that has already passed is an ended session, not a timer that never starts.
    if (expireIn <= 0) {
      onExpired();
      return;
    }

    if (warnIn > 0) {
      warnTimerRef.current = setTimeout(onWarn, warnIn);
    }
    expireTimerRef.current = setTimeout(onExpired, expireIn);

    return clearTimers;
  }, [deadlineOverride, warningLeadMinutes, onWarn, onExpired, clearTimers]);
}
