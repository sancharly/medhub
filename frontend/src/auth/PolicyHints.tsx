import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import ListItemText from "@mui/material/ListItemText";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import RadioButtonUncheckedIcon from "@mui/icons-material/RadioButtonUnchecked";
import { passwordHints } from "./passwordHints";

interface PolicyHintsProps {
  password: string;
  email?: string;
}

interface HintItem {
  label: string;
  met: boolean;
  serverOnly?: boolean;
}

export function PolicyHints({ password, email = "" }: PolicyHintsProps) {
  const hints: HintItem[] = [
    { label: "At least 12 characters", met: passwordHints.checkLength(password) },
    {
      label: "Upper and lowercase letters, digits, and special characters",
      met: passwordHints.checkClasses(password),
    },
    {
      label: "Does not contain your email address",
      met: passwordHints.checkSubstring(password, email),
    },
    {
      label: "Not one of your last 12 passwords (checked on submit by server)",
      met: false,
      serverOnly: true,
    },
  ];

  return (
    <Box>
      <Typography variant="caption" color="text.secondary">
        Password requirements (checked on submit by server):
      </Typography>
      <List dense disablePadding>
        {hints.map((hint) => (
          <ListItem key={hint.label} disableGutters>
            <ListItemIcon sx={{ minWidth: 28 }}>
              {!hint.serverOnly && hint.met ? (
                <CheckCircleOutlinedIcon fontSize="small" color="success" />
              ) : (
                <RadioButtonUncheckedIcon fontSize="small" color="disabled" />
              )}
            </ListItemIcon>
            <ListItemText
              primary={<Typography variant="caption">{hint.label}</Typography>}
            />
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
