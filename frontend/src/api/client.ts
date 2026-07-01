import { withCsrf } from "./csrf";
import type {
  LoginRequest,
  LoginResponse,
  MeResponse,
  ChangePasswordRequest,
  ExtendSessionResponse,
  ProblemError,
  PatientSummary,
  ClinicalEntry,
  CreateClinicalEntryRequest,
  Attachment,
  Appointment,
  CreateAppointmentRequest,
  ConsentGrant,
  AccountSummary,
  CreateAccountRequest,
  Group,
  InstalledModule,
  ActivationTokenStatus,
} from "./generated/types";

export type { ProblemError };

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export class AuthError extends Error {
  constructor(public readonly problem: ProblemError) {
    super(problem.title);
    this.name = "AuthError";
  }
}

export class ApiError extends Error {
  constructor(public readonly problem: ProblemError) {
    super(problem.title);
    this.name = "ApiError";
  }
}

export class ApiClient {
  private readonly baseUrl = "/api/v1";

  private async request<T>(
    method: string,
    path: string,
    body?: unknown
  ): Promise<T> {
    const headers: HeadersInit = {};
    if (body !== undefined) {
      (headers as Record<string, string>)["Content-Type"] = "application/json";
    }

    const finalHeaders = MUTATING_METHODS.has(method)
      ? withCsrf(headers)
      : new Headers(headers);

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      credentials: "include",
      headers: finalHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/problem+json")) {
        const problem: ProblemError = await response.json();
        if (
          response.status === 401 &&
          problem.type.endsWith("/errors/unauthenticated")
        ) {
          throw new AuthError(problem);
        }
        throw new ApiError(problem);
      }
      throw new ApiError({
        type: "/errors/unknown",
        title: response.statusText || "Unknown error",
        status: response.status,

      });
    }

    if (response.status === 204 || response.headers.get("content-length") === "0") {
      return undefined as unknown as T;
    }

    const text = await response.text();
    if (!text) return undefined as unknown as T;
    return JSON.parse(text) as T;
  }

  login(data: LoginRequest): Promise<LoginResponse> {
    return this.request<LoginResponse>("POST", "/auth/login", data);
  }

  me(): Promise<MeResponse> {
    return this.request<MeResponse>("GET", "/me");
  }

  changePassword(data: ChangePasswordRequest): Promise<void> {
    return this.request<void>("POST", "/auth/password", data);
  }

  extendSession(): Promise<ExtendSessionResponse> {
    return this.request<ExtendSessionResponse>("POST", "/auth/session/extend");
  }

  logout(): Promise<void> {
    return this.request<void>("POST", "/auth/logout");
  }

  getActivation(token: string): Promise<ActivationTokenStatus> {
    return this.request<ActivationTokenStatus>("GET", `/activation/${token}`);
  }

  activate(token: string, accountId: string, password: string, confirmPassword: string): Promise<void> {
    return this.request<void>("POST", `/activation/${token}`, { accountId, password, confirmPassword });
  }

  // Patients
  listPatients(): Promise<PatientSummary[]> {
    return this.request<PatientSummary[]>("GET", "/clinical-entries/patients");
  }

  // Clinical entries
  listClinicalEntries(patientId: string): Promise<ClinicalEntry[]> {
    return this.request<ClinicalEntry[]>("GET", `/patients/${patientId}/clinical-entries`);
  }

  createClinicalEntry(patientId: string, data: CreateClinicalEntryRequest): Promise<ClinicalEntry> {
    return this.request<ClinicalEntry>("POST", `/patients/${patientId}/clinical-entries`, data);
  }

  async uploadAttachment(entryId: string, file: File): Promise<Attachment> {
    const formData = new FormData();
    formData.append("file", file);
    const headers = withCsrf({});
    const response = await fetch(`${this.baseUrl}/clinical-entries/${entryId}/attachments`, {
      method: "POST",
      credentials: "include",
      headers,
      body: formData,
    });
    if (!response.ok) {
      const contentType = response.headers.get("content-type") ?? "";
      if (contentType.includes("application/problem+json")) {
        const problem: ProblemError = await response.json();
        throw new ApiError(problem);
      }
      throw new ApiError({
        type: "/errors/unknown",
        title: response.statusText || "Unknown error",
        status: response.status,

      });
    }
    return response.json() as Promise<Attachment>;
  }

  listAttachments(entryId: string): Promise<Attachment[]> {
    return this.request<Attachment[]>("GET", `/clinical-entries/${entryId}/attachments`);
  }

  getAttachmentUrl(attachmentId: string): string {
    return `${this.baseUrl}/attachments/${attachmentId}`;
  }

  listMyModules(): Promise<string[]> {
    return this.request<{ modules: string[] }>("GET", "/me/modules").then((r) => r.modules);
  }

  // Appointments
  listAppointments(): Promise<Appointment[]> {
    return this.request<Appointment[]>("GET", "/appointments");
  }

  createAppointment(data: CreateAppointmentRequest): Promise<Appointment> {
    return this.request<Appointment>("POST", "/appointments", data);
  }

  confirmAppointment(id: string): Promise<void> {
    return this.request<void>("POST", `/appointments/${id}/confirm`);
  }

  declineAppointment(id: string): Promise<void> {
    return this.request<void>("POST", `/appointments/${id}/decline`);
  }

  // Consents
  listMyConsents(): Promise<ConsentGrant[]> {
    return this.request<ConsentGrant[]>("GET", "/me/consents");
  }

  grantConsent(data: { doctorId: string }): Promise<ConsentGrant> {
    return this.request<ConsentGrant>("POST", "/consents", data);
  }

  revokeConsent(grantId: string): Promise<void> {
    return this.request<void>("DELETE", `/consents/${grantId}`);
  }

  // Accounts
  async listAccounts(): Promise<AccountSummary[]> {
    const response = await this.request<{ items: AccountSummary[] }>("GET", "/accounts");
    return response.items;
  }

  createAccount(data: CreateAccountRequest): Promise<AccountSummary> {
    return this.request<AccountSummary>("POST", "/accounts", data);
  }

  deactivateAccount(id: string): Promise<void> {
    return this.request<void>("POST", `/accounts/${id}/deactivate`);
  }

  reactivateAccount(id: string): Promise<void> {
    return this.request<void>("POST", `/accounts/${id}/reactivate`);
  }

  deleteAccount(id: string): Promise<void> {
    return this.request<void>("DELETE", `/accounts/${id}`);
  }

  resendActivation(id: string): Promise<void> {
    return this.request<void>("POST", `/accounts/${id}/resend-activation`);
  }

  // Groups
  listGroups(): Promise<Group[]> {
    return this.request<Group[]>("GET", "/groups");
  }

  createGroup(data: { name: string }): Promise<Group> {
    return this.request<Group>("POST", "/groups", data);
  }

  addGroupMember(groupId: string, accountId: string): Promise<void> {
    return this.request<void>("POST", `/groups/${groupId}/members`, { accountId });
  }

  removeGroupMember(groupId: string, accountId: string): Promise<void> {
    return this.request<void>("DELETE", `/groups/${groupId}/members/${accountId}`);
  }

  async listInstalledModules(): Promise<InstalledModule[]> {
    const response = await this.request<{ items: InstalledModule[] }>("GET", "/modules");
    return response.items;
  }

  setGroupModuleEnabled(groupId: string, moduleKey: string, enabled: boolean): Promise<void> {
    return this.request<void>("PUT", `/groups/${groupId}/modules/${moduleKey}`, { enabled });
  }
}
