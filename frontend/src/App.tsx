/**
 * Routeur principal de Petrix.
 * Déclare toutes les routes de l'application avec chargement différé (lazy/Suspense),
 * et protège les routes via trois gardes RBAC : ProtectedRoute, AuditorRoute, AdminRoute.
 */
import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import Layout from '@/components/layout/Layout';

const LoginPage           = lazy(() => import('@/pages/auth/LoginPage'));
const SignupPage           = lazy(() => import('@/pages/auth/SigninPage'));
const ChangePasswordPage   = lazy(() => import('@/pages/auth/ChangePasswordPage'));
const HomePage             = lazy(() => import('@/pages/HomePage'));
const DashboardPage        = lazy(() => import('@/pages/DashboardPage'));
const AssetsPage           = lazy(() => import('@/pages/assets/AssetsPage'));
const VulnerabilitiesPage  = lazy(() => import('@/pages/vulnerabilities/VulnerabilitiesPage'));
const SettingsPage         = lazy(() => import('@/pages/settings/SettingsPage'));
const UsersPage            = lazy(() => import('@/pages/users/UsersPage'));
const HardeningPage        = lazy(() => import('@/pages/hardening/HardeningPage'));
const AuditReportPage      = lazy(() => import('@/pages/audit-report/AuditReportPage'));
const AuditLogsPage        = lazy(() => import('@/pages/audit/AuditLogsPage'));
const SupportPage          = lazy(() => import('@/pages/support/SupportPage'));

const Spinner = () => (
  <div className="flex items-center justify-center h-screen bg-gray-950 text-white">
    Chargement…
  </div>
);

// ─── Route guards ─────────────────────────────────────────────────────────────

/**
 * Garde de route pour tout utilisateur authentifié.
 * Redirige vers /login si la session est absente, sinon enveloppe la page dans le Layout applicatif.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore(s => s.isAuthenticated);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

/**
 * Garde de route réservée aux administrateurs.
 * Redirige vers /login si non connecté, vers /dashboard si le rôle est insuffisant.
 */
function AdminRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== 'admin') return <Navigate to="/dashboard" replace />;
  return <Layout>{children}</Layout>;
}

/**
 * Garde de route accessible aux rôles admin et auditor.
 * Redirige les autres profils connectés vers /dashboard.
 */
function AuditorRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, user } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!['admin', 'auditor'].includes(user?.role ?? '')) return <Navigate to="/dashboard" replace />;
  return <Layout>{children}</Layout>;
}

// ─── App ──────────────────────────────────────────────────────────────────────

/**
 * Composant racine : définit la table de routage complète de l'application
 * avec chargement différé de chaque page et un fallback Spinner pendant la résolution.
 */
function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        {/* Public */}
        <Route path="/"    element={<HomePage />} />
        <Route path="/login"  element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Tous les utilisateurs connectés */}
        <Route path="/change-password" element={<ProtectedRoute><ChangePasswordPage /></ProtectedRoute>} />
        <Route path="/dashboard"        element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
        <Route path="/assets"           element={<ProtectedRoute><AssetsPage /></ProtectedRoute>} />
        <Route path="/hardening"        element={<ProtectedRoute><HardeningPage /></ProtectedRoute>} />
        <Route path="/audit"            element={<ProtectedRoute><AuditReportPage /></ProtectedRoute>} />
        <Route path="/audit/:sessionId" element={<ProtectedRoute><AuditReportPage /></ProtectedRoute>} />
        <Route path="/vulnerabilities"  element={<ProtectedRoute><VulnerabilitiesPage /></ProtectedRoute>} />
        <Route path="/settings"         element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
        <Route path="/support"          element={<ProtectedRoute><SupportPage /></ProtectedRoute>} />

        {/* Auditeurs + Admins */}
        <Route path="/audit-logs" element={<AuditorRoute><AuditLogsPage /></AuditorRoute>} />

        {/* Admins uniquement */}
        <Route path="/users" element={<AdminRoute><UsersPage /></AdminRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
