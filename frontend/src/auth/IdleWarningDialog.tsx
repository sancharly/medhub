import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import Dialog from "@mui/material/Dialog";
import DialogTitle from "@mui/material/DialogTitle";
import DialogContent from "@mui/material/DialogContent";
import DialogContentText from "@mui/material/DialogContentText";
import DialogActions from "@mui/material/DialogActions";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { apiClient } from "../api";
import { AuthError } from "../api/client";

interface IdleWarningDialogProps {
  open: boolean;
  expiresAt: number;
  onExtended: (newDeadline: number) => void;
  onLogout: () => void;
}

function formatCountdown(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function IdleWarningDialog({
  open,
  expiresAt,
  onExtended,
  onLogout,
}: IdleWarningDialogProps) {
  const navigate = useNavigate();
  const [remaining, setRemaining] = useState(expiresAt - Date.now());
  const [extending, setExtending] = useState(false);

  useEffect(() => {
    if (!open) return;

    const interval = setInterval(() => {
      const rem = expiresAt - Date.now();
      setRemaining(rem);
      if (rem <= 0) {
        clearInterval(interval);
        navigate("/login?timeout=1");
      }
    }, 500);

    return () => clearInterval(interval);
  }, [open, expiresAt, navigate]);

  const handleExtend = useCallback(async () => {
    setExtending(true);
    try {
      const result = await apiClient.extendSession();
      onExtended(new Date(result.expiresAt).getTime());
    } catch (err) {
      if (err instanceof AuthError) {
        navigate("/login?timeout=1");
      }
    } finally {
      setExtending(false);
    }
  }, [navigate, onExtended]);

  return (
    <Dialog open={open} aria-labelledby="idle-dialog-title">
      <DialogTitle id="idle-dialog-title">Session expiring soon</DialogTitle>
      <DialogContent>
        <DialogContentText>
          Your session will expire due to inactivity.
        </DialogContentText>
        <Typography variant="h4" align="center" sx={{ mt: 2 }} data-testid="countdown">
          {formatCountdown(remaining)}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onLogout} disabled={extending}>
          Log out now
        </Button>
        <Button
          variant="contained"
          onClick={handleExtend}
          disabled={extending}
          autoFocus
        >
          Stay signed in
        </Button>
      </DialogActions>
    </Dialog>
  );
}
