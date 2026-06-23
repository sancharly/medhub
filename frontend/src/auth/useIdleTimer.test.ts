import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIdleTimer } from "./useIdleTimer";

describe("useIdleTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fires onWarn after timeout - warningLead minutes", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        timeoutMinutes: 15,
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
      })
    );

    act(() => {
      vi.advanceTimersByTime(13 * 60 * 1000);
    });

    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("fires onExpired after full timeout minutes", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        timeoutMinutes: 15,
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
      })
    );

    act(() => {
      vi.advanceTimersByTime(15 * 60 * 1000);
    });

    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("admin role: warn at 28 minutes (30 - 2)", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        timeoutMinutes: 30,
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
      })
    );

    act(() => {
      vi.advanceTimersByTime(28 * 60 * 1000);
    });

    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("activity before warn resets deadline", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        timeoutMinutes: 15,
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
      })
    );

    act(() => {
      vi.advanceTimersByTime(12 * 60 * 1000);
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
      vi.advanceTimersByTime(5 * 60 * 1000);
    });

    expect(onWarn).not.toHaveBeenCalled();
  });

  it("clinical role: warn fires at 13 min and expire at 15 min", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        timeoutMinutes: 15,
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
      })
    );

    act(() => vi.advanceTimersByTime(13 * 60 * 1000));
    expect(onWarn).toHaveBeenCalledTimes(1);

    act(() => vi.advanceTimersByTime(2 * 60 * 1000));
    expect(onExpired).toHaveBeenCalledTimes(1);
  });
});
