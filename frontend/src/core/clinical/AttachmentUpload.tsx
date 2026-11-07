import { useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import Alert from "@mui/material/Alert";
import { apiClient } from "../../api";
import { ApiError } from "../../api/client";

interface AttachmentUploadProps {
  entryId: string;
  patientId: string;
}

export function AttachmentUpload({ entryId, patientId }: AttachmentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (files: File[]) =>
      Promise.all(files.map((file) => apiClient.uploadAttachment(entryId, file))),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["attachments", entryId] });
      queryClient.invalidateQueries({ queryKey: ["clinicalEntries", patientId] });
    },
  });

  // The server's reason (for example a file name over 255 bytes) is shown to the user (PRB-069).
  const errorMessage = mutation.isError
    ? mutation.error instanceof ApiError && mutation.error.problem.detail
      ? mutation.error.problem.detail
      : "The file could not be uploaded."
    : null;

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const files = e.target.files;
    if (files && files.length > 0) {
      mutation.mutate(Array.from(files));
      // Reset so the same file(s) can be uploaded again if needed
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <Box>
      <label htmlFor={`upload-${entryId}`}>
        <input
          id={`upload-${entryId}`}
          ref={inputRef}
          type="file"
          multiple
          aria-label="Upload file"
          style={{ display: "none" }}
          onChange={handleChange}
        />
        <Button component="span" variant="outlined" size="small">
          Upload file
        </Button>
      </label>
      {errorMessage && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {errorMessage}
        </Alert>
      )}
    </Box>
  );
}
