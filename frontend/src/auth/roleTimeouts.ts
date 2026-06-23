import type { UserType } from "../api/generated/openapi";

export const roleTimeouts = {
  clinical: 15,
  admin: 30,
  warningLeadMinutes: 2,
} as const;

export function getTimeoutMinutes(userType: UserType): number {
  if (userType === "doctor" || userType === "patient") {
    return roleTimeouts.clinical;
  }
  return roleTimeouts.admin;
}
