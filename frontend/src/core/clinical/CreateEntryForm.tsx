import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { apiClient } from "../../api";
import type { CreateClinicalEntryRequest } from "../../api/generated/types";

interface CreateEntryFormProps {
  patientId: string;
}

export function CreateEntryForm({ patientId }: CreateEntryFormProps) {
  const [description, setDescription] = useState("");
  const [occurredDate, setOccurredDate] = useState("");
  const [occurredTime, setOccurredTime] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: CreateClinicalEntryRequest) =>
      apiClient.createClinicalEntry(patientId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clinicalEntries", patientId] });
      setDescription("");
      setOccurredDate("");
      setOccurredTime("");
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate({
      occurredAt: new Date(`${occurredDate}T${occurredTime}`).toISOString(),
      description,
    });
  }

  const isDisabled = !description.trim() || !occurredDate || !occurredTime;

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3 }}>
      <Typography variant="h6">Add Entry</Typography>
      <TextField
        label="Description"
        id="entry-description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
        multiline
        rows={3}
        required
      />
      <TextField
        label="Date"
        id="entry-date"
        type="date"
        value={occurredDate}
        onChange={(e) => setOccurredDate(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
        required
      />
      <TextField
        label="Time"
        id="entry-time"
        type="time"
        value={occurredTime}
        onChange={(e) => setOccurredTime(e.target.value)}
        slotProps={{ inputLabel: { shrink: true } }}
        required
      />
      <Button type="submit" variant="contained" disabled={isDisabled}>
        Add Entry
      </Button>
    </Box>
  );
}
