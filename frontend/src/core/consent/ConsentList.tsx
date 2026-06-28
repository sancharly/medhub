import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import type { ConsentGrant } from "../../api/generated/types";
import { RevokeAction } from "./RevokeAction";

interface ConsentListProps {
  grants: ConsentGrant[];
}

function sourceLabel(grant: ConsentGrant): string {
  if (grant.sourceType === "APPOINTMENT" && grant.appointmentId) {
    return `APPOINTMENT (${grant.appointmentId})`;
  }
  return grant.sourceType;
}

export function ConsentList({ grants }: ConsentListProps) {
  return (
    <List>
      {grants.map((grant) => (
        <ListItem
          key={grant.id}
          secondaryAction={<RevokeAction grantId={grant.id} />}
        >
          <ListItemText
            primary={`Doctor: ${grant.doctorId}`}
            secondary={
              <>
                <Typography component="span" variant="caption" color="text.secondary">
                  {sourceLabel(grant)}
                </Typography>
              </>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}
