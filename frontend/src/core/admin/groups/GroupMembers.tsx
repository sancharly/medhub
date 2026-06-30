import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import IconButton from "@mui/material/IconButton";
import DeleteIcon from "@mui/icons-material/Delete";
import Typography from "@mui/material/Typography";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import { apiClient } from "../../../api";
import type { GroupMember } from "../../../api/generated/types";

interface GroupMembersProps {
  groupId: string;
  members: GroupMember[];
}

export function GroupMembers({ groupId, members }: GroupMembersProps) {
  const [accountId, setAccountId] = useState("");
  const queryClient = useQueryClient();

  const removeMutation = useMutation({
    mutationFn: (id: string) => apiClient.removeGroupMember(groupId, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["groups"] }),
  });

  const addMutation = useMutation({
    mutationFn: (id: string) => apiClient.addGroupMember(groupId, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      setAccountId("");
    },
  });

  function handleAddSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (accountId.trim()) addMutation.mutate(accountId.trim());
  }

  return (
    <Box>
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
      <Box
        component="form"
        onSubmit={handleAddSubmit}
        sx={{ display: "flex", gap: 1, alignItems: "center", mt: 1 }}
      >
        <TextField
          label="Account ID or email"
          id={`add-member-${groupId}`}
          size="small"
          value={accountId}
          onChange={(e) => setAccountId(e.target.value)}
        />
        <Button
          type="submit"
          variant="outlined"
          size="small"
          disabled={!accountId.trim() || addMutation.isPending}
        >
          Add member
        </Button>
      </Box>
    </Box>
  );
}
