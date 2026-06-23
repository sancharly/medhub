import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNavItems } from "./useNavItems";
import { navConfig } from "./navConfig";

describe("useNavItems", () => {
  it("returns patient entries for patient role", () => {
    const { result } = renderHook(() => useNavItems("patient"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Profile");
    expect(labels).toContain("Appointments");
    expect(labels).toContain("Consent");
  });

  it("patient does not see admin entries", () => {
    const { result } = renderHook(() => useNavItems("patient"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).not.toContain("Users");
    expect(labels).not.toContain("Audit Log");
    expect(labels).not.toContain("System");
  });

  it("sysadmin sees admin entries", () => {
    const { result } = renderHook(() => useNavItems("sysadmin"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Users");
    expect(labels).toContain("Audit Log");
    expect(labels).toContain("System");
  });

  it("labels come from navConfig", () => {
    const { result } = renderHook(() => useNavItems("doctor"));
    const configLabels = navConfig
      .filter((e) => e.roles.includes("doctor"))
      .map((e) => e.label);
    const hookLabels = result.current.items.map((i) => i.label);
    configLabels.forEach((l) => expect(hookLabels).toContain(l));
  });

  it("appendItems adds extra items", () => {
    const { result } = renderHook(() => useNavItems("patient"));
    act(() => {
      result.current.appendItems([{ label: "Extra", path: "/extra" }]);
    });
    expect(result.current.items.map((i) => i.label)).toContain("Extra");
  });

  it("admin sees admin entries but not sysadmin-only entries", () => {
    const { result } = renderHook(() => useNavItems("admin"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Users");
    expect(labels).not.toContain("System");
  });
});
