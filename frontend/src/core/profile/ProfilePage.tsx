import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import { ProfileFields } from "./ProfileFields";

export function ProfilePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
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
        Failed to load profile. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        My Profile
      </Typography>
      <ProfileFields user={data} />
    </Box>
  );
}
