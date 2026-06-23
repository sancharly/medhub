import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import { SetPasswordForm } from "./SetPasswordForm";
import { useActivate } from "./useActivate";
import { apiClient } from "../api";
import { ApiError } from "../api/client";

type TokenState = "loading" | "valid" | "invalid";

export function ActivationPage() {
  const { token } = useParams<{ token: string }>();
  const [tokenState, setTokenState] = useState<TokenState>("loading");
  const [fieldError, setFieldError] = useState<string | undefined>();
  const activate = useActivate(token!);

  useEffect(() => {
    apiClient
      .getActivation(token!)
      .then(() => setTokenState("valid"))
      .catch(() => setTokenState("invalid"));
  }, [token]);

  async function handleSubmit(password: string) {
    setFieldError(undefined);
    try {
      await activate.mutateAsync(password);
    } catch (err) {
      if (err instanceof ApiError && err.problem.errors?.length) {
        setFieldError(err.problem.errors[0].message);
      } else if (err instanceof ApiError) {
        setFieldError(err.problem.detail ?? err.problem.title);
      }
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
      <Paper sx={{ p: 4, width: "100%", maxWidth: 420 }}>
        <Typography variant="h5" gutterBottom>
          Activate account
        </Typography>

        {tokenState === "loading" && <CircularProgress />}

        {tokenState === "invalid" && (
          <Typography data-testid="invalid-token-message">
            This activation link is no longer valid. Please request a new one.
          </Typography>
        )}

        {tokenState === "valid" && (
          <SetPasswordForm
            onSubmit={handleSubmit}
            isPending={activate.isPending}
            fieldError={fieldError}
          />
        )}
      </Paper>
    </Box>
  );
}
