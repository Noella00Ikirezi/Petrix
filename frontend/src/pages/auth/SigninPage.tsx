/**
 * Page d'inscription publique de Petrix.
 * Collecte prénom, nom, email et mot de passe (min. 8 caractères, confirmation),
 * appelle authApi.signup puis redirige vers la page de connexion.
 */
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api/client';

/**
 * Formulaire de création de compte : valide localement les champs
 * avant d'appeler l'API d'inscription et de rediriger vers /login.
 */
export default function SignupPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  /**
   * Valide les champs du formulaire (prénom/nom requis, mots de passe identiques et ≥ 8 chars)
   * puis soumet la requête d'inscription à l'API.
   */
  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!firstName.trim() || !lastName.trim()) {
      toast.error('First and last name are required');
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords don't match");
      return;
    }
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return;
    }
    setIsLoading(true);

    try {
      // Assuming an `authApi.signup` method exists.
      // This would typically make a POST request to a public registration endpoint.
      await authApi.signup(email, password, firstName.trim(), lastName.trim());
      toast.success('Account created successfully! Please log in.');
      navigate('/login');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Signup failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-petrix-white px-4 dark:bg-petrix-void">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="mb-8 text-center">
          <img src="/logo-petrix.svg" alt="Petrix" className="mx-auto mb-4 h-20 w-20 dark:hidden" />
          <img src="/logo-petrix-dark.svg" alt="Petrix" className="mx-auto mb-4 hidden h-20 w-20 dark:block" />
          <h1 className="text-3xl font-bold text-petrix-void dark:text-petrix-cyan-light">
            Petrix
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Create your Security & Compliance Platform account
          </p>
        </div>

        <div className="card">
          <form onSubmit={handleSignup} className="space-y-4">
            <div className="flex space-x-4">
              <div className="w-1/2">
                <label htmlFor="firstName" className="label">
                  First Name
                </label>
                <input
                  id="firstName"
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="input mt-1"
                  placeholder="John"
                  required
                />
              </div>
              <div className="w-1/2">
                <label htmlFor="lastName" className="label">
                  Last Name
                </label>
                <input
                  id="lastName"
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="input mt-1"
                  placeholder="Doe"
                  required
                />
              </div>
            </div>
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
                placeholder="john.doe@example.com"
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
                autoComplete="new-password"
                required
              />
            </div>

            <div>
              <label htmlFor="confirmPassword" className="label">
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input mt-1"
                placeholder="********"
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
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Sign Up'
              )}
            </button>
          </form>
          <div className="mt-4 text-center">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Already have an account?{' '}
              <Link
                to="/login"
                className="font-medium text-primary-600 hover:underline dark:text-primary-400"
              >
                Log in
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
    