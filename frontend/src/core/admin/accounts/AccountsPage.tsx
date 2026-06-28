import { useQuery } from "@tanstack/react-query";
import Typography from "@mui/material/Typography";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Box from "@mui/material/Box";
import { apiClient } from "../../../api";
import { AccountList } from "./AccountList";
import { CreateAccountForm } from "./CreateAccountForm";

export function AccountsPage() {
  const { data: me, isLoading: meLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => apiClient.listAccounts(),
  });

  if (meLoading || isLoading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !data || !me) {
    return (
      <Alert severity="error" role="alert">
        Failed to load accounts. Please try again.
      </Alert>
    );
  }

  const isSysadmin = me.userType === "SYSADMIN";

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Account Management
      </Typography>

      <CreateAccountForm isSysadmin={isSysadmin} />

      {data.length === 0 ? (
        <Typography color="text.secondary">No accounts found.</Typography>
      ) : (
        <AccountList
          accounts={data}
          isSysadmin={isSysadmin}
          actingUserId={me.id}
        />
      )}
    </Box>
  );
}
