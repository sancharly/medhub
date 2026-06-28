import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { apiClient } from "../../api";

export function GrantConsentForm() {
  const [doctorId, setDoctorId] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => apiClient.grantConsent({ doctorId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me", "consents"] });
      setDoctorId("");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate();
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3 }}
    >
      <Typography variant="h6">Grant Consent</Typography>
      <TextField
        label="Doctor ID"
        id="doctor-id"
        value={doctorId}
        onChange={(e) => setDoctorId(e.target.value)}
        required
      />
      <Button
        type="submit"
        variant="contained"
        disabled={!doctorId.trim() || mutation.isPending}
      >
        Grant
      </Button>
    </Box>
  );
}
