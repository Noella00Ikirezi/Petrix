import { useState, useRef } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { User, Shield, Bell, Palette, Camera, Trash2 } from 'lucide-react';
import toast from 'react-hot-toast';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('profile');

  const tabs = [
    { id: 'profile',       label: 'Profil',        icon: User },
    { id: 'security',      label: 'Sécurité',       icon: Shield },
    { id: 'notifications', label: 'Notifications',  icon: Bell },
    { id: 'appearance',    label: 'Apparence',      icon: Palette },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Paramètres</h1>
        <p className="text-gray-600 dark:text-gray-400">Gérez votre compte et vos préférences</p>
      </div>

      <div className="flex gap-6">
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

        <div className="flex-1">
          {activeTab === 'profile'       && <ProfileSettings />}
          {activeTab === 'security'      && <SecuritySettings />}
          {activeTab === 'notifications' && <NotificationSettings />}
          {activeTab === 'appearance'    && <AppearanceSettings />}
        </div>
      </div>
    </div>
  );
}

function resizeImageToDataUrl(file: File, size = 128): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => {
      URL.revokeObjectURL(url);
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d')!;
      const side = Math.min(img.width, img.height);
      const sx = (img.width - side) / 2;
      const sy = (img.height - side) / 2;
      ctx.drawImage(img, sx, sy, side, side, 0, 0, size, size);
      resolve(canvas.toDataURL('image/jpeg', 0.82));
    };
    img.onerror = reject;
    img.src = url;
  });
}

function ProfileSettings() {
  const { user, token, updateUser } = useAuthStore();
  const [formData, setFormData] = useState({
    first_name: user?.first_name || '',
    last_name:  user?.last_name  || '',
  });
  const [loading, setLoading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/v1/users/me', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify(formData),
      });
      if (res.ok) {
        const updated = await res.json();
        updateUser({ first_name: updated.first_name, last_name: updated.last_name });
        toast.success('Profil mis à jour');
      } else {
        toast.error('Erreur lors de la mise à jour');
      }
    } catch {
      toast.error('Erreur réseau');
    } finally {
      setLoading(false);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      toast.error('Fichier non supporté — image requise');
      return;
    }
    setAvatarLoading(true);
    try {
      const dataUrl = await resizeImageToDataUrl(file, 128);
      const res = await fetch('/api/v1/users/me/avatar', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ avatar_url: dataUrl }),
      });
      if (res.ok) {
        const updated = await res.json();
        updateUser({ avatar_url: updated.avatar_url });
        toast.success('Photo de profil mise à jour');
      } else {
        toast.error('Erreur lors de l\'upload');
      }
    } catch {
      toast.error('Erreur lors du traitement de l\'image');
    } finally {
      setAvatarLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleAvatarDelete = async () => {
    setAvatarLoading(true);
    try {
      const res = await fetch('/api/v1/users/me/avatar', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ avatar_url: null }),
      });
      if (res.ok) {
        updateUser({ avatar_url: null });
        toast.success('Photo supprimée');
      }
    } catch {
      toast.error('Erreur réseau');
    } finally {
      setAvatarLoading(false);
    }
  };

  const initials = user?.first_name && user?.last_name
    ? `${user.first_name[0]}${user.last_name[0]}`.toUpperCase()
    : user?.first_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?';

  return (
    <div className="card space-y-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Informations du profil</h2>

      {/* Avatar */}
      <div className="flex items-center gap-5">
        <div className="relative">
          {user?.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Avatar"
              className="h-20 w-20 rounded-full object-cover ring-4 ring-primary-100 dark:ring-primary-900"
            />
          ) : (
            <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary-500 text-3xl font-bold text-white ring-4 ring-primary-100 dark:ring-primary-900">
              {initials}
            </div>
          )}
          {avatarLoading && (
            <div className="absolute inset-0 flex items-center justify-center rounded-full bg-black/40">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
            </div>
          )}
        </div>

        <div className="space-y-2">
          <p className="font-medium text-gray-900 dark:text-white">
            {user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email}
          </p>
          <p className="text-sm capitalize text-gray-500 dark:text-gray-400">{user?.role}</p>
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarChange}
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={avatarLoading}
              className="btn btn-secondary btn-sm"
            >
              <Camera className="mr-1.5 h-3.5 w-3.5" />
              {user?.avatar_url ? 'Changer la photo' : 'Ajouter une photo'}
            </button>
            {user?.avatar_url && (
              <button
                type="button"
                onClick={handleAvatarDelete}
                disabled={avatarLoading}
                className="btn btn-secondary btn-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
          <p className="text-xs text-gray-400">JPG, PNG, GIF · max 5 Mo · réduit à 128×128</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">Prénom</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="input mt-1"
              placeholder="Votre prénom"
            />
          </div>
          <div>
            <label className="label">Nom</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="input mt-1"
              placeholder="Votre nom"
            />
          </div>
        </div>
        <div>
          <label className="label">Email</label>
          <input type="email" value={user?.email || ''} className="input mt-1 opacity-60" disabled />
          <p className="mt-1 text-xs text-gray-500">L'email ne peut pas être modifié</p>
        </div>
        <div>
          <label className="label">Rôle</label>
          <input type="text" value={user?.role || ''} className="input mt-1 capitalize opacity-60" disabled />
          <p className="mt-1 text-xs text-gray-500">Le rôle est géré par un administrateur</p>
        </div>
        <div className="pt-2">
          <button type="submit" disabled={loading} className="btn btn-primary btn-md">
            {loading ? 'Enregistrement...' : 'Enregistrer les modifications'}
          </button>
        </div>
      </form>
    </div>
  );
}

