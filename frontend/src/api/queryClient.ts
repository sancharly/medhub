import { QueryClient } from "@tanstack/react-query";

export const queryClient = new QueryClient({
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

// PRB-067: an errored `["me"]` query must not be refetched by every observer
// that mounts. With no data, a refetch resets it to `pending`, `RequireAuth`
// unmounts the tree, and the remount refetches again (tight request loop).
queryClient.setQueryDefaults(["me"], { retryOnMount: false });
// `setQueryDefaults` matches by key prefix; the consent list shares the prefix
// but must keep retrying on mount.
queryClient.setQueryDefaults(["me", "consents"], { retryOnMount: true });
