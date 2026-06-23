import React from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemText from "@mui/material/ListItemText";
import Switch from "@mui/material/Switch";
import { apiClient } from "../../../api";
import type { InstalledModule } from "../../../api/generated/openapi";

interface GroupModulesProps {
  groupId: string;
  enabledModules: string[];
  installedModules: InstalledModule[];
}

export function GroupModules({
  groupId,
  enabledModules,
  installedModules,
}: GroupModulesProps) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: ({
      moduleKey,
      enabled,
    }: {
      moduleKey: string;
      enabled: boolean;
    }) => apiClient.setGroupModuleEnabled(groupId, moduleKey, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["groups"] }),
  });

  return (
    <List dense>
      {installedModules.map((mod) => {
        const isEnabled = enabledModules.includes(mod.moduleKey);
        return (
          <ListItem key={mod.moduleKey}>
            <ListItemText primary={mod.name} />
            <Switch
              checked={isEnabled}
              onChange={() =>
                mutation.mutate({ moduleKey: mod.moduleKey, enabled: !isEnabled })
              }
              disabled={mutation.isPending}
              slotProps={{
                input: { "aria-label": `Toggle ${mod.name}` } as React.InputHTMLAttributes<HTMLInputElement>,
              }}
            />
          </ListItem>
        );
      })}
    </List>
  );
}
