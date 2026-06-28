import type { NavEntry } from "./types";

export const navConfig: NavEntry[] = [
  {
    label: "Profile",
    path: "/profile",
    roles: ["PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"],
  },
  {
    label: "Appointments",
    path: "/appointments",
    roles: ["PATIENT", "DOCTOR"],
  },
  {
    label: "Consent",
    path: "/consent",
    roles: ["PATIENT"],
  },
  {
    label: "Patients",
    path: "/patients",
    roles: ["DOCTOR"],
  },
  {
    label: "Accounts",
    path: "/admin/accounts",
    roles: ["ADMIN", "SYSADMIN"],
  },
  {
    label: "Groups",
    path: "/admin/groups",
    roles: ["SYSADMIN"],
  },
];
