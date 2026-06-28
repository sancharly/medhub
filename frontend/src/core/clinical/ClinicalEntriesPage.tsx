import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import { ApiError } from "../../api/client";
import { ClinicalEntryList } from "./ClinicalEntryList";
import { CreateEntryForm } from "./CreateEntryForm";
import { AttachmentUpload } from "./AttachmentUpload";

interface ClinicalEntriesPageProps {
  userType?: "DOCTOR" | "PATIENT";
}

export function ClinicalEntriesPage({ userType = "DOCTOR" }: ClinicalEntriesPageProps) {
  const { patientId } = useParams<{ patientId: string }>();

  const { data, isLoading, error } = useQuery({
    queryKey: ["clinicalEntries", patientId],
    queryFn: () => apiClient.listClinicalEntries(patientId ?? ""),
    enabled: !!patientId,
  });

  if (!patientId) {
    return (
      <Alert severity="error" role="alert">
        Invalid route: patient ID is missing.
      </Alert>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    const status = error instanceof ApiError ? error.problem.status : undefined;
    if (status === 403) {
      return (
        <Alert severity="error" role="alert">
          Access denied. You do not have permission to view these records.
        </Alert>
      );
    }
    return (
      <Alert severity="error" role="alert">
        Failed to load clinical entries. Please try again.
      </Alert>
    );
  }

  const isDoctor = userType === "DOCTOR";

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Clinical Entries
      </Typography>

      {isDoctor && <CreateEntryForm patientId={patientId} />}

      {data && data.length > 0 ? (
        <>
          <ClinicalEntryList entries={data} />
          {isDoctor && (
            <Box sx={{ mt: 1 }}>
              {data.map((entry) => (
                <Box key={entry.id} sx={{ mt: 1 }}>
                  <AttachmentUpload entryId={entry.id} patientId={patientId} />
                </Box>
              ))}
            </Box>
          )}
        </>
      ) : (
        <Typography color="text.secondary">No clinical entries found.</Typography>
      )}
    </Box>
  );
}
