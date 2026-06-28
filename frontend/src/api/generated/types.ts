/**
 * Named type aliases extracted from the auto-generated OpenAPI schema.
 * Import from this file, not from openapi.ts directly.
 * Re-generate with: npm run generate:types
 */
import type { components } from "./openapi";

export type UserType = components["schemas"]["UserType"];
export type AccountStatus = components["schemas"]["AccountStatus"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type LoginResponse = components["schemas"]["LoginResponse"];
export type MeResponse = components["schemas"]["MeResponse"];
export type MeSummary = components["schemas"]["MeSummary"];
export type ChangePasswordRequest = components["schemas"]["PasswordChangeRequest"];
export type ExtendSessionResponse = components["schemas"]["SessionExtendResponse"];
// Override: detail is optional (synthetic errors omit it), errors have known shape
export type ProblemError = {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: Array<{ field?: string; rule?: string; message?: string }>;
};
export type ClinicalEntry = components["schemas"]["ClinicalEntryResponse"];
export type CreateClinicalEntryRequest = components["schemas"]["ClinicalEntryCreate"];
export type Attachment = components["schemas"]["AttachmentResponse"];
export type Appointment = components["schemas"]["AppointmentResponse"];
export type CreateAppointmentRequest = components["schemas"]["AppointmentCreate"];
export type ConsentGrant = components["schemas"]["ConsentGrantResponse"];
export type AccountSummary = components["schemas"]["AccountResponse"];
export type CreateAccountRequest = components["schemas"]["AccountCreateRequest"];
export type Group = components["schemas"]["GroupResponse"];
export type InstalledModule = components["schemas"]["ModuleResponse"];
export type GroupMember = components["schemas"]["GroupMemberResponse"];
// PatientSummary shares the same shape as AccountResponse (patients are accounts)
export type PatientSummary = components["schemas"]["AccountResponse"];
