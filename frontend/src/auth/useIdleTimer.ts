import { useEffect, useRef, useCallback } from "react";

const ACTIVITY_EVENTS = [
  "mousemove",
  "keydown",
  "click",
  "touchstart",
  "scroll",
] as const;

interface UseIdleTimerOptions {
  timeoutMinutes: number;
  warningLeadMinutes: number;
  onWarn: () => void;
  onExpired: () => void;
  deadlineOverride?: number;
}

export function useIdleTimer({
  timeoutMinutes,
  warningLeadMinutes,
  onWarn,
  onExpired,
  deadlineOverride,
}: UseIdleTimerOptions) {
  const warnTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const expireTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const deadlineRef = useRef<number>(Date.now() + timeoutMinutes * 60 * 1000);

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
    const newDeadline = Date.now() + timeoutMinutes * 60 * 1000;
    deadlineRef.current = newDeadline;
    scheduleTimers(newDeadline);
  }, [timeoutMinutes, scheduleTimers]);

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
