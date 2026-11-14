// One module for both admin pages, so a dynamic import of it yields one chunk (TASK-145).
export { AccountsPage } from "./accounts";
export { GroupsPage } from "./groups";
