import Table from "@mui/material/Table";
import TableHead from "@mui/material/TableHead";
import TableBody from "@mui/material/TableBody";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Chip from "@mui/material/Chip";
import type { AccountSummary } from "../../../api/generated/openapi";
import { LifecycleActions } from "./LifecycleActions";

interface AccountListProps {
  accounts: AccountSummary[];
  isSysadmin: boolean;
  actingUserId: string;
}

const STATE_COLOR: Record<string, "default" | "success" | "error" | "warning"> = {
  ACTIVE: "success",
  INACTIVE: "warning",
  DELETED: "error",
};

export function AccountList({ accounts, isSysadmin, actingUserId }: AccountListProps) {
  return (
    <Table>
      <TableHead>
        <TableRow>
          <TableCell>Name</TableCell>
          <TableCell>Email</TableCell>
          <TableCell>Role</TableCell>
          <TableCell>Status</TableCell>
          {isSysadmin && <TableCell>Actions</TableCell>}
        </TableRow>
      </TableHead>
      <TableBody>
        {accounts.map((account) => (
          <TableRow key={account.id}>
            <TableCell>{account.firstName} {account.surname}</TableCell>
            <TableCell>{account.email}</TableCell>
            <TableCell>{account.userType}</TableCell>
            <TableCell>
              <Chip
                label={account.state}
                color={STATE_COLOR[account.state] ?? "default"}
                size="small"
              />
            </TableCell>
            {isSysadmin && (
              <TableCell>
                <LifecycleActions
                  account={account}
                  isSelf={account.id === actingUserId}
                />
              </TableCell>
            )}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
