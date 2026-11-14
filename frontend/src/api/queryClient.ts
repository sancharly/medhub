import { MutationCache, QueryClient } from "@tanstack/react-query";
import { AuthError } from "./client";
import { queryKeys } from "./queryKeys";

// A 401 on a mutation (the attachment upload included) ends the session: the handler registered
// by `SessionActivityProvider` clears the cache and redirects. Concurrent failures fire it once;
// registering a handler (a new signed-in session) re-arms it.
let authExpiredHandler: (() => void) | null = null;
let authExpiredFired = false;

export function setAuthExpiredHandler(handler: () => void): () => void {
  authExpiredHandler = handler;
  authExpiredFired = false;
  return () => {
    if (authExpiredHandler === handler) authExpiredHandler = null;
  };
}

function onMutationError(error: unknown) {
  if (error instanceof AuthError && authExpiredHandler && !authExpiredFired) {
    authExpiredFired = true;
    authExpiredHandler();
  }
}

export const queryClient = new QueryClient({
  mutationCache: new MutationCache({ onError: onMutationError }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (
          error &&
          typeof error === "object" &&
          "problem" in error &&
          typeof (error as { problem: { status: number } }).problem
            .status === "number"
        ) {
          const status = (error as { problem: { status: number } }).problem
            .status;
          if (status >= 400 && status < 500) return false;
        }
        return failureCount < 3;
      },
    },
  },
});

// PRB-067: an errored `me` query must not be refetched by every observer
// that mounts. With no data, a refetch resets it to `pending`, `RequireAuth`
// unmounts the tree, and the remount refetches again (tight request loop).
queryClient.setQueryDefaults(queryKeys.me, { retryOnMount: false });
// `setQueryDefaults` matches by key prefix; the consent list shares the prefix
// but must keep retrying on mount.
queryClient.setQueryDefaults(queryKeys.myConsents, { retryOnMount: true });
