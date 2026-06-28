import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import type { AccountSummary } from "../../../api/generated/types";

interface DeleteConfirmDialogProps {
  account: AccountSummary | null;
  onConfirm: () => void;
  onCancel: () => void;
}

export function DeleteConfirmDialog({
  account,
  onConfirm,
  onCancel,
}: DeleteConfirmDialogProps) {
  if (!account) return null;

  return (
    <Dialog open onClose={onCancel} aria-labelledby="delete-dialog-title">
      <DialogTitle id="delete-dialog-title">Delete Account</DialogTitle>
      <DialogContent>
        <Typography gutterBottom>
          You are about to permanently delete this account:
        </Typography>
        <Typography>
          <strong>Email:</strong> {account.email}
        </Typography>
        <Typography gutterBottom>
          <strong>Role:</strong> {account.userType}
        </Typography>
        <Alert severity="error" sx={{ mt: 2 }}>
          This action is unrecoverable. All data associated with this account,
          including any activation codes, will be permanently lost and cannot
          be restored.
        </Alert>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>Cancel</Button>
        <Button onClick={onConfirm} color="error" variant="contained">
          Delete permanently
        </Button>
      </DialogActions>
    </Dialog>
  );
}
