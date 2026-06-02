import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, Mail, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';

type Phase = 'credentials' | 'otp';

export default function LoginPage() {
  const [phase, setPhase] = useState<Phase>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Auto-focus first OTP input when switching to OTP phase
  useEffect(() => {
    if (phase === 'otp') {
      otpRefs.current[0]?.focus();
    }
  }, [phase]);

  const handleCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const data = await authApi.login(email, password);

      // MFA désactivé → tokens directs
      if (data.access_token) {
        // Stocker le token d'abord pour que getMe() fonctionne
        useAuthStore.getState().setToken(data.access_token);
        useAuthStore.getState().setRefreshToken(data.refresh_token);

        try {
          const user = await authApi.getMe();
          setAuth(data.access_token, data.refresh_token, user);
        } catch {
          // Si getMe échoue, on crée un user minimal depuis l'email
          setAuth(data.access_token, data.refresh_token, {
            id: '', email, first_name: null, last_name: null, role: 'admin',
          });
        }

        toast.success('Connecté');
        navigate('/dashboard');
        return;
      }

      // MFA activé → phase OTP
      setMfaToken(data.mfa_token);
      setPhase('otp');
      toast.success('Code envoyé sur votre email');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyOtp = async (code: string) => {
    setIsLoading(true);

    try {
      const { access_token, refresh_token } = await authApi.verifyOtp(mfaToken, code);

      // Set token to make authenticated request
      useAuthStore.getState().setToken(access_token);

      // Get user info
      const user = await authApi.getMe();
      setAuth(access_token, refresh_token, user);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Invalid OTP code');
      setOtpDigits(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleOtpChange = (index: number, value: string) => {
    // Handle paste
    if (value.length > 1) {
      const digits = value.replace(/\D/g, '').slice(0, 6).split('');
      const newOtp = [...otpDigits];
      digits.forEach((d, i) => {
        if (index + i < 6) newOtp[index + i] = d;
      });
      setOtpDigits(newOtp);

      const nextIndex = Math.min(index + digits.length, 5);
      otpRefs.current[nextIndex]?.focus();

      // Auto-submit if all 6 digits filled
      if (newOtp.every((d) => d !== '')) {
        verifyOtp(newOtp.join(''));
      }
      return;
    }

    // Single digit
    if (value && !/^\d$/.test(value)) return;

    const newOtp = [...otpDigits];
    newOtp[index] = value;
    setOtpDigits(newOtp);

    if (value && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }

    // Auto-submit when all 6 digits entered
    if (value && newOtp.every((d) => d !== '')) {
      verifyOtp(newOtp.join(''));
    }
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const handleBack = () => {
    setPhase('credentials');
    setOtpDigits(['', '', '', '', '', '']);
    setMfaToken('');
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
            Security & Compliance Platform
          </p>
        </div>

        {/* Phase 1: Credentials */}
        {phase === 'credentials' && (
          <div className="card">
            <form onSubmit={handleCredentials} className="space-y-4">
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
                  placeholder="admin@petrix.local"
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
                    Verifying...
                  </>
                ) : (
                  'Continue'
                )}
              </button>
            </form>

            <div className="mt-4 text-center">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Don't have an account?{' '}
                <Link to="/signup" className="font-medium text-primary-600 hover:underline dark:text-primary-400">
                  Sign up
                </Link>
              </p>
            </div>
          </div>
        )}

        {/* Phase 2: OTP Verification */}
        {phase === 'otp' && (
          <div className="card">
            <div className="mb-6 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/50">
                <Mail className="h-7 w-7 text-primary-600 dark:text-primary-400" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Verification code
              </h2>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Code sent to <span className="font-medium text-gray-700 dark:text-gray-300">{email}</span>
              </p>
            </div>

            <div className="flex justify-center gap-2">
              {otpDigits.map((digit, index) => (
                <input
                  key={index}
                  ref={(el) => { otpRefs.current[index] = el; }}
                  type="text"
                  inputMode="numeric"
                  maxLength={6}
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleOtpKeyDown(index, e)}
                  className="h-14 w-12 rounded-lg border border-gray-300 bg-white text-center text-xl font-bold text-gray-900 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400"
                  disabled={isLoading}
                />
              ))}
            </div>

            {isLoading && (
              <div className="mt-4 flex items-center justify-center text-sm text-gray-500">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Verifying...
              </div>
            )}

            <div className="mt-6 text-center">
              <button
                onClick={handleBack}
                className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <ArrowLeft className="mr-1 h-4 w-4" />
                Back to login
              </button>
            </div>

            <p className="mt-4 text-center text-xs text-gray-400 dark:text-gray-500">
              Check your email for the 6-digit code. Code expires in 5 minutes.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
