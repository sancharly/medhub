export type UserType = "patient" | "doctor" | "admin" | "sysadmin";

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: MeResponse;
  mustChangePassword: boolean;
  evictedSession: boolean;
}

export interface MeResponse {
  id: string;
  email: string;
  userType: UserType;
  mustChangePassword: boolean;
}

export interface ChangePasswordRequest {
  currentPassword: string;
  newPassword: string;
}

export interface ExtendSessionResponse {
  expiresAt: string;
}

export interface ActivateRequest {
  token: string;
  password: string;
}

export interface ProblemError {
  type: string;
  title: string;
  status: number;
  detail?: string;
  errors?: Array<{ field: string; message: string }>;
}
