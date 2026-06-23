import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";
import { useChangePassword, extractChangePasswordError } from "./useChangePassword";
import { PolicyHints } from "./PolicyHints";
import { apiClient } from "../api";
import { queryClient } from "../api/queryClient";

export function ChangePasswordPage() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [mismatch, setMismatch] = useState(false);

  const changePassword = useChangePassword();
  const fieldError = extractChangePasswordError(changePassword.error);

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setMismatch(true);
      return;
    }
    setMismatch(false);

    try {
      await changePassword.mutateAsync({ currentPassword, newPassword });
      queryClient.setQueryData(["me"], (old: typeof me) =>
        old ? { ...old, mustChangePassword: false } : old
      );
      navigate("/profile");
    } catch {
      // error rendered below
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        bgcolor: "background.default",
      }}
    >
      <Paper sx={{ p: 4, width: "100%", maxWidth: 480 }}>
        <Typography variant="h5" gutterBottom>
          Change password
        </Typography>

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Current password"
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            fullWidth
            margin="normal"
            required
            autoComplete="current-password"
          />
          <TextField
            label="New password"
            type="password"
            value={newPassword}
            onChange={(e) => {
              setNewPassword(e.target.value);
              setMismatch(false);
            }}
            fullWidth
            margin="normal"
            required
            autoComplete="new-password"
          />

          <PolicyHints password={newPassword} email={me?.email} />

          <TextField
            label="Confirm new password"
            type="password"
            value={confirmPassword}
            onChange={(e) => {
              setConfirmPassword(e.target.value);
              setMismatch(false);
            }}
            fullWidth
            margin="normal"
            required
            autoComplete="new-password"
          />

          {mismatch && (
            <Alert severity="error" sx={{ mt: 1 }} data-testid="mismatch-error">
              Passwords do not match.
            </Alert>
          )}

          {changePassword.isError && !mismatch && (
            <Alert severity="error" sx={{ mt: 1 }} data-testid="server-error">
              {fieldError?.message ?? "An error occurred"}
            </Alert>
          )}

          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{ mt: 2 }}
            disabled={changePassword.isPending || mismatch}
          >
            Change password
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
