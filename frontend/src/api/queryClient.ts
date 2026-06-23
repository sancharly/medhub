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
