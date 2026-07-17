import IconButton from "@mui/material/IconButton";
import LogoutIcon from "@mui/icons-material/Logout";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../../api";
import { queryClient } from "../../api/queryClient";

export function SignOutButton() {
  const navigate = useNavigate();

  async function handleSignOut() {
    try {
      await apiClient.logout();
    } catch {
      // session may already be invalid server-side; clear local state regardless
    }
    queryClient.clear();
    navigate("/login");
  }

  return (
    <IconButton onClick={handleSignOut} color="inherit" aria-label="Sign out">
      <LogoutIcon />
    </IconButton>
  );
}
