import { useEffect, useRef, useCallback } from "react";

const ACTIVITY_EVENTS = [
  "mousemove",
  "keydown",
  "click",
  "touchstart",
  "scroll",
] as const;

interface UseIdleTimerOptions {
  /** Length of the session as last reported by the server; activity re-arms to this. */
  timeoutSeconds: number;
  warningLeadMinutes: number;
  onWarn: () => void;
  onExpired: () => void;
  /** Deadline (ms) derived from the server-reported expiry; no timers run until it is known. */
  deadlineOverride?: number;
}

export function useIdleTimer({
  timeoutSeconds,
  warningLeadMinutes,
  onWarn,
  onExpired,
  deadlineOverride,
}: UseIdleTimerOptions) {
  const warnTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const expireTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const deadlineRef = useRef<number>(Date.now() + timeoutSeconds * 1000);

  const clearTimers = useCallback(() => {
    if (warnTimerRef.current) clearTimeout(warnTimerRef.current);
    if (expireTimerRef.current) clearTimeout(expireTimerRef.current);
  }, []);

  const scheduleTimers = useCallback(
    (fromDeadline: number) => {
      clearTimers();
      const now = Date.now();
      const expireIn = fromDeadline - now;
      const warnIn = expireIn - warningLeadMinutes * 60 * 1000;

      // A deadline that has already passed is an ended session, not a timer that never starts.
      if (expireIn <= 0) {
        onExpired();
        return;
      }

      if (warnIn > 0) {
        warnTimerRef.current = setTimeout(onWarn, warnIn);
      }
      if (expireIn > 0) {
        expireTimerRef.current = setTimeout(onExpired, expireIn);
      }
    },
    [clearTimers, onWarn, onExpired, warningLeadMinutes]
  );

  const resetDeadline = useCallback(() => {
    // No server-reported length yet: nothing to re-arm to.
    if (!(timeoutSeconds > 0)) return;
    const newDeadline = Date.now() + timeoutSeconds * 1000;
    deadlineRef.current = newDeadline;
    scheduleTimers(newDeadline);
  }, [timeoutSeconds, scheduleTimers]);

  useEffect(() => {
    if (deadlineOverride !== undefined) {
      deadlineRef.current = deadlineOverride;
      scheduleTimers(deadlineOverride);
    } else {
      resetDeadline();
    }

    ACTIVITY_EVENTS.forEach((event) =>
      window.addEventListener(event, resetDeadline, { passive: true })
    );

    return () => {
      clearTimers();
      ACTIVITY_EVENTS.forEach((event) =>
        window.removeEventListener(event, resetDeadline)
      );
    };
  }, [deadlineOverride, resetDeadline, scheduleTimers, clearTimers]);

  return { resetDeadline };
}
