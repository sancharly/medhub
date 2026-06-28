import { describe, it, expect } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useNavItems } from "./useNavItems";
import { navConfig } from "./navConfig";

describe("useNavItems", () => {
  it("returns patient entries for patient role", () => {
    const { result } = renderHook(() => useNavItems("PATIENT"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Profile");
    expect(labels).toContain("Appointments");
    expect(labels).toContain("Consent");
  });

  it("patient does not see admin entries", () => {
    const { result } = renderHook(() => useNavItems("PATIENT"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).not.toContain("Accounts");
    expect(labels).not.toContain("Groups");
  });

  it("sysadmin sees admin entries", () => {
    const { result } = renderHook(() => useNavItems("SYSADMIN"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Accounts");
    expect(labels).toContain("Groups");
  });

  it("labels come from navConfig", () => {
    const { result } = renderHook(() => useNavItems("DOCTOR"));
    const configLabels = navConfig
      .filter((e) => e.roles.includes("DOCTOR"))
      .map((e) => e.label);
    const hookLabels = result.current.items.map((i) => i.label);
    configLabels.forEach((l) => expect(hookLabels).toContain(l));
  });

  it("appendItems adds extra items", () => {
    const { result } = renderHook(() => useNavItems("PATIENT"));
    act(() => {
      result.current.appendItems([{ label: "Extra", path: "/extra" }]);
    });
    expect(result.current.items.map((i) => i.label)).toContain("Extra");
  });

  it("admin sees Accounts but not Groups (sysadmin-only)", () => {
    const { result } = renderHook(() => useNavItems("ADMIN"));
    const labels = result.current.items.map((i) => i.label);
    expect(labels).toContain("Accounts");
    expect(labels).not.toContain("Groups");
  });
});
