import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Moon, Sun, Bell, LogOut, User } from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

export default function Header() {
  const [isDark, setIsDark] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  useEffect(() => {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    setIsDark(isDarkMode);
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleDarkMode = () => {
    const newValue = !isDark;
    setIsDark(newValue);
    localStorage.setItem('darkMode', String(newValue));
    document.documentElement.classList.toggle('dark', newValue);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 dark:border-gray-700 dark:bg-gray-800">
      {/* Search placeholder */}
      <div className="flex-1">
        {/* Add search bar here later */}
      </div>

      {/* Actions */}
      <div className="flex items-center gap-4">
        {/* Dark mode toggle */}
        <button
          onClick={toggleDarkMode}
          className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          title={isDark ? 'Light mode' : 'Dark mode'}
        >
          {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>

        {/* Notifications */}
        <button
          className="relative rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
          title="Notifications"
        >
          <Bell className="h-5 w-5" />
          <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
        </button>

        {/* User menu */}
        <div className="flex items-center gap-3 border-l border-gray-200 pl-4 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-primary-700 dark:bg-primary-900 dark:text-primary-300">
              <User className="h-4 w-4" />
            </div>
            <div className="hidden sm:block">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {user?.first_name || user?.email?.split('@')[0]}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {user?.role}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="rounded-md p-2 text-gray-500 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-700"
            title="Logout"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
