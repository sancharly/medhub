import IconButton from "@mui/material/IconButton";
import LightModeIcon from "@mui/icons-material/LightMode";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import { useColorScheme } from "@mui/material/styles";

/**
 * Chrome-header toggle between light and dark mode (SR-039).
 * While `mode` is `"system"`, `systemMode` follows OS preference live.
 */
export function ModeToggle() {
  const { mode, systemMode, setMode } = useColorScheme();

  // `mode`/`systemMode` resolve one tick after mount (MUI CssVarsProvider);
  // skip rendering until resolved so we never show the wrong icon/label.
  if (!mode) {
    return null;
  }

  const resolvedMode = mode === "system" ? systemMode : mode;
  const isDark = resolvedMode === "dark";

  return (
    <IconButton
      onClick={() => setMode(isDark ? "light" : "dark")}
      color="inherit"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? <LightModeIcon /> : <DarkModeIcon />}
    </IconButton>
  );
}
