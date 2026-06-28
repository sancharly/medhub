import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../../api";
import { GroupList } from "./GroupList";
import { CreateGroupForm } from "./CreateGroupForm";

export function GroupsPage() {
  const { data: groups, isLoading: groupsLoading, error: groupsError } = useQuery({
    queryKey: ["groups"],
    queryFn: () => apiClient.listGroups(),
  });

  const { data: modules, isLoading: modulesLoading } = useQuery({
    queryKey: ["modules"],
    queryFn: () => apiClient.listInstalledModules(),
  });

  if (groupsLoading || modulesLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (groupsError) {
    return (
      <Alert severity="error" role="alert">
        Failed to load groups. Please try again.
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Groups & Modules
      </Typography>

      <CreateGroupForm />

      {!groups || groups.length === 0 ? (
        <Typography color="text.secondary">No groups found.</Typography>
      ) : (
        <GroupList groups={groups} installedModules={modules ?? []} />
      )}
    </Box>
  );
}
