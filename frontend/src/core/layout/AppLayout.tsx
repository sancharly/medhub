import Box from "@mui/material/Box";
import AppBar from "@mui/material/AppBar";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";

export interface AppLayoutProps {
  navigation: React.ReactNode;
  children: React.ReactNode;
}

const NAV_WIDTH = 240;

export function AppLayout({ navigation, children }: AppLayoutProps) {
  return (
    <Box sx={{ display: "flex", minHeight: "100vh", overflow: "hidden" }}>
      <AppBar
        position="fixed"
        sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}
        aria-label="header"
      >
        <Toolbar>
          <Typography variant="h6" noWrap>
            MedHub
          </Typography>
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        aria-label="navigation"
        sx={{
          width: { md: NAV_WIDTH },
          flexShrink: { md: 0 },
        }}
      >
        {navigation}
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          mt: "64px",
          p: 3,
          width: { xs: "100%", md: `calc(100% - ${NAV_WIDTH}px)` },
          overflowX: "hidden",
          maxWidth: "100%",
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
