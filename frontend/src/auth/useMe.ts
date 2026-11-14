import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import { queryKeys } from "../api/queryKeys";

/**
 * The one reader of the signed-in user (SR-030 AC 8, PRB-016). No retries: a failed session
 * check is not repeated, so an expired session gives one 401 and one redirect, not three.
 * `staleTime` stops each mounting component from re-requesting it.
 */
export function useMe() {
  return useQuery({
    queryKey: queryKeys.me,
    queryFn: () => apiClient.me(),
    retry: false,
    staleTime: 30_000,
  });
}
