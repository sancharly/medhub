import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import { AppointmentList } from "./AppointmentList";
import { CreateAppointmentForm } from "./CreateAppointmentForm";

export function AppointmentsPage() {
  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["appointments"],
    queryFn: () => apiClient.listAppointments(),
  });

  if (meLoading || isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !data) {
    return (
      <Alert severity="error" role="alert">
        Failed to load appointments. Please try again.
      </Alert>
    );
  }

  const isPatient = me?.userType === "patient";

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Appointments
      </Typography>

      {!isPatient && <CreateAppointmentForm />}

      {data.length === 0 ? (
        <Typography color="text.secondary">No appointments found.</Typography>
      ) : (
        <AppointmentList appointments={data} isPatient={isPatient} />
      )}
    </Box>
  );
}
