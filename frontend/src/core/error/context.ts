import { createContext } from "react";
import type { ProblemError } from "../../api/generated/types";

interface ErrorToastContextValue {
  errorToast: (error: ProblemError | Error) => void;
}

export const ErrorToastContext = createContext<ErrorToastContextValue | null>(
  null
);
