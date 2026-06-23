import { useCallback, useRef, useState } from "react";
import { ConfirmDialog } from "./ConfirmDialog";
import { ConfirmContext } from "./context";
import type { ConfirmDialogOptions } from "./ConfirmDialog";

interface DialogState extends ConfirmDialogOptions {
  open: boolean;
}

const CLOSED: DialogState = {
  open: false,
  title: "",
  description: "",
};

export function ConfirmProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DialogState>(CLOSED);
  const resolverRef = useRef<((value: boolean) => void) | null>(null);

  const confirm = useCallback(
    (options: ConfirmDialogOptions): Promise<boolean> => {
      setState({ ...options, open: true });
      return new Promise<boolean>((resolve) => {
        resolverRef.current = resolve;
      });
    },
    []
  );

  function handleConfirm() {
    resolverRef.current?.(true);
    resolverRef.current = null;
    setState(CLOSED);
  }

  function handleCancel() {
    resolverRef.current?.(false);
    resolverRef.current = null;
    setState(CLOSED);
  }

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      <ConfirmDialog {...state} onConfirm={handleConfirm} onCancel={handleCancel} />
    </ConfirmContext.Provider>
  );
}
