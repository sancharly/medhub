import { useCallback, useState } from "react";
import Snackbar from "@mui/material/Snackbar";
import Alert from "@mui/material/Alert";
import { problemToMessage } from "./problemToMessage";
import { AuthError } from "../../api/client";
import { ErrorToastContext } from "./context";
import type { ProblemError } from "../../api/generated/openapi";

export function ErrorToastProvider({ children }: { children: React.ReactNode }) {
  const [message, setMessage] = useState<string | null>(null);

  const errorToast = useCallback((error: ProblemError | Error) => {
    // 401 unauthenticated is handled by RequireAuth, not toasted
    if (error instanceof AuthError) return;

    let summary: string;
    if ("type" in error && "title" in error && "status" in error) {
      summary = problemToMessage(error as ProblemError).summary;
    } else {
      summary = (error as Error).message || "An unexpected error occurred";
    }
    setMessage(summary);
  }, []);

  return (
    <ErrorToastContext.Provider value={{ errorToast }}>
      {children}
      <Snackbar
        open={message !== null}
        autoHideDuration={6000}
        onClose={() => setMessage(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity="error"
          onClose={() => setMessage(null)}
          sx={{ width: "100%" }}
        >
          {message}
        </Alert>
      </Snackbar>
    </ErrorToastContext.Provider>
  );
}
