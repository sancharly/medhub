import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import Paper from "@mui/material/Paper";
import { useLogin } from "./useLogin";
import type { UserType } from "../api/generated/types";

function roleLanding(userType: UserType): string {
  if (userType === "PATIENT") return "/appointments";
  if (userType === "DOCTOR") return "/patients";
  return "/admin/accounts";
}

export function LoginPage() {
  const navigate = useNavigate();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [evictedDest, setEvictedDest] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const result = await login.mutateAsync({ email, password });
      if (result.mustChangePassword) {
        navigate("/password");
        return;
      }
      const dest = roleLanding(result.user.userType);
      if (result.evictedSession) {
        setEvictedDest(dest);
        return; // show notice first, don't navigate yet
      }
      navigate(dest);
    } catch {
      // error rendered below
    }
  }

  const hasError = login.isError;

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
      <Paper sx={{ p: 4, width: "100%", maxWidth: 400 }}>
        <Typography variant="h5" gutterBottom>
          Sign in
        </Typography>

        {evictedDest && (
          <Alert
            severity="warning"
            sx={{ mb: 2 }}
            action={
              <Button color="inherit" size="small" onClick={() => navigate(evictedDest)}>
                Continue
              </Button>
            }
          >
            Your previous session was ended because you signed in elsewhere.
          </Alert>
        )}

        {hasError && (
          <Alert severity="error" sx={{ mb: 2 }} data-testid="login-error">
            Invalid email or password.
          </Alert>
        )}

        <Box component="form" onSubmit={handleSubmit} noValidate>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            margin="normal"
            required
            autoComplete="email"
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            margin="normal"
            required
            autoComplete="current-password"
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            sx={{ mt: 2 }}
            disabled={login.isPending}
          >
            Sign in
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
