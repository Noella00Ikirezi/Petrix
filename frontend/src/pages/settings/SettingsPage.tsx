import { useState } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { Settings, User, Shield, Bell, Palette } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');
  const { user } = useAuthStore();

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'appearance', label: 'Appearance', icon: Palette },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your account and preferences
        </p>
      </div>

      <div className="flex gap-6">
        {/* Tabs */}
        <div className="w-48 shrink-0">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/50 dark:text-primary-300'
                    : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                }`}
              >
                <tab.icon className="h-5 w-5" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && <ProfileSettings user={user} />}
          {activeTab === 'security' && <SecuritySettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          {activeTab === 'appearance' && <AppearanceSettings />}
        </div>
      </div>
    </div>
  );
}

function ProfileSettings({ user }: { user: { email: string; first_name: string | null; last_name: string | null; role: string } | null }) {
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    toast.success('Profile updated (demo)');
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Profile Information
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) =>
                setFormData({ ...formData, first_name: e.target.value })
              }
              className="input mt-1"
            />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) =>
                setFormData({ ...formData, last_name: e.target.value })
              }
              className="input mt-1"
            />
          </div>
        </div>
        <div>
          <label className="label">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="input mt-1"
            disabled
          />
          <p className="mt-1 text-xs text-gray-500">
            Email cannot be changed
          </p>
        </div>
        <div>
          <label className="label">Role</label>
          <input
            type="text"
            value={user?.role || ''}
            className="input mt-1"
            disabled
          />
        </div>
        <div className="pt-4">
          <button type="submit" className="btn btn-primary btn-md">
            Save Changes
          </button>
        </div>
      </form>
    </div>
  );
}

function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    toast.success('Password changed (demo)');
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Change Password
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Current Password</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="input mt-1"
            required
          />
        </div>
        <div>
          <label className="label">New Password</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="input mt-1"
            required
            minLength={8}
          />
        </div>
        <div>
          <label className="label">Confirm New Password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="input mt-1"
            required
          />
        </div>
        <div className="pt-4">
          <button type="submit" className="btn btn-primary btn-md">
            Change Password
          </button>
        </div>
      </form>
    </div>
  );
}

function NotificationSettings() {
  const [settings, setSettings] = useState({
    email_scan_complete: true,
    email_critical_vuln: true,
    email_weekly_report: false,
    browser_notifications: true,
  });

  const handleToggle = (key: keyof typeof settings) => {
    setSettings({ ...settings, [key]: !settings[key] });
    toast.success('Setting updated');
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Notification Preferences
      </h2>
      <div className="space-y-4">
        <ToggleOption
          label="Scan completion emails"
          description="Receive an email when a scan completes"
          checked={settings.email_scan_complete}
          onChange={() => handleToggle('email_scan_complete')}
        />
        <ToggleOption
          label="Critical vulnerability alerts"
          description="Immediate notification for critical findings"
          checked={settings.email_critical_vuln}
          onChange={() => handleToggle('email_critical_vuln')}
        />
        <ToggleOption
          label="Weekly security report"
          description="Receive a weekly summary of your security posture"
          checked={settings.email_weekly_report}
          onChange={() => handleToggle('email_weekly_report')}
        />
        <ToggleOption
          label="Browser notifications"
          description="Show desktop notifications for important events"
          checked={settings.browser_notifications}
          onChange={() => handleToggle('browser_notifications')}
        />
      </div>
    </div>
  );
}

function AppearanceSettings() {
  const [isDark, setIsDark] = useState(
    document.documentElement.classList.contains('dark')
  );

  const toggleDarkMode = () => {
    const newValue = !isDark;
    setIsDark(newValue);
    localStorage.setItem('darkMode', String(newValue));
    document.documentElement.classList.toggle('dark', newValue);
    toast.success(`${newValue ? 'Dark' : 'Light'} mode enabled`);
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
        Appearance
      </h2>
      <div className="space-y-4">
        <ToggleOption
          label="Dark mode"
          description="Use dark theme for the interface"
          checked={isDark}
          onChange={toggleDarkMode}
        />
      </div>
    </div>
  );
}

function ToggleOption({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: () => void;
}) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <button
        type="button"
        onClick={onChange}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
          checked ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}
