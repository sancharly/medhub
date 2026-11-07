import type { UserType } from "../../api/generated/types";

/**
 * Single source of truth for which roles may use which route (TASK-142,
 * PRB-014). Navigation (`navConfig.ts`) and the route guard (`RequireRole`)
 * both read this table. The server stays the control (SR-005, SR-009); this
 * is defence in depth. Every `<Route>` in `App.tsx` must have an entry.
 */
export const routeRoles = {
  "/password": ["PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"],
  "/profile": ["PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"],
  "/patients": ["DOCTOR"],
  "/patients/:patientId/clinical-entries": ["DOCTOR", "PATIENT"],
  "/appointments": ["PATIENT", "DOCTOR", "ADMIN", "SYSADMIN"],
  "/consent": ["PATIENT"],
  "/admin/accounts": ["ADMIN", "SYSADMIN"],
  "/admin/groups": ["SYSADMIN"],
} as const satisfies Record<string, readonly UserType[]>;

export type RoutePath = keyof typeof routeRoles;
