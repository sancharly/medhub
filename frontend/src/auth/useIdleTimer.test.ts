import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIdleTimer } from "./useIdleTimer";

const minutes = (m: number) => m * 60 * 1000;

describe("useIdleTimer", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  function setup(deadlineMinutes?: number) {
    const onWarn = vi.fn();
    const onExpired = vi.fn();
    const hook = renderHook(
      ({ deadline }: { deadline?: number }) =>
        useIdleTimer({
          warningLeadMinutes: 2,
          onWarn,
          onExpired,
          deadlineOverride: deadline,
        }),
      {
        initialProps: {
          deadline:
            deadlineMinutes === undefined ? undefined : Date.now() + minutes(deadlineMinutes),
        },
      }
    );
    return { onWarn, onExpired, ...hook };
  }

  it("clinical role: warn fires at 13 min and expire at 15 min", () => {
    const { onWarn, onExpired } = setup(15);

    act(() => vi.advanceTimersByTime(minutes(13) - 1));
    expect(onWarn).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));
    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();

    act(() => vi.advanceTimersByTime(minutes(2)));
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("admin role: warn at 28 minutes (30 - 2)", () => {
    const { onWarn, onExpired } = setup(30);

    act(() => vi.advanceTimersByTime(minutes(28)));

    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("activity events do not move the deadline", () => {
    const { onWarn, onExpired } = setup(15);

    act(() => vi.advanceTimersByTime(minutes(10)));
    act(() => {
      window.dispatchEvent(new MouseEvent("mousemove"));
      window.dispatchEvent(new KeyboardEvent("keydown", { key: "a" }));
      window.dispatchEvent(new MouseEvent("click"));
      window.dispatchEvent(new Event("touchstart"));
      window.dispatchEvent(new Event("scroll"));
    });

    // 13 min after the deadline was set, not 23 min.
    act(() => vi.advanceTimersByTime(minutes(3)));
    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(minutes(2)));
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("no listeners registered for activity events", () => {
    const add = vi.spyOn(window, "addEventListener");
    setup(15);

    const events = ["mousemove", "keydown", "click", "touchstart", "scroll"];
    expect(add.mock.calls.filter(([type]) => events.includes(type))).toEqual([]);
  });

  it("a new deadline re-arms both timers", () => {
    const { onWarn, onExpired, rerender } = setup(15);

    act(() => vi.advanceTimersByTime(minutes(10)));
    rerender({ deadline: Date.now() + minutes(15) });

    act(() => vi.advanceTimersByTime(minutes(3)));
    expect(onWarn).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(minutes(10)));
    expect(onWarn).toHaveBeenCalledTimes(1);
    expect(onExpired).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(minutes(2)));
    expect(onExpired).toHaveBeenCalledTimes(1);
  });

  it("schedules nothing until a deadline is known", () => {
    const { onWarn, onExpired } = setup(undefined);

    act(() => vi.advanceTimersByTime(minutes(60)));

    expect(onWarn).not.toHaveBeenCalled();
    expect(onExpired).not.toHaveBeenCalled();
  });

  it("treats a deadline already in the past as expired", () => {
    const onWarn = vi.fn();
    const onExpired = vi.fn();

    renderHook(() =>
      useIdleTimer({
        warningLeadMinutes: 2,
        onWarn,
        onExpired,
        deadlineOverride: Date.now() - 1,
      })
    );

    expect(onExpired).toHaveBeenCalledTimes(1);
    expect(onWarn).not.toHaveBeenCalled();
  });
});
