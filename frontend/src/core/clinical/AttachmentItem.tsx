import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import type { Attachment } from "../../api/generated/openapi";
import { apiClient } from "../../api";

interface AttachmentItemProps {
  attachment: Attachment;
}

const DICOM_TYPE = "application/dicom";

export function AttachmentItem({ attachment }: AttachmentItemProps) {
  const url = apiClient.getAttachmentUrl(attachment.id);

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2">{attachment.filename}</Typography>
      {attachment.contentType === DICOM_TYPE && (
        <Link href={url} target="_blank" rel="noopener noreferrer" variant="body2">
          Open in viewer
        </Link>
      )}
    </Box>
  );
}
