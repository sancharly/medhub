import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Divider from "@mui/material/Divider";
import type { Group, InstalledModule } from "../../../api/generated/types";
import { GroupMembers } from "./GroupMembers";
import { GroupModules } from "./GroupModules";

interface GroupListProps {
  groups: Group[];
  installedModules: InstalledModule[];
}

export function GroupList({ groups, installedModules }: GroupListProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {groups.map((group) => (
        <Box key={group.id} sx={{ border: 1, borderColor: "divider", borderRadius: 1, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            {group.name}
          </Typography>
          <Typography variant="subtitle2" gutterBottom>
            Members
          </Typography>
          {group.members.length === 0 && (
            <Typography variant="body2" color="text.secondary">
              No members.
            </Typography>
          )}
          <GroupMembers groupId={group.id} members={group.members} />
          <Divider sx={{ my: 1 }} />
          <Typography variant="subtitle2" gutterBottom>
            Modules
          </Typography>
          {installedModules.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No modules installed.
            </Typography>
          ) : (
            <GroupModules
              groupId={group.id}
              enabledModules={group.enabledModules}
              installedModules={installedModules}
            />
          )}
        </Box>
      ))}
    </Box>
  );
}
