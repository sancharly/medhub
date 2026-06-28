import List from "@mui/material/List";
import ListItem from "@mui/material/ListItem";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";
import type { Appointment } from "../../api/generated/types";
import { PatientActions } from "./PatientActions";

interface AppointmentListProps {
  appointments: Appointment[];
  isPatient: boolean;
}

const STATUS_COLOR: Record<string, "default" | "success" | "error" | "warning"> = {
  PENDING: "warning",
  CONFIRMED: "success",
  DECLINED: "error",
};

export function AppointmentList({ appointments, isPatient }: AppointmentListProps) {
  return (
    <List>
      {appointments.map((appt) => (
        <ListItem
          key={appt.id}
          sx={{ flexDirection: "column", alignItems: "flex-start" }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1, width: "100%" }}>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="body1">
                Dr. {appt.doctorId} — Patient {appt.patientId}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(appt.scheduledAt).toLocaleString()}
              </Typography>
            </Box>
            <Chip
              label={appt.state}
              color={STATUS_COLOR[appt.state] ?? "default"}
              size="small"
            />
          </Box>
          {isPatient && <PatientActions appointment={appt} />}
        </ListItem>
      ))}
    </List>
  );
}
