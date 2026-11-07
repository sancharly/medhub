import type { NavEntry } from "./types";
import { routeRoles, type RoutePath } from "./routeRoles";

function entry(label: string, path: RoutePath): NavEntry {
  return { label, path, roles: [...routeRoles[path]] };
}

export const navConfig: NavEntry[] = [
  entry("Profile", "/profile"),
  entry("Appointments", "/appointments"),
  entry("Consent", "/consent"),
  entry("Patients", "/patients"),
  entry("Accounts", "/admin/accounts"),
  entry("Groups", "/admin/groups"),
];
