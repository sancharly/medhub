import { useMutation, useQueryClient } from "@tanstack/react-query";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import IconButton from "@mui/material/IconButton";
import DeleteIcon from "@mui/icons-material/Delete";
import Typography from "@mui/material/Typography";
import { apiClient } from "../../../api";
import type { GroupMember } from "../../../api/generated/types";

interface GroupMembersProps {
  groupId: string;
  members: GroupMember[];
}

export function GroupMembers({ groupId, members }: GroupMembersProps) {
  const queryClient = useQueryClient();

  const removeMutation = useMutation({
    mutationFn: (accountId: string) =>
      apiClient.removeGroupMember(groupId, accountId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["groups"] }),
  });

  return (
    <List dense>
      {members.map((member) => (
        <ListItem
          key={member.accountId}
          secondaryAction={
            member.membershipSource === "MANUAL" ? (
              <IconButton
                edge="end"
                aria-label={`Remove ${member.name}`}
                size="small"
                onClick={() => removeMutation.mutate(member.accountId)}
                disabled={removeMutation.isPending}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            ) : undefined
          }
        >
          <ListItemText
            primary={member.name}
            secondary={
              <Typography component="span" variant="caption" color="text.secondary">
                {member.membershipSource === "AUTO" ? "Auto-assigned" : "Manual"}
              </Typography>
            }
          />
        </ListItem>
      ))}
    </List>
  );
}
