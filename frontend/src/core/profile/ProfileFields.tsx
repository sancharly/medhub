import Typography from "@mui/material/Typography";
import Box from "@mui/material/Box";
import type { MeResponse } from "../../api/generated/openapi";

interface ProfileFieldsProps {
  user: MeResponse;
}

export function ProfileFields({ user }: ProfileFieldsProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {user.firstName && (
        <Box>
          <Typography variant="caption" color="text.secondary">
            First name
          </Typography>
          <Typography>{user.firstName}</Typography>
        </Box>
      )}
      {user.surname && (
        <Box>
          <Typography variant="caption" color="text.secondary">
            Surname
          </Typography>
          <Typography>{user.surname}</Typography>
        </Box>
      )}
      <Box>
        <Typography variant="caption" color="text.secondary">
          Email
        </Typography>
        <Typography>{user.email}</Typography>
      </Box>
      <Box>
        <Typography variant="caption" color="text.secondary">
          Role
        </Typography>
        <Typography>{user.userType}</Typography>
      </Box>
    </Box>
  );
}
