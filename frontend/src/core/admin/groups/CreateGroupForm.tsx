import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import { apiClient } from "../../../api";

export function CreateGroupForm() {
  const [name, setName] = useState("");
  const [nameError, setNameError] = useState("");
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => apiClient.createGroup({ name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      setName("");
      setNameError("");
    },
    onError: (err: unknown) => {
      const problem = (err as { problem?: { errors?: Array<{ field: string; message: string }> } }).problem;
      if (problem?.errors) {
        const nameErr = problem.errors.find((e) => e.field === "name");
        if (nameErr) setNameError(nameErr.message);
      }
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setNameError("");
    mutation.mutate();
  }

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3, maxWidth: 400 }}
    >
      <Typography variant="h6">Create Group</Typography>
      <TextField
        label="Group Name"
        id="group-name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        required
        error={!!nameError}
        helperText={nameError}
      />
      <Button
        type="submit"
        variant="contained"
        disabled={!name.trim() || mutation.isPending}
      >
        Create Group
      </Button>
    </Box>
  );
}
