import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import { apiClient } from "../../api";
import { useConfirm } from "../confirm/useConfirm";
import type { Appointment } from "../../api/generated/openapi";

interface PatientActionsProps {
  appointment: Appointment;
}

export function PatientActions({ appointment }: PatientActionsProps) {
  const confirm = useConfirm();
  const queryClient = useQueryClient();

  const confirmMutation = useMutation({
    mutationFn: () => apiClient.confirmAppointment(appointment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });

  const declineMutation = useMutation({
    mutationFn: () => apiClient.declineAppointment(appointment.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
    },
  });

  // Patient can confirm PENDING appointments
  const canConfirm = appointment.status === "PENDING";
  // Patient can decline PENDING or CONFIRMED appointments
  const canDecline = appointment.status === "PENDING" || appointment.status === "CONFIRMED";

  async function handleDecline() {
    const ok = await confirm({
      title: "Decline appointment",
      description: "Are you sure you want to decline this appointment?",
      destructive: true,
    });
    if (ok) {
      declineMutation.mutate();
    }
  }

  return (
    <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
      {canConfirm && (
        <Button
          size="small"
          variant="contained"
          color="success"
          onClick={() => confirmMutation.mutate()}
          disabled={confirmMutation.isPending}
        >
          Confirm
        </Button>
      )}
      {canDecline && (
        <Button
          size="small"
          variant="outlined"
          color="error"
          onClick={handleDecline}
          disabled={declineMutation.isPending}
        >
          Decline
        </Button>
      )}
    </Box>
  );
}
