export { ApiClient, ApiError, AuthError } from "./client";
export type { ProblemError } from "./client";
export { queryClient } from "./queryClient";
export { QueryProvider } from "./QueryProvider";

import { ApiClient } from "./client";
export const apiClient = new ApiClient();
