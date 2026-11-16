// The inactivity timeout itself comes from the server (`sessionExpiresInSeconds`, SR-030 AC 8);
// only the warning lead (SR-030 AC 4) is a client value.
export const roleTimeouts = {
  warningLeadMinutes: 2,
} as const;