function SecuritySettings() {
  const { token } = useAuthStore();
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.new_password !== form.confirm_password) {
      toast.error('Les mots de passe ne correspondent pas');
      return;
    }
    if (form.new_password.length < 8) {
      toast.error('Le nouveau mot de passe doit faire au moins 8 caractères');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          current_password: form.current_password,
          new_password: form.new_password,
        }),
      });
      if (res.ok) {
        toast.success('Mot de passe changé avec succès');
        setForm({ current_password: '', new_password: '', confirm_password: '' });
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erreur');
      }
    } catch {
      toast.error('Erreur réseau');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Changer le mot de passe</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Mot de passe actuel</label>
          <input
            type="password"
            value={form.current_password}
            onChange={(e) => setForm({ ...form, current_password: e.target.value })}
            className="input mt-1"
            autoComplete="current-password"
            required
          />
        </div>
        <div>
          <label className="label">Nouveau mot de passe</label>
          <input
            type="password"
            value={form.new_password}
            onChange={(e) => setForm({ ...form, new_password: e.target.value })}
            className="input mt-1"
            autoComplete="new-password"
            minLength={8}
            required
          />
          <p className="mt-1 text-xs text-gray-500">Minimum 8 caractères</p>
        </div>
        <div>
          <label className="label">Confirmer le nouveau mot de passe</label>
          <input
            type="password"
            value={form.confirm_password}
            onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            className="input mt-1"
            autoComplete="new-password"
            required
          />
        </div>
        <div className="pt-2">
          <button type="submit" disabled={loading} className="btn btn-primary btn-md">
            {loading ? 'Enregistrement...' : 'Changer le mot de passe'}
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
  });

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Notifications</h2>
      <div className="space-y-4">
        <Toggle label="Scan terminé" description="Email quand un scan se termine" checked={settings.email_scan_complete} onChange={() => setSettings(s => ({ ...s, email_scan_complete: !s.email_scan_complete }))} />
        <Toggle label="Vulnérabilité critique" description="Alerte immédiate pour les findings critiques" checked={settings.email_critical_vuln} onChange={() => setSettings(s => ({ ...s, email_critical_vuln: !s.email_critical_vuln }))} />
        <Toggle label="Rapport hebdomadaire" description="Résumé de sécurité chaque semaine" checked={settings.email_weekly_report} onChange={() => setSettings(s => ({ ...s, email_weekly_report: !s.email_weekly_report }))} />
      </div>
    </div>
  );
}

function AppearanceSettings() {
  const [isDark, setIsDark] = useState(document.documentElement.classList.contains('dark'));

  const toggle = () => {
    const v = !isDark;
    setIsDark(v);
    localStorage.setItem('darkMode', String(v));
    document.documentElement.classList.toggle('dark', v);
    toast.success(`Mode ${v ? 'sombre' : 'clair'} activé`);
  };

  return (
    <div className="card">
      <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Apparence</h2>
      <Toggle label="Mode sombre" description="Utiliser le thème sombre" checked={isDark} onChange={toggle} />
    </div>
  );
}

function Toggle({ label, description, checked, onChange }: { label: string; description: string; checked: boolean; onChange: () => void }) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        <p className="text-sm text-gray-500 dark:text-gray-400">{description}</p>
      </div>
      <button
        type="button"
        onClick={onChange}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-primary-600' : 'bg-gray-300 dark:bg-gray-600'}`}
      >
        <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
      </button>
    </div>
  );
}
