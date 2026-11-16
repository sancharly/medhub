import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { ProfileFields } from "./ProfileFields";
import { useMe } from "../../auth/useMe";

export function ProfilePage() {
  const { data, isLoading, error } = useMe();

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
