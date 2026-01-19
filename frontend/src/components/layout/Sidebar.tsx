import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Server,
  Shield,
  Scan,
  FileText,
  Users,
  Settings,
  ShieldCheck,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Assets', href: '/assets', icon: Server },
  { name: 'Vulnerabilities', href: '/vulnerabilities', icon: Shield },
  { name: 'Scans', href: '/scans', icon: Scan },
  { name: 'Compliance', href: '/compliance', icon: ShieldCheck, disabled: true },
  { name: 'Reports', href: '/reports', icon: FileText, disabled: true },
  { name: 'Users', href: '/users', icon: Users, disabled: true },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      {/* Logo */}
      <div className="flex h-16 items-center gap-2 border-b border-gray-200 px-6 dark:border-gray-700">
        <ShieldCheck className="h-8 w-8 text-primary-600" />
        <span className="text-xl font-bold text-gray-900 dark:text-white">
          GRC Platform
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.disabled ? '#' : item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                item.disabled
                  ? 'cursor-not-allowed text-gray-400 dark:text-gray-600'
                  : isActive
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
                  : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
              }`
            }
            onClick={(e) => item.disabled && e.preventDefault()}
          >
            <item.icon className="h-5 w-5" />
            {item.name}
            {item.disabled && (
              <span className="ml-auto text-xs text-gray-400">Soon</span>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="border-t border-gray-200 p-4 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          GRC Platform v0.1.0
        </p>
      </div>
    </div>
  );
}
