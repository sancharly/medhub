import { useQuery } from "@tanstack/react-query";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import Box from "@mui/material/Box";
import { apiClient } from "../../api";
import type { Attachment, ClinicalEntry } from "../../api/generated/types";
import { AttachmentItem } from "./AttachmentItem";

interface ClinicalEntryListProps {
  entries: ClinicalEntry[];
}

function EntryAttachments({ entryId }: { entryId: string }) {
  const { data: attachments } = useQuery<Attachment[]>({
    queryKey: ["attachments", entryId],
    queryFn: () => apiClient.listAttachments(entryId),
  });

  if (!attachments || attachments.length === 0) return null;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, mt: 1 }}>
      {attachments.map((attachment) => (
        <AttachmentItem key={attachment.id} attachment={attachment} />
      ))}
    </Box>
  );
}

export function ClinicalEntryList({ entries }: ClinicalEntryListProps) {
  // Sort reverse-chronological (newest first)
  const sorted = [...entries].sort(
    (a, b) => new Date(b.occurredAt).getTime() - new Date(a.occurredAt).getTime()
  );

  return (
    <List>
      {sorted.map((entry) => (
        <ListItem
          key={entry.id}
          alignItems="flex-start"
          sx={{ flexDirection: "column" }}
        >
          <ListItemText
            primary={entry.description}
            secondary={
              <Typography component="span" variant="caption" color="text.secondary">
                {new Date(entry.occurredAt).toLocaleString()} — Author: {entry.authorName}
              </Typography>
            }
          />
          <EntryAttachments entryId={entry.id} />
          <Divider sx={{ width: "100%", mt: 1 }} />
        </ListItem>
      ))}
    </List>
  );
}
