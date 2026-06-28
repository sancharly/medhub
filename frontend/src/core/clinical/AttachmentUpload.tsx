import { useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";

interface AttachmentUploadProps {
  entryId: string;
  patientId: string;
}

export function AttachmentUpload({ entryId, patientId }: AttachmentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadAttachment(entryId, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["clinicalEntries", patientId] });
    },
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      mutation.mutate(file);
      // Reset so the same file can be uploaded again if needed
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
          aria-label="Upload file"
          style={{ display: "none" }}
          onChange={handleChange}
        />
        <Button component="span" variant="outlined" size="small">
          Upload file
        </Button>
      </label>
    </Box>
  );
}
