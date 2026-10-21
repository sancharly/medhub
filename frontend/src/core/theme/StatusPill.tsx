import Chip from "@mui/material/Chip";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import ErrorIcon from "@mui/icons-material/Error";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

export type StatusPillSeverity = "success" | "warning" | "error" | "info";

export interface StatusPillProps {
  severity: StatusPillSeverity;
  label: string;
}

const SEVERITY_ICON: Record<StatusPillSeverity, typeof CheckCircleIcon> = {
  success: CheckCircleIcon,
  warning: WarningAmberIcon,
  error: ErrorIcon,
  info: InfoOutlinedIcon,
};

/**
 * Tinted status pill: background + text tint + a leading icon per severity,
 * so state is never conveyed by color alone (SR-038 AC-4).
 */
export function StatusPill({ severity, label }: StatusPillProps) {
  const Icon = SEVERITY_ICON[severity];
  return (
    <Chip
      icon={<Icon fontSize="small" />}
      label={label}
      size="small"
      sx={(theme) => {
        const pill = theme.vars.palette.statusPill[severity];
        return {
          bgcolor: pill.bg,
          color: pill.text,
          "& .MuiChip-icon": { color: pill.text },
        };
      }}
    />
  );
}
