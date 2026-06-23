import { useNavigate } from "react-router-dom";
import ListItem from "@mui/material/ListItem";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import type { PatientSummary } from "../../api/generated/openapi";

interface PatientRowProps {
  patient: PatientSummary;
}

export function PatientRow({ patient }: PatientRowProps) {
  const navigate = useNavigate();

  const secondary = patient.dateOfBirth
    ? `DOB: ${patient.dateOfBirth}`
    : undefined;

  return (
    <ListItem disablePadding>
      <ListItemButton
        onClick={() => navigate(`/patients/${patient.id}/clinical-entries`)}
      >
        <ListItemText
          primary={`${patient.firstName} ${patient.surname}`}
          secondary={secondary}
        />
      </ListItemButton>
    </ListItem>
  );
}
