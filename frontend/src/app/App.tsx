import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "../core/theme/ThemeProvider";
import { QueryProvider } from "../api/QueryProvider";
import { ConfirmProvider } from "../core/confirm/ConfirmProvider";
import { ErrorToastProvider } from "../core/error/ErrorToastProvider";
import { LoginPage } from "../auth/LoginPage";
import { ActivationPage } from "../auth/ActivationPage";
import { RequireAuth } from "../auth/RequireAuth";
import { ForcedPasswordGate } from "../auth/ForcedPasswordGate";
import { SessionActivityProvider } from "../auth/SessionActivityProvider";
import { AppErrorBoundary } from "../core/error/AppErrorBoundary";
import { ChangePasswordPage } from "../auth/ChangePasswordPage";
import { AppLayout } from "../core/layout/AppLayout";
import { AppNavigation } from "../core/nav/AppNavigation";
import { ProfilePage } from "../core/profile";
import { PatientListPage } from "../core/patients";
import { ClinicalEntriesPage } from "../core/clinical";
import { AppointmentsPage } from "../core/appointments";
import { ConsentPage } from "../core/consent";
import { AccountsPage } from "../core/admin/accounts";
import { GroupsPage } from "../core/admin/groups";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api";
import { routeRoles, type RoutePath } from "../core/nav/routeRoles";
import { RequireRole } from "./RequireRole";

function guarded(path: RoutePath, element: React.ReactElement) {
  return <RequireRole roles={routeRoles[path]}>{element}</RequireRole>;
}

function AuthenticatedApp() {
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiClient.me(),
  });

  return (
    <AppLayout navigation={me ? <AppNavigation userType={me.userType} /> : null}>
      <Routes>
        <Route path="/password" element={guarded("/password", <ChangePasswordPage />)} />
        <Route path="/profile" element={guarded("/profile", <ProfilePage />)} />
        <Route path="/patients" element={guarded("/patients", <PatientListPage />)} />
        <Route
          path="/patients/:patientId/clinical-entries"
          element={guarded(
            "/patients/:patientId/clinical-entries",
            <ClinicalEntriesPage
              userType={
                me?.userType === "DOCTOR" || me?.userType === "PATIENT" ? me.userType : "PATIENT"
              }
            />
          )}
        />
        <Route path="/appointments" element={guarded("/appointments", <AppointmentsPage />)} />
        <Route path="/consent" element={guarded("/consent", <ConsentPage />)} />
        <Route path="/admin/accounts" element={guarded("/admin/accounts", <AccountsPage />)} />
        <Route path="/admin/groups" element={guarded("/admin/groups", <GroupsPage />)} />
        <Route path="/*" element={<Navigate to="/profile" replace />} />
      </Routes>
    </AppLayout>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <QueryProvider>
        <ConfirmProvider>
          <ErrorToastProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/activation/:token" element={<ActivationPage />} />
                <Route path="*" element={<RequireAuth />}>
                  <Route path="*" element={<ForcedPasswordGate />}>
                    <Route
                      path="*"
                      element={
                        <SessionActivityProvider>
                          <AppErrorBoundary>
                            <AuthenticatedApp />
                          </AppErrorBoundary>
                        </SessionActivityProvider>
                      }
                    />
                  </Route>
                </Route>
              </Routes>
            </BrowserRouter>
          </ErrorToastProvider>
        </ConfirmProvider>
      </QueryProvider>
    </ThemeProvider>
  );
}
