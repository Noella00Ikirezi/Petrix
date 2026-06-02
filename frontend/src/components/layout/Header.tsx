import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, LogOut, User, Settings, ChevronDown } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/client';

const ROLE_COLORS: Record<string, string> = {
  admin:   'bg-red-500',
  auditor: 'bg-purple-500',
  analyst: 'bg-blue-500',
  viewer:  'bg-gray-500',
};

function Avatar({ user }: { user: { first_name: string | null; last_name: string | null; email: string; role: string } | null }) {
  const initials = user
    ? user.first_name && user.last_name
      ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
      : user.first_name
      ? user.first_name[0].toUpperCase()
      : user.email[0].toUpperCase()
    : '?';

  const color = ROLE_COLORS[user?.role || ''] || 'bg-primary-500';

  return (
    <div className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold text-white ${color}`}>
      {initials}
    </div>
  );
}

export default function Header() {
  const [isDark, setIsDark] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    setIsDark(isDarkMode);
    if (isDarkMode) document.documentElement.classList.add('dark');
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

  const toggleDarkMode = () => {
    const newValue = !isDark;
    setIsDark(newValue);
    localStorage.setItem('darkMode', String(newValue));
    document.documentElement.classList.toggle('dark', newValue);
  };

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
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex-1" />

      <div className="flex items-center gap-4">
        {/* Dark mode */}
        <button
          onClick={toggleDarkMode}
          className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Notifications */}
        <button className="relative rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700">
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* Avatar + menu */}
        <div className="relative border-l border-gray-200 pl-4 dark:border-gray-700" ref={menuRef}>
          <button
            onClick={() => setMenuOpen((v) => !v)}
            className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <Avatar user={user} />
            <div className="hidden text-left sm:block">
              <p className="text-sm font-medium text-gray-900 dark:text-white leading-tight">
                {displayName}
              </p>
              <p className="text-xs capitalize text-gray-500 dark:text-gray-400">
                {user?.role}
              </p>
            </div>
            <ChevronDown className="h-4 w-4 text-gray-400" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-full mt-2 w-52 rounded-lg border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800 z-50">
              {/* Info utilisateur */}
              <div className="border-b border-gray-100 px-4 py-3 dark:border-gray-700">
                <p className="font-medium text-gray-900 dark:text-white text-sm">{displayName}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{user?.email}</p>
                <span className="mt-1 inline-block rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium capitalize text-primary-700 dark:bg-primary-900/50 dark:text-primary-300">
                  {user?.role}
                </span>
              </div>

              {/* Actions */}
              <div className="p-1">
                <button
                  onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  <User className="h-4 w-4" />
                  Mon profil
                </button>
                <button
                  onClick={() => { setMenuOpen(false); navigate('/settings'); }}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                >
                  <Settings className="h-4 w-4" />
                  Paramètres
                </button>
              </div>

              <div className="border-t border-gray-100 p-1 dark:border-gray-700">
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
                >
                  <LogOut className="h-4 w-4" />
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
