import { createContext } from "react";
import type { ConfirmDialogOptions } from "./ConfirmDialog";

interface ConfirmContextValue {
  confirm: (options: ConfirmDialogOptions) => Promise<boolean>;
}

export const ConfirmContext = createContext<ConfirmContextValue | null>(null);
