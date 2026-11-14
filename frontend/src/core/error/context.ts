import { createContext } from "react";
import type { ProblemError } from "../../api/problem";

interface ErrorToastContextValue {
  errorToast: (error: ProblemError | Error) => void;
}

export const ErrorToastContext = createContext<ErrorToastContextValue | null>(
  null
);
