import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import List from "@mui/material/List";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import { PatientRow } from "./PatientRow";

export function PatientListPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["patients"],
    queryFn: () => apiClient.listPatients(),
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
        Failed to load patients. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Patients
      </Typography>
      {data.length === 0 ? (
        <Typography color="text.secondary">No patients found.</Typography>
      ) : (
        <List>
          {data.map((patient) => (
            <PatientRow key={patient.id} patient={patient} />
          ))}
        </List>
      )}
    </Box>
  );
}
