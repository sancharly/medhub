import { useState } from "react";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface SetPasswordFormProps {
  onSubmit: (password: string, confirmPassword: string) => void;
  isPending?: boolean;
  fieldError?: string;
}

export function SetPasswordForm({
  onSubmit,
  isPending,
  fieldError,
}: SetPasswordFormProps) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirm) {
      setMismatch(true);
      return;
    }
    setMismatch(false);
    onSubmit(password, confirm);
  }

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      <TextField
        label="Password"
        type="password"
        value={password}
        onChange={(e) => {
          setPassword(e.target.value);
          setMismatch(false);
        }}
        fullWidth
        margin="normal"
        required
        autoComplete="new-password"
      />
      <TextField
        label="Confirm password"
        type="password"
        value={confirm}
        onChange={(e) => {
          setConfirm(e.target.value);
          setMismatch(false);
        }}
        fullWidth
        margin="normal"
        required
        autoComplete="new-password"
      />
      {mismatch && (
        <Typography color="error" variant="body2" data-testid="mismatch-error">
          Passwords do not match.
        </Typography>
      )}
      {fieldError && (
        <Typography color="error" variant="body2" data-testid="field-error">
          {fieldError}
        </Typography>
      )}
      <Button
        type="submit"
        variant="contained"
        fullWidth
        sx={{ mt: 2 }}
        disabled={isPending || mismatch}
      >
        Set password
      </Button>
    </Box>
  );
}
