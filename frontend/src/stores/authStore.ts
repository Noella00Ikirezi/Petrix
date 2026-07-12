/**
 * Store global d'authentification (Zustand).
 * Persiste les tokens JWT et les informations utilisateur dans localStorage
 * sous la clé "petrix-auth" ; expose les actions setAuth, setToken, updateUser et logout.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/** Représentation d'un utilisateur Petrix telle que renvoyée par l'endpoint /auth/me. */
interface User {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  /** Rôle RBAC : admin | auditor | analyst | viewer */
  role: string;
  avatar_url: string | null;
}

/**
 * Forme complète du store d'authentification.
 * Les quatre actions mutent l'état de manière atomique et sont synchronisées
 * automatiquement avec le localStorage via le middleware `persist`.
 */
interface AuthState {
  /** Access token JWT courant (Bearer). */
  token: string | null;
  /** Refresh token utilisé pour renouveler l'access token expiré. */
  refreshToken: string | null;
  /** Profil de l'utilisateur connecté, null si non authentifié. */
  user: User | null;
  /** Indique si une session active est en cours. */
  isAuthenticated: boolean;
  /** Initialise la session complète après connexion ou vérification OTP réussie. */
  setAuth: (token: string, refreshToken: string, user: User) => void;
  /** Met à jour uniquement l'access token (après refresh silencieux). */
  setToken: (token: string) => void;
  /** Met à jour uniquement le refresh token. */
  setRefreshToken: (refreshToken: string) => void;
  /** Applique une mise à jour partielle du profil utilisateur (ex. : changement de nom). */
  updateUser: (updates: Partial<User>) => void;
  /** Efface tous les tokens et l'utilisateur — réinitialise l'état à non-authentifié. */
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      setAuth: (token, refreshToken, user) =>
        set({ token, refreshToken, user, isAuthenticated: true }),
      setToken: (token) => set({ token }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : state.user,
        })),
      logout: () =>
        set({ token: null, refreshToken: null, user: null, isAuthenticated: false }),
    }),
    { name: 'petrix-auth' }
  )
);
