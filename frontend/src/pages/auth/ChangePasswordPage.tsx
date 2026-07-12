/**
 * Page de changement de mot de passe obligatoire.
 * Affichée lors de la première connexion (flag must_change_password) ou sur demande.
 * Valide la longueur minimale et la confirmation avant d'appeler /api/v1/auth/change-password.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Lock } from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/stores/authStore';

/**
 * Formulaire de réinitialisation du mot de passe utilisateur.
 * Utilise le token JWT courant pour authentifier la requête POST /auth/change-password.
 */
export default function ChangePasswordPage() {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const token = useAuthStore((s) => s.token);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword.length < 8) {
      toast.error('Le mot de passe doit faire au moins 8 caractères');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Les mots de passe ne correspondent pas');
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('/api/v1/auth/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ new_password: newPassword }),
      });

      if (res.ok) {
        toast.success('Mot de passe mis à jour');
        navigate('/dashboard');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Erreur');
      }
    } catch {
      toast.error('Erreur réseau');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-petrix-white px-4 dark:bg-petrix-void">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
            <Lock className="h-8 w-8 text-amber-600 dark:text-amber-400" />
          </div>
          <h1 className="text-2xl font-bold text-petrix-void dark:text-white">
            Changer votre mot de passe
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Vous devez définir un nouveau mot de passe avant de continuer.
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Nouveau mot de passe</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="input mt-1"
                placeholder="Minimum 8 caractères"
                autoComplete="new-password"
                required
              />
            </div>
            <div>
              <label className="label">Confirmer le mot de passe</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input mt-1"
                placeholder="Répétez votre mot de passe"
                autoComplete="new-password"
                required
              />
            </div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary btn-md w-full"
            >
              {isLoading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Enregistrement...</>
              ) : (
                'Enregistrer le mot de passe'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
