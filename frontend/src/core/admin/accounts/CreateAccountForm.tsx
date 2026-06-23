import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Select from "@mui/material/Select";
import MenuItem from "@mui/material/MenuItem";
import InputLabel from "@mui/material/InputLabel";
import FormControl from "@mui/material/FormControl";
import { apiClient } from "../../../api";
import type { UserType, CreateAccountRequest } from "../../../api/generated/openapi";

interface CreateAccountFormProps {
  isSysadmin: boolean;
}

type FieldErrors = Partial<Record<string, string>>;

export function CreateAccountForm({ isSysadmin }: CreateAccountFormProps) {
  const [firstName, setFirstName] = useState("");
  const [surname, setSurname] = useState("");
  const [email, setEmail] = useState("");
  const [userType, setUserType] = useState<UserType | "">("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (data: CreateAccountRequest) => apiClient.createAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setFirstName("");
      setSurname("");
      setEmail("");
      setUserType("");
      setFieldErrors({});
    },
    onError: (err: unknown) => {
      const problem = (err as { problem?: { errors?: Array<{ field: string; message: string }> } }).problem;
      if (problem?.errors) {
        const errs: FieldErrors = {};
        for (const e of problem.errors) {
          errs[e.field] = e.message;
        }
        setFieldErrors(errs);
      }
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userType) return;
    setFieldErrors({});
    mutation.mutate({ firstName, surname, email, userType });
  }

  const isDisabled = !firstName.trim() || !surname.trim() || !email.trim() || !userType;

  return (
    <Box
      component="form"
      onSubmit={handleSubmit}
      sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 3, maxWidth: 400 }}
    >
      <Typography variant="h6">Create Account</Typography>
      <TextField
        label="First name"
        id="create-first-name"
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
        required
      />
      <TextField
        label="Surname"
        id="create-surname"
        value={surname}
        onChange={(e) => setSurname(e.target.value)}
        required
      />
      <TextField
        label="Email"
        id="create-email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        error={!!fieldErrors.email}
        helperText={fieldErrors.email}
      />
      <FormControl required>
        <InputLabel id="user-type-label">User Type</InputLabel>
        <Select
          labelId="user-type-label"
          label="User Type"
          id="user-type-select"
          value={userType}
          onChange={(e) => setUserType(e.target.value as UserType)}
        >
          <MenuItem value="patient">Patient</MenuItem>
          <MenuItem value="doctor">Doctor</MenuItem>
          <MenuItem value="admin">Administrator</MenuItem>
          {isSysadmin && (
            <MenuItem value="sysadmin">System Administrator</MenuItem>
          )}
        </Select>
      </FormControl>
      <Button
        type="submit"
        variant="contained"
        disabled={isDisabled || mutation.isPending}
      >
        Create Account
      </Button>
    </Box>
  );
}
