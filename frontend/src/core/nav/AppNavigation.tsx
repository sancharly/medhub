import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import Drawer from "@mui/material/Drawer";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import IconButton from "@mui/material/IconButton";
import MenuIcon from "@mui/icons-material/Menu";
import Box from "@mui/material/Box";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useTheme } from "@mui/material/styles";
import { useNavItems } from "./useNavItems";
import type { UserType } from "./types";

interface AppNavigationProps {
  userType: UserType;
}

const DRAWER_WIDTH = 240;

export function AppNavigation({ userType }: AppNavigationProps) {
  const { items } = useNavItems(userType);
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));
  const [mobileOpen, setMobileOpen] = useState(false);

  const navList = (
    <List>
      {items.map((item) => (
        <ListItemButton
          key={item.path}
          selected={location.pathname === item.path}
          onClick={() => {
            navigate(item.path);
            setMobileOpen(false);
          }}
        >
          <ListItemText primary={item.label} />
        </ListItemButton>
      ))}
    </List>
  );

  if (isDesktop) {
    return (
      <Drawer
        variant="permanent"
        open
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
            top: "64px",
          },
        }}
      >
        {navList}
      </Drawer>
    );
  }

  return (
    <>
      <Box sx={{ position: "fixed", top: 8, left: 8, zIndex: 1300 }}>
        <IconButton
          aria-label="open navigation"
          onClick={() => setMobileOpen(true)}
        >
          <MenuIcon />
        </IconButton>
      </Box>
      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          "& .MuiDrawer-paper": {
            width: DRAWER_WIDTH,
            boxSizing: "border-box",
          },
        }}
      >
        {navList}
      </Drawer>
    </>
  );
}
