import { useMutation, useQueryClient } from "@tanstack/react-query";
import Button from "@mui/material/Button";
import { apiClient } from "../../api";
import { useConfirm } from "../confirm/useConfirm";
import { useErrorToast } from "../error/useErrorToast";

interface RevokeActionProps {
  grantId: string;
}

export function RevokeAction({ grantId }: RevokeActionProps) {
  const confirm = useConfirm();
  const errorToast = useErrorToast();
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => apiClient.revokeConsent(grantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me", "consents"] });
    },
    onError: (err) => {
      errorToast(err as Error);
    },
  });

  async function handleRevoke() {
    const ok = await confirm({
      title: "Revoke consent",
      description: "Are you sure you want to revoke this consent grant? The doctor will lose access to your records.",
      destructive: true,
    });
    if (ok) {
      mutation.mutate();
    }
  }

  return (
    <Button
      size="small"
      variant="outlined"
      color="error"
      onClick={handleRevoke}
      disabled={mutation.isPending}
    >
      Revoke
    </Button>
  );
}
