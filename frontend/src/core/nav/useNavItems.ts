import { useState, useCallback } from "react";
import { navConfig } from "./navConfig";
import type { NavItem, NavEntry, UserType } from "./types";

export function useNavItems(userType: UserType) {
  const [extra, setExtra] = useState<NavItem[]>([]);

  const appendItems = useCallback((items: NavItem[]) => {
    setExtra((prev) => [...prev, ...items]);
  }, []);

  const filtered: NavItem[] = (navConfig as NavEntry[])
    .filter((entry) => entry.roles.includes(userType))
    .map(({ label, path, icon }) => ({ label, path, icon }));

  return { items: [...filtered, ...extra], appendItems };
}
