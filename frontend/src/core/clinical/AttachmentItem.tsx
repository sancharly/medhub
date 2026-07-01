import { useQuery } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import Link from "@mui/material/Link";
import Typography from "@mui/material/Typography";
import type { Attachment } from "../../api/generated/types";
import { apiClient } from "../../api";

interface AttachmentItemProps {
  attachment: Attachment;
}

const DICOM_TYPE = "application/dicom";
const DICOM_MODULE_KEY = "dicom-viewer";

export function AttachmentItem({ attachment }: AttachmentItemProps) {
  const url = apiClient.getAttachmentUrl(attachment.id);

  const { data: myModules } = useQuery({
    queryKey: ["myModules"],
    queryFn: () => apiClient.listMyModules(),
  });

  const isDicom = attachment.contentType === DICOM_TYPE;
  const dicomModuleEnabled = myModules?.includes(DICOM_MODULE_KEY) ?? false;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Typography variant="body2">{attachment.filename}</Typography>
      <Link href={url} target="_blank" rel="noopener noreferrer" variant="body2">
        Download
      </Link>
      {isDicom && dicomModuleEnabled && (
        <Link href={url} target="_blank" rel="noopener noreferrer" variant="body2">
          Open in viewer
        </Link>
      )}
    </Box>
  );
}
