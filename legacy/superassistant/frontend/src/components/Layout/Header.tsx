import { Bell, Moon, Sun } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center flex-1">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Bienvenue
        </h1>
      </div>

      <div className="flex items-center space-x-4">
        <button
          onClick={toggleDarkMode}
          className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <div className="flex items-center">
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-bold">
            U
          </div>
        </div>
      </div>
    </header>
  );
}
