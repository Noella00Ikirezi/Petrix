/**
 * Barre de navigation supérieure de l'application.
 * Contient le bouton hamburger mobile, le toggle dark/light mode, les notifications
 * et le menu déroulant utilisateur (profil, déconnexion).
 */
import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, LogOut, User, Settings, ChevronDown, Menu } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/client';

const ROLE_COLORS: Record<string, string> = {
  admin:   'bg-red-500',
  auditor: 'bg-purple-500',
  analyst: 'bg-blue-500',
  viewer:  'bg-gray-500',
};

/**
 * Avatar utilisateur : affiche la photo de profil si disponible,
 * sinon un cercle coloré selon le rôle avec les initiales de l'utilisateur.
 */
function Avatar({ user }: { user: { first_name: string | null; last_name: string | null; email: string; role: string; avatar_url?: string | null } | null }) {
  const initials = user
    ? user.first_name && user.last_name
      ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
      : user.first_name
      ? user.first_name[0].toUpperCase()
      : user.email[0].toUpperCase()
    : '?';

  const color = ROLE_COLORS[user?.role || ''] || 'bg-primary-500';

  if (user?.avatar_url) {
    return (
      <img
        src={user.avatar_url}
        alt={user.first_name || 'Avatar'}
        className="h-8 w-8 rounded-full object-cover ring-2 ring-primary-500/30"
      />
    );
  }

  return (
    <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold text-white ${color}`}>
      {initials}
    </div>
  );
}

/**
 * En-tête principal de l'application.
 * @param onMenuClick - Callback déclenché par le bouton hamburger pour basculer la sidebar mobile.
 */
export default function Header({ onMenuClick }: { onMenuClick?: () => void }) {
  const [isDark, setIsDark] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    const isDarkMode = localStorage.getItem('darkMode') !== 'false';
    setIsDark(isDarkMode);
    document.documentElement.classList.toggle('dark', isDarkMode);
  }, []);

  // Fermer le menu si clic en dehors
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  /** Bascule le thème sombre/clair et persiste le choix dans localStorage. */
  const toggleDarkMode = () => {
    const newValue = !isDark;
    setIsDark(newValue);
    localStorage.setItem('darkMode', String(newValue));
    document.documentElement.classList.toggle('dark', newValue);
  };

  /** Invalide la session côté serveur puis vide le store et redirige vers /login. */
  const handleLogout = async () => {
    setMenuOpen(false);
    await authApi.logout();
    logout();
    navigate('/login');
  };

  const displayName = user?.first_name
    ? `${user.first_name}${user.last_name ? ' ' + user.last_name : ''}`
    : user?.email?.split('@')[0] || '';

  return (
    <header style={{ display: 'flex', height: 64, alignItems: 'center', justifyContent: 'space-between', background: 'var(--panel)', borderBottom: '1px solid var(--line)', padding: '0 16px' }}>
      {/* Hamburger — mobile only */}
      <button
        className="sidebar-toggle-btn"
        onClick={onMenuClick}
        style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 36, height: 36, background: 'none', border: '1px solid var(--line)', cursor: 'pointer', color: 'var(--dim)' }}
        aria-label="Menu"
      >
        <Menu size={18} />
      </button>
      <div className="flex-1" />

      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          title={isDark ? 'Light mode' : 'Dark mode'}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: 34, height: 34, background: 'none', border: '1px solid transparent', borderRadius: 3, cursor: 'pointer', color: 'var(--dim)', transition: 'color .15s, border-color .15s' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = 'var(--lime)'; (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'var(--dim)'; (e.currentTarget as HTMLElement).style.borderColor = 'transparent'; }}
        >
          {isDark ? <Sun size={16} /> : <Moon size={16} />}
        </button>

        {/* Notifications */}
        <button
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', width: 34, height: 34, background: 'none', border: '1px solid transparent', borderRadius: 3, cursor: 'pointer', color: 'var(--dim)', transition: 'color .15s, border-color .15s' }}
          onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color = 'var(--lime)'; (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)'; }}
          onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color = 'var(--dim)'; (e.currentTarget as HTMLElement).style.borderColor = 'transparent'; }}
        >
          <Bell size={16} />
          <span style={{ position: 'absolute', top: 6, right: 6, width: 6, height: 6, borderRadius: '50%', background: '#ef4444' }} />
        </button>

        {/* Avatar + menu */}
        <div style={{ position: 'relative', borderLeft: '1px solid var(--line)', paddingLeft: 12, marginLeft: 4 }} ref={menuRef}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 8px', background: 'none', border: '1px solid transparent', borderRadius: 3, cursor: 'pointer', transition: 'border-color .15s, background .15s' }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--line)'; (e.currentTarget as HTMLElement).style.background = 'var(--panel-hi)'; }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'transparent'; (e.currentTarget as HTMLElement).style.background = 'none'; }}
          >
            <Avatar user={user} />
            <div style={{ textAlign: 'left' }} className="hidden sm:block">
              <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', lineHeight: 1.3, margin: 0 }}>
                {displayName}
              </p>
              <p style={{ fontSize: 11, color: 'var(--faint)', margin: 0, textTransform: 'capitalize', letterSpacing: '.04em' }}>
                {user?.role}
              </p>
            </div>
            <ChevronDown size={14} style={{ color: 'var(--faint)' }} />
          </button>

          {menuOpen && (
            <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 6px)', width: 208, zIndex: 50, background: 'var(--panel)', border: '1px solid var(--line)' }}>
              {/* Info utilisateur */}
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--line)' }}>
                <p style={{ fontWeight: 600, color: 'var(--text)', fontSize: 13, margin: 0 }}>{displayName}</p>
                <p style={{ fontSize: 11, color: 'var(--faint)', margin: '2px 0 6px' }}>{user?.email}</p>
                <span style={{ display: 'inline-block', padding: '2px 8px', fontSize: 10, fontWeight: 700, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--lime)', background: 'color-mix(in srgb, var(--lime) 10%, transparent)', border: '1px solid color-mix(in srgb, var(--lime) 30%, transparent)', borderRadius: 2 }}>
                  {user?.role}
                </span>
              </div>

              {/* Actions */}
              <div style={{ padding: 4 }}>
                {[
                  { label: 'Mon profil', icon: User, onClick: () => { setMenuOpen(false); navigate('/settings'); } },
                  { label: 'Paramètres', icon: Settings, onClick: () => { setMenuOpen(false); navigate('/settings'); } },
                ].map(({ label, icon: Icon, onClick }) => (
                  <button
                    key={label}
                    onClick={onClick}
                    style={{ display: 'flex', width: '100%', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'none', border: 'none', borderRadius: 2, cursor: 'pointer', fontSize: 12, color: 'var(--dim)', transition: 'background .1s, color .1s' }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--panel-hi)'; (e.currentTarget as HTMLElement).style.color = 'var(--text)'; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; (e.currentTarget as HTMLElement).style.color = 'var(--dim)'; }}
                  >
                    <Icon size={14} />
                    {label}
                  </button>
                ))}
              </div>

              <div style={{ padding: 4, borderTop: '1px solid var(--line)' }}>
                <button
                  onClick={handleLogout}
                  style={{ display: 'flex', width: '100%', alignItems: 'center', gap: 10, padding: '8px 12px', background: 'none', border: 'none', borderRadius: 2, cursor: 'pointer', fontSize: 12, color: '#ef4444', transition: 'background .1s' }}
                  onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(239,68,68,.08)'; }}
                  onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'none'; }}
                >
                  <LogOut size={14} />
                  Déconnexion
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
