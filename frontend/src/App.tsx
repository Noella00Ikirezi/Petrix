import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import Layout from '@/components/layout/Layout';

const LoginPage        = lazy(() => import('@/pages/auth/LoginPage'));
const SignupPage        = lazy(() => import('@/pages/auth/SigninPage'));
const ChangePasswordPage = lazy(() => import('@/pages/auth/ChangePasswordPage'));
const HomePage          = lazy(() => import('@/pages/HomePage'));
const DashboardPage     = lazy(() => import('@/pages/DashboardPage'));

const AssetsPage        = lazy(() => import('@/pages/assets/AssetsPage'));
const VulnerabilitiesPage = lazy(() => import('@/pages/vulnerabilities/VulnerabilitiesPage'));
const ScansPage         = lazy(() => import('@/pages/scans/ScansPage'));
const SettingsPage      = lazy(() => import('@/pages/settings/SettingsPage'));
const UsersPage         = lazy(() => import('@/pages/users/UsersPage'));
const HardeningPage     = lazy(() => import('@/pages/hardening/HardeningPage'));
const AuditLogsPage     = lazy(() => import('@/pages/audit/AuditLogsPage'));
const AgentPage         = lazy(() => import('@/pages/agent/AgentPage'));

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

function App() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-screen bg-gray-950 text-white">Chargement…</div>}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/change-password" element={<ChangePasswordPage />} />
        <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/assets" element={<ProtectedRoute><AssetsPage /></ProtectedRoute>} />
        <Route path="/vulnerabilities" element={<ProtectedRoute><VulnerabilitiesPage /></ProtectedRoute>} />
        <Route path="/scans" element={<ProtectedRoute><ScansPage /></ProtectedRoute>} />
        <Route path="/hardening" element={<ProtectedRoute><HardeningPage /></ProtectedRoute>} />
        <Route path="/agent" element={<ProtectedRoute><AgentPage /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="/users" element={<ProtectedRoute><UsersPage /></ProtectedRoute>} />
        <Route path="/audit-logs" element={<ProtectedRoute><AuditLogsPage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
