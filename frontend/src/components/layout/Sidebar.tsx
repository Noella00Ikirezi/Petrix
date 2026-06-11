import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Server,
  Shield,
  ShieldCheck,
  Scan,
  Users,
  Settings,
  ClipboardList,
  Bot,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard',      href: '/dashboard',       icon: LayoutDashboard },
  { name: 'Assets',         href: '/assets',          icon: Server },
  { name: 'Scans',          href: '/scans',           icon: Scan },
  { name: 'Vulnérabilités', href: '/vulnerabilities', icon: Shield },
  { name: 'Hardening',      href: '/hardening',       icon: ShieldCheck },
  { name: 'Agent',          href: '/agent',           icon: Bot },
  { name: 'Utilisateurs',   href: '/users',           icon: Users },
  { name: 'Audit Logs',     href: '/audit-logs',      icon: ClipboardList },
  { name: 'Paramètres',     href: '/settings',        icon: Settings },
];

export default function Sidebar() {
  return (
    <div className="flex h-full w-64 flex-col border-r border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="flex h-16 items-center gap-3 border-b border-gray-200 px-6 dark:border-gray-700">
        <img src="/logo-petrix-dark.svg" alt="Petrix" className="hidden h-9 w-9 dark:block" />
        <img src="/logo-petrix.svg" alt="Petrix" className="h-9 w-9 dark:hidden" />
        <span className="text-xl font-bold text-petrix-void dark:text-petrix-cyan-light">
          Petrix
        </span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
                  : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-gray-200 p-4 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400">Petrix v0.2.0</p>
      </div>
    </div>
  );
}
