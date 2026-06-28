import type { UserType } from "../api/generated/types";

export const roleTimeouts = {
  clinical: 15,
  admin: 30,
  warningLeadMinutes: 2,
} as const;

export function getTimeoutMinutes(userType: UserType): number {
  if (userType === "DOCTOR" || userType === "PATIENT") {
    return roleTimeouts.clinical;
  }
  return roleTimeouts.admin;
}
