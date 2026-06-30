import { useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import type { Attachment } from "../../api/generated/types";

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
    onSuccess: (uploaded) => {
      queryClient.setQueryData<Attachment[]>(["attachments", entryId], (existing) => [
        ...(existing ?? []),
        ...uploaded,
      ]);
      queryClient.invalidateQueries({ queryKey: ["clinicalEntries", patientId] });
    },
  });

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
    </Box>
  );
}
