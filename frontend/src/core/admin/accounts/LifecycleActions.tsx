import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";
import { apiClient } from "../../../api";
import type { AccountSummary } from "../../../api/generated/types";
import { DeleteConfirmDialog } from "./DeleteConfirmDialog";

interface LifecycleActionsProps {
  account: AccountSummary;
  isSelf: boolean;
}

export function LifecycleActions({ account, isSelf }: LifecycleActionsProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const queryClient = useQueryClient();

  const deactivateMutation = useMutation({
    mutationFn: () => apiClient.deactivateAccount(account.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });

  const reactivateMutation = useMutation({
    mutationFn: () => apiClient.reactivateAccount(account.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["accounts"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiClient.deleteAccount(account.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setShowDeleteDialog(false);
    },
  });

  const resendActivationMutation = useMutation({
    mutationFn: () => apiClient.resendActivation(account.id),
  });

  return (
    <Box sx={{ display: "flex", gap: 1 }}>
      {account.state === "ACTIVE" && (
        <Button
          size="small"
          variant="outlined"
          onClick={() => deactivateMutation.mutate()}
          disabled={isSelf || deactivateMutation.isPending}
        >
          Deactivate
        </Button>
      )}
      {account.state === "INACTIVE" && (
        <Button
          size="small"
          variant="outlined"
          color="success"
          onClick={() => reactivateMutation.mutate()}
          disabled={reactivateMutation.isPending}
        >
          Reactivate
        </Button>
      )}
      {account.state === "INACTIVE" && (
        <Button
          size="small"
          variant="outlined"
          onClick={() => resendActivationMutation.mutate()}
          disabled={resendActivationMutation.isPending}
        >
          Resend activation
        </Button>
      )}
      {account.state !== "DELETED" && (
        <Button
          size="small"
          variant="outlined"
          color="error"
          onClick={() => setShowDeleteDialog(true)}
        >
          Delete
        </Button>
      )}
      {showDeleteDialog && (
        <DeleteConfirmDialog
          account={account}
          onConfirm={() => deleteMutation.mutate()}
          onCancel={() => setShowDeleteDialog(false)}
        />
      )}
      {resendActivationMutation.isSuccess && (
        <Alert severity="success" sx={{ py: 0 }}>
          Activation email resent.
        </Alert>
      )}
      {resendActivationMutation.isError && (
        <Alert severity="error" sx={{ py: 0 }}>
          Failed to resend activation email.
        </Alert>
      )}
    </Box>
  );
}
