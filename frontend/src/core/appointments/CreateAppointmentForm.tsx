import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { apiClient } from "../../api";
import type { CreateAppointmentRequest } from "../../api/generated/types";

export function CreateAppointmentForm() {
  const [doctorId, setDoctorId] = useState("");
  const [patientId, setPatientId] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: CreateAppointmentRequest) =>
      apiClient.createAppointment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      setDoctorId("");
      setPatientId("");
      setScheduledAt("");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate({ doctorId, patientId, scheduledAt });
  }

  const isDisabled = !doctorId.trim() || !patientId.trim() || !scheduledAt;

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3 }}
    >
      <Typography variant="h6">Schedule Appointment</Typography>
      <TextField
        label="Doctor ID"
        value={doctorId}
        onChange={(e) => setDoctorId(e.target.value)}
        required
      />
      <TextField
        label="Patient ID"
        value={patientId}
        onChange={(e) => setPatientId(e.target.value)}
        required
      />
      <TextField
        label="Date & Time"
        type="datetime-local"
        value={scheduledAt}
        onChange={(e) => setScheduledAt(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
        required
      />
      <Button type="submit" variant="contained" disabled={isDisabled}>
        Schedule
      </Button>
    </Box>
  );
}
