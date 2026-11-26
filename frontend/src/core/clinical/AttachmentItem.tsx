import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import type { Attachment } from "../../api/generated/types";
import { apiClient } from "../../api";

interface AttachmentItemProps {
  attachment: Attachment;
}

export function AttachmentItem({ attachment }: AttachmentItemProps) {
  const url = apiClient.getAttachmentUrl(attachment.id);

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2">{attachment.filename}</Typography>
      <Link href={url} target="_blank" rel="noopener noreferrer" variant="body2">
        Download
      </Link>
    </Box>
  );
}
