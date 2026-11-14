import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import { queryKeys } from "../api/queryKeys";

/**
 * The one reader of the signed-in user's enabled modules (SR-015 AC 5, PRB-015). A change made by
 * an administrator reaches this user within 60 s (`refetchInterval` of 50 s: the interval restarts when a response arrives, so 10 s remain for the round trip and one retry of 1 s), on window focus, or on the
 * next mount of a module-dependent view (`refetchOnMount: "always"`). A failed refetch keeps the
 * last known list (TanStack Query keeps `data` on error), so an enabled module is never hidden by a
 * transient failure (RISK-004); the server guard stays the authority (SR-015 AC 3).
 */
export function useMyModules() {
  return useQuery({
    queryKey: queryKeys.myModules,
    queryFn: () => apiClient.listMyModules(),
    staleTime: 30_000,
    refetchInterval: 50_000,
    refetchOnWindowFocus: true,
    refetchOnMount: "always",
    retry: 1,
  });
}
