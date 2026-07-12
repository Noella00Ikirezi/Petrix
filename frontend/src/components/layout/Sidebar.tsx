/**
 * Barre de navigation latérale de l'application.
 * Affiche le logo Petrix et les liens de navigation filtrés selon le rôle RBAC de l'utilisateur.
 * Sur mobile, est contrôlée par la prop `isOpen` via une classe CSS.
 */
import { NavLink, Link } from 'react-router-dom';
import {
  LayoutDashboard, Server, Shield, ShieldCheck, FileBarChart2,
  Users, Settings, ClipboardList, HelpCircle,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

/**
 * Sidebar de navigation RBAC.
 * @param isOpen - Indique si la sidebar est visible sur mobile (classe `sidebar-open`).
 */
export default function Sidebar({ isOpen }: { isOpen?: boolean }) {
  const user = useAuthStore(s => s.user);
  const role = user?.role ?? '';
  const isAdmin   = role === 'admin';
  const isAuditor = role === 'auditor' || isAdmin;

  const nav = [
    // ── Principal ──────────────────────────────────────────────
    { name: 'Dashboard',       href: '/dashboard',       icon: LayoutDashboard, show: true },
    { name: 'Systèmes',        href: '/assets',          icon: Server,          show: true },
    { name: 'Hardening',       href: '/hardening',       icon: ShieldCheck,     show: true },
    { name: "Rapport d'audit", href: '/audit',           icon: FileBarChart2,   show: true },
    { name: 'Vulnérabilités',  href: '/vulnerabilities', icon: Shield,          show: true },
    // ── Administration ─────────────────────────────────────────
    { name: 'Utilisateurs',    href: '/users',           icon: Users,           show: isAdmin },
    { name: 'Audit Logs',      href: '/audit-logs',      icon: ClipboardList,   show: isAuditor },
    // ── Commun ─────────────────────────────────────────────────
    { name: 'Support',         href: '/support',         icon: HelpCircle,      show: true },
    { name: 'Paramètres',      href: '/settings',        icon: Settings,        show: true },
  ].filter(item => item.show);

  return (
    <div
      className={`app-sidebar${isOpen ? ' sidebar-open' : ''}`}
      style={{
        display: 'flex', flexDirection: 'column', height: '100%', width: 220,
        background: 'var(--panel)', borderRight: '1px solid var(--line)',
      }}
    >
      {/* Logo */}
      <Link
        to="/"
        style={{
          display: 'flex', alignItems: 'center', gap: 10, height: 64,
          borderBottom: '1px solid var(--line)', padding: '0 20px',
          textDecoration: 'none', transition: 'opacity .15s',
        }}
        onMouseEnter={e => (e.currentTarget.style.opacity = '.7')}
        onMouseLeave={e => (e.currentTarget.style.opacity = '1')}
      >
        <img src="/logo-petrix-dark.svg" alt="Petrix" style={{ height: 28, width: 28 }} />
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, letterSpacing: '.08em', color: 'var(--text)' }}>
          &lt;PETRIX <span style={{ color: 'var(--lime)' }}>/&gt;</span>
        </span>
      </Link>

      {/* Navigation */}
      <nav style={{ flex: 1, overflowY: 'auto', padding: '16px 12px' }}>
        {nav.map((item, idx) => {
          // Séparateur visuel avant la section administration
          const isAdminSection = item.href === '/users';
          const isSupportSection = item.href === '/support';
          return (
            <div key={item.name}>
              {(isAdminSection || isSupportSection) && (
                <div style={{ borderTop: '1px solid var(--line)', margin: '8px 0 8px' }} />
              )}
              <NavLink
                to={item.href}
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '9px 12px', marginBottom: 2,
                  fontSize: 11, letterSpacing: '.15em', textTransform: 'uppercase',
                  textDecoration: 'none',
                  color: 'var(--lime)',
                  background: isActive ? 'color-mix(in srgb, var(--lime) 10%, transparent)' : 'transparent',
                  borderLeft: isActive ? '2px solid var(--lime)' : '2px solid transparent',
                  opacity: isActive ? 1 : 0.65,
                  transition: 'opacity .15s, background .15s, border-color .15s',
                })}
                onMouseEnter={e => { (e.currentTarget as HTMLElement).style.opacity = '1'; }}
                onMouseLeave={e => {
                  const el = e.currentTarget as HTMLElement;
                  if (!el.getAttribute('aria-current')) el.style.opacity = '0.65';
                }}
              >
                {({ isActive: _isActive }) => (
                  <>
                    <item.icon size={14} style={{ color: 'var(--lime)', flexShrink: 0 }} />
                    <span style={{ fontVariantNumeric: 'tabular-nums' }}>
                      <span style={{ color: 'var(--lime)', marginRight: 4, fontSize: 10, opacity: 0.45 }}>
                        {String(idx + 1).padStart(2, '0')}
                      </span>
                      {item.name}
                    </span>
                  </>
                )}
              </NavLink>
            </div>
          );
        })}
      </nav>

      {/* Footer version + rôle */}
      <div style={{ borderTop: '1px solid var(--line)', padding: '12px 20px' }}>
        <span style={{ fontSize: 10, letterSpacing: '.2em', color: 'var(--faint)', textTransform: 'uppercase', display: 'block' }}>
          // v0.2.0
        </span>
        {role && (
          <span style={{ fontSize: 10, color: 'var(--lime)', opacity: 0.65, textTransform: 'uppercase', letterSpacing: '.1em' }}>
            {role}
          </span>
        )}
      </div>
    </div>
  );
}
