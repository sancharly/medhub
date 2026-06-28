import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import type { ClinicalEntry } from "../../api/generated/types";

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
                  {new Date(entry.occurredAt).toLocaleDateString()} — Author: {entry.authorId}
                </Typography>
              </>
            }
          />
          <Divider sx={{ width: "100%", mt: 1 }} />
        </ListItem>
      ))}
    </List>
  );
}
