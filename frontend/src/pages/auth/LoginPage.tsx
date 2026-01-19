import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const { access_token } = await authApi.login(email, password);

      // Set token first to make authenticated request
      useAuthStore.getState().token = access_token;

      // Get user info
      const user = await authApi.getMe();

      setAuth(access_token, user);
      toast.success('Welcome back!');
      navigate('/');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 dark:bg-gray-900">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
            <ShieldCheck className="h-10 w-10 text-primary-600 dark:text-primary-400" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            GRC Platform
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Governance, Risk & Compliance Management
          </p>
        </div>

        {/* Login form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input mt-1"
                placeholder="admin@grc-platform.local"
                required
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input mt-1"
                placeholder="********"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary btn-md w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-500 dark:text-gray-400">
            Default: admin@grc-platform.local / admin123
          </div>
        </div>
      </div>
    </div>
  );
}
