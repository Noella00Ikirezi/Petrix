import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  Target,
  Calendar,
  FileText,
  Book,
  Settings,
  Bot,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Tâches', href: '/tasks', icon: CheckSquare },
  { name: 'Projets', href: '/projects', icon: Target },
  { name: 'Agenda', href: '/calendar', icon: Calendar },
  { name: 'Documents SMSI', href: '/documents', icon: FileText },
  { name: 'Base de Connaissances', href: '/knowledge', icon: Book },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <div className="flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="flex items-center h-16 px-6 border-b border-gray-200 dark:border-gray-700">
        <Bot className="w-8 h-8 text-primary-600" />
        <span className="ml-3 text-xl font-bold text-gray-900 dark:text-white">
          SuperAssistant
        </span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`
            }
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          © 2025 SuperAssistant
          <br />
          100% Local & Privé
        </p>
      </div>
    </div>
  );
}
