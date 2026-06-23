import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    fontSize: 14,
  },
  palette: {
    primary: {
      main: "#1565c0",
    },
    secondary: {
      main: "#0288d1",
    },
    error: {
      main: "#c62828",
    },
    background: {
      default: "#f5f7fa",
    },
  },
  spacing: 8,
  components: {
    MuiButtonBase: {
      styleOverrides: {
        root: {
          minHeight: 44,
          minWidth: 44,
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          minHeight: 44,
          minWidth: 44,
        },
      },
    },
  },
});
