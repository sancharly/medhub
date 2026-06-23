import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import Box from "@mui/material/Box";
import type { ClinicalEntry } from "../../api/generated/openapi";
import { AttachmentItem } from "./AttachmentItem";

interface ClinicalEntryListProps {
  entries: ClinicalEntry[];
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
              <>
                <Typography component="span" variant="caption" color="text.secondary">
                  {new Date(entry.occurredAt).toLocaleDateString()} — {entry.authorName}
                </Typography>
              </>
            }
          />
          {entry.attachments.length > 0 && (
            <Box sx={{ mt: 1, pl: 2 }}>
              {entry.attachments.map((att) => (
                <AttachmentItem key={att.id} attachment={att} />
              ))}
            </Box>
          )}
          <Divider sx={{ width: "100%", mt: 1 }} />
        </ListItem>
      ))}
    </List>
  );
}
