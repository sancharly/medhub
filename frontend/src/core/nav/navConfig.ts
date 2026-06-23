import type { NavEntry } from "./types";

export const navConfig: NavEntry[] = [
  {
    label: "Profile",
    path: "/profile",
    roles: ["patient", "doctor", "admin", "sysadmin"],
  },
  {
    label: "Appointments",
    path: "/appointments",
    roles: ["patient", "doctor"],
  },
  {
    label: "Consent",
    path: "/consent",
    roles: ["patient"],
  },
  {
    label: "Patients",
    path: "/patients",
    roles: ["doctor"],
  },
  {
    label: "Accounts",
    path: "/admin/accounts",
    roles: ["admin", "sysadmin"],
  },
  {
    label: "Groups",
    path: "/admin/groups",
    roles: ["sysadmin"],
  },
];
