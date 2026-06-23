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
    label: "Clinical Notes",
    path: "/clinical-notes",
    roles: ["doctor"],
  },
  {
    label: "Users",
    path: "/admin/users",
    roles: ["admin", "sysadmin"],
  },
  {
    label: "Audit Log",
    path: "/admin/audit",
    roles: ["admin", "sysadmin"],
  },
  {
    label: "System",
    path: "/admin/system",
    roles: ["sysadmin"],
  },
];
