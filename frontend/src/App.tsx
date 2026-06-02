import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import Layout from '@/components/layout/Layout';
import LoginPage from '@/pages/auth/LoginPage';
import SignupPage from '@/pages/auth/SigninPage';
import ChangePasswordPage from '@/pages/auth/ChangePasswordPage';
import HomePage from '@/pages/HomePage';
import DashboardPage from '@/pages/DashboardPage';
import AssetsPage from '@/pages/assets/AssetsPage';
import VulnerabilitiesPage from '@/pages/vulnerabilities/VulnerabilitiesPage';
import ScansPage from '@/pages/scans/ScansPage';
import SettingsPage from '@/pages/settings/SettingsPage';
import UsersPage from '@/pages/users/UsersPage';
import { SMSIPage } from '@/pages/smsi/SMSIPage';
import { ClientsPage } from '@/pages/clients/ClientsPage';
import PentestPage from '@/pages/pentest/PentestPage';
import PentestSessionDetail from '@/pages/pentest/PentestSessionDetail';
import HardeningPage from '@/pages/hardening/HardeningPage';
import AuditLogsPage from '@/pages/audit/AuditLogsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <Routes>
      
      <Route path="/" element={<HomePage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/change-password" element={<ChangePasswordPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/assets"
        element={
          <ProtectedRoute>
            <AssetsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/vulnerabilities"
        element={
          <ProtectedRoute>
            <VulnerabilitiesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scans"
        element={
          <ProtectedRoute>
            <ScansPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pentest"
        element={
          <ProtectedRoute>
            <PentestPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/pentest/session/:id"
        element={
          <ProtectedRoute>
            <PentestSessionDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hardening"
        element={
          <ProtectedRoute>
            <HardeningPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/smsi"
        element={
          <ProtectedRoute>
            <SMSIPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/clients"
        element={
          <ProtectedRoute>
            <ClientsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute>
            <UsersPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/audit-logs"
        element={
          <ProtectedRoute>
            <AuditLogsPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
