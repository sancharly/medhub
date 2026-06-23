import { useContext } from "react";
import { ErrorToastContext } from "./context";

export function useErrorToast() {
  const ctx = useContext(ErrorToastContext);
  if (!ctx) throw new Error("useErrorToast must be used within ErrorToastProvider");
  return ctx.errorToast;
}
