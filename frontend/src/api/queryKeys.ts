/** Query keys that more than one file needs. `me` is read only through `useMe` (SR-030 AC 8). */
export const queryKeys = {
  me: ["me"] as const,
  myConsents: ["me", "consents"] as const,
};
