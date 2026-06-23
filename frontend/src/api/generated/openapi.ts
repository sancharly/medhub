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
  firstName?: string;
  surname?: string;
}

export interface PatientSummary {
  id: string;
  firstName: string;
  surname: string;
  dateOfBirth?: string;
}

export interface ClinicalEntry {
  id: string;
  patientId: string;
  authorName: string;
  occurredAt: string;
  description: string;
  attachments: Attachment[];
}

export interface CreateClinicalEntryRequest {
  occurredAt: string;
  description: string;
  // NO author field — SR-012 AC-3
}

export interface Attachment {
  id: string;
  filename: string;
  contentType: string;
}

export interface UserModule {
  moduleKey: string;
  enabled: boolean;
}

export type AppointmentStatus = "PENDING" | "CONFIRMED" | "DECLINED";

export interface Appointment {
  id: string;
  doctorId: string;
  doctorName: string;
  patientId: string;
  patientName: string;
  scheduledAt: string;
  status: AppointmentStatus;
}

export interface CreateAppointmentRequest {
  doctorId: string;
  patientId: string;
  scheduledAt: string;
}

export type ConsentSource = "MANUAL" | `APPOINTMENT:${string}`;

export interface ConsentGrant {
  id: string;
  doctorId: string;
  doctorName: string;
  source: string; // 'MANUAL' or 'APPOINTMENT:{id}'
  grantedAt: string;
}

export type AccountState = "INACTIVE" | "ACTIVE" | "DELETED";

export interface AccountSummary {
  id: string;
  firstName: string;
  surname: string;
  email: string;
  userType: UserType;
  state: AccountState;
  dateOfBirth?: string;
}

export interface CreateAccountRequest {
  firstName: string;
  surname: string;
  email: string;
  userType: UserType;
}

export type MembershipSource = "AUTO" | "MANUAL";

export interface GroupMember {
  accountId: string;
  name: string;
  membershipSource: MembershipSource;
}

export interface Group {
  id: string;
  name: string;
  members: GroupMember[];
  enabledModules: string[];
}

export interface InstalledModule {
  moduleKey: string;
  name: string;
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
