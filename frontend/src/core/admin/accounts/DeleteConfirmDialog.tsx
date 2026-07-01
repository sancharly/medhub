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
          Deletion anonymizes this user&apos;s data into a dataset retained for
          5 years; the email address is released and may be reused by another
          account. A one-time retrieval code is emailed to the user — that code
          is <strong>never stored</strong> by the system, so it is the user&apos;s
          only way to retrieve the dataset. If the code is lost, the data is
          unrecoverable. This action is unrecoverable and cannot be undone.
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
