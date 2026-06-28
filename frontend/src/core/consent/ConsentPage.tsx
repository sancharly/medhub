import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import { ConsentList } from "./ConsentList";
import { GrantConsentForm } from "./GrantConsentForm";

export function ConsentPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["me", "consents"],
    queryFn: () => apiClient.listMyConsents(),
  });

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Alert severity="error" role="alert">
        Failed to load consents. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        My Consents
      </Typography>

      <GrantConsentForm />

      {data.length === 0 ? (
        <Typography color="text.secondary">No active consent grants.</Typography>
      ) : (
        <ConsentList grants={data} />
      )}
    </Box>
  );
}
