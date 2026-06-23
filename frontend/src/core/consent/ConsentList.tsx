import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Typography from "@mui/material/Typography";
import type { ConsentGrant } from "../../api/generated/openapi";
import { RevokeAction } from "./RevokeAction";

interface ConsentListProps {
  grants: ConsentGrant[];
}

function sourceLabel(source: string): string {
  if (source === "MANUAL") return "MANUAL";
  if (source.startsWith("APPOINTMENT:")) {
    const id = source.replace("APPOINTMENT:", "");
    return `APPOINTMENT (${id})`;
  }
  return source;
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
            primary={grant.doctorName}
            secondary={
              <>
                <Typography component="span" variant="caption" color="text.secondary">
                  {sourceLabel(grant.source)} — granted {new Date(grant.grantedAt).toLocaleDateString()}
                </Typography>
              </>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}
