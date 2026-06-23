import type { UserType } from "../../api/generated/openapi";

export type { UserType };

export interface NavItem {
  label: string;
  path: string;
  icon?: React.ReactNode;
}

export interface NavEntry extends NavItem {
  roles: UserType[];
}
