import { BrowserRouter, Routes, Route } from "react-router-dom";
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
                <Route element={<RequireAuth />}>
                  <Route element={<ForcedPasswordGate />}>
                    <Route
                      element={
                        <SessionActivityProvider>
                          <AppErrorBoundary>
                            <AppLayout navigation={<div />}>
                              <Routes>
                                <Route
                                  path="/password"
                                  element={<ChangePasswordPage />}
                                />
                                <Route
                                  path="/*"
                                  element={
                                    <div>App shell - phase 7</div>
                                  }
                                />
                              </Routes>
                            </AppLayout>
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
