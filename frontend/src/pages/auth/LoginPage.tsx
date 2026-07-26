/**
 * Page de connexion à deux étapes (MFA).
 * Phase 1 : saisie email/mot de passe → envoi OTP par email.
 * Phase 2 : saisie du code OTP à 6 chiffres → obtention des tokens JWT et redirection.
 */
import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { authApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';

type Phase = 'credentials' | 'otp' | 'forgot-email' | 'forgot-otp' | 'forgot-new-password';

/**
 * Page de connexion Petrix avec authentification multi-facteurs (email OTP).
 * Gère la transition entre les deux phases et le focus automatique sur les champs OTP.
 */
export default function LoginPage() {
  const [phase, setPhase] = useState<Phase>('credentials');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaToken, setMfaToken] = useState('');
  const [otpDigits, setOtpDigits] = useState(['', '', '', '', '', '']);
  const [forgotEmail, setForgotEmail] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [resetOtpDigits, setResetOtpDigits] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const resetOtpRefs = useRef<(HTMLInputElement | null)[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);
  const otpRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (phase === 'otp') otpRefs.current[0]?.focus();
    if (phase === 'forgot-otp') resetOtpRefs.current[0]?.focus();
  }, [phase]);

  /**
   * Soumet les identifiants et bascule en phase OTP si le backend renvoie un mfa_token,
   * ou termine la connexion directement si un access_token est immédiatement retourné.
   */
  const handleCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const data = await authApi.login(email, password);
      if (data.access_token) {
        useAuthStore.getState().setToken(data.access_token);
        useAuthStore.getState().setRefreshToken(data.refresh_token);
        try {
          const user = await authApi.getMe();
          setAuth(data.access_token, data.refresh_token, user);
        } catch {
          setAuth(data.access_token, data.refresh_token, { id: '', email, first_name: null, last_name: null, role: 'admin', avatar_url: null });
        }
        toast.success('Connecté');
        navigate(data.must_change_password ? '/change-password' : '/dashboard');
        return;
      }
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

  /**
   * Vérifie le code OTP auprès du backend et finalise l'authentification.
   * @param code - Code à 6 chiffres saisi par l'utilisateur.
   */
  const verifyOtp = async (code: string) => {
    setIsLoading(true);
    try {
      const { access_token, refresh_token } = await authApi.verifyOtp(mfaToken, code);
      useAuthStore.getState().setToken(access_token);
      const user = await authApi.getMe();
      setAuth(access_token, refresh_token, user);
      toast.success('Connecté');
      navigate('/dashboard');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Code invalide');
      setOtpDigits(['', '', '', '', '', '']);
      otpRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Gère la saisie dans un champ OTP individuel : avance le focus, gère le collage
   * de 6 chiffres d'un coup et déclenche la vérification automatique quand tous les champs sont remplis.
   * @param index - Position du champ (0–5).
   * @param value - Caractère(s) saisi(s).
   */
  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) {
      const digits = value.replace(/\D/g, '').slice(0, 6).split('');
      const newOtp = [...otpDigits];
      digits.forEach((d, i) => { if (index + i < 6) newOtp[index + i] = d; });
      setOtpDigits(newOtp);
      otpRefs.current[Math.min(index + digits.length, 5)]?.focus();
      if (newOtp.every((d) => d !== '')) verifyOtp(newOtp.join(''));
      return;
    }
    if (value && !/^\d$/.test(value)) return;
    const newOtp = [...otpDigits];
    newOtp[index] = value;
    setOtpDigits(newOtp);
    if (value && index < 5) otpRefs.current[index + 1]?.focus();
    if (value && newOtp.every((d) => d !== '')) verifyOtp(newOtp.join(''));
  };

  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) otpRefs.current[index - 1]?.focus();
  };

  const handleForgotEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const data = await authApi.forgotPassword(forgotEmail);
      setResetToken(data.reset_token);
      setPhase('forgot-otp');
      toast.success('Si cet email existe, un code a été envoyé');
    } catch {
      toast.error('Erreur — réessayez');
    } finally {
      setIsLoading(false);
    }
  };

  const verifyResetOtp = async (code: string) => {
    // On garde juste le code pour la prochaine étape
    setResetToken(resetToken); // déjà stocké
    setPhase('forgot-new-password');
    // Store the code temporarily in the resetToken state as a combined string
    setResetToken(`${resetToken}__${code}`);
  };

  const handleResetOtpChange = (index: number, value: string) => {
    if (value.length > 1) {
      const digits = value.replace(/\D/g, '').slice(0, 6).split('');
      const newOtp = [...resetOtpDigits];
      digits.forEach((d, i) => { if (index + i < 6) newOtp[index + i] = d; });
      setResetOtpDigits(newOtp);
      resetOtpRefs.current[Math.min(index + digits.length, 5)]?.focus();
      if (newOtp.every((d) => d !== '')) verifyResetOtp(newOtp.join(''));
      return;
    }
    if (value && !/^\d$/.test(value)) return;
    const newOtp = [...resetOtpDigits];
    newOtp[index] = value;
    setResetOtpDigits(newOtp);
    if (value && index < 5) resetOtpRefs.current[index + 1]?.focus();
    if (value && newOtp.every((d) => d !== '')) verifyResetOtp(newOtp.join(''));
  };

  const handleResetOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !resetOtpDigits[index] && index > 0) resetOtpRefs.current[index - 1]?.focus();
  };

  const handleNewPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) { toast.error('Les mots de passe ne correspondent pas'); return; }
    if (newPassword.length < 8) { toast.error('Minimum 8 caractères'); return; }
    const [token, code] = resetToken.split('__');
    setIsLoading(true);
    try {
      await authApi.resetPassword(token, code, newPassword);
      toast.success('Mot de passe réinitialisé — connectez-vous');
      setPhase('credentials');
      setResetToken(''); setResetOtpDigits(['', '', '', '', '', '']); setNewPassword(''); setConfirmPassword('');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Erreur lors de la réinitialisation');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 24px', fontFamily: 'var(--font-mono)' }}>
      {/* Pixels décoratifs */}
      <span style={{ position: 'fixed', top: '20%', left: '5%', width: 6, height: 6, background: 'var(--lime)', opacity: 0, animation: 'pxfade 6s ease-in-out infinite' }} />
      <span style={{ position: 'fixed', top: '60%', right: '8%', width: 6, height: 6, background: 'var(--lime)', opacity: 0, animation: 'pxfade 6s ease-in-out 2s infinite' }} />

      <div style={{ width: '100%', maxWidth: 420 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ display: 'inline-block', border: '1px solid var(--lime-dim)', padding: '12px 24px', marginBottom: 20 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 18, letterSpacing: '.08em', color: 'var(--text)' }}>
              &lt;PETRIX <span style={{ color: 'var(--lime)' }}>/&gt;</span>
            </span>
          </div>
          <div style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)' }}>
            // Security &amp; Compliance Platform
          </div>
        </div>

        {/* Phase 1 : credentials */}
        {phase === 'credentials' && (
          <div style={{ border: '1px solid var(--line)', background: 'var(--panel)' }}>
            {/* Header du panel */}
            <div style={{ borderBottom: '1px solid var(--line)', padding: '14px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--lime)' }}>// AUTH.LOGIN()</span>
              <span style={{ fontSize: 10, letterSpacing: '.15em', color: 'var(--faint)', textTransform: 'uppercase' }}>Accès_Sécurisé</span>
            </div>

            <form onSubmit={handleCredentials} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div>
                <label htmlFor="email" style={{ display: 'block', fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 8 }}>
                  .Email
                </label>
                <input
                  id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  className="input" placeholder="admin@petrix.local" required
                  style={{ width: '100%' }}
                />
              </div>
              <div>
                <label htmlFor="password" style={{ display: 'block', fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 8 }}>
                  .Password
                </label>
                <input
                  id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="input" placeholder="••••••••" required
                  style={{ width: '100%' }}
                />
              </div>

              <button type="submit" disabled={isLoading} className="btn" style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 8, opacity: isLoading ? 0.6 : 1 }}>
                {isLoading ? <><Loader2 size={14} className="animate-spin" /> Vérification...</> : 'CONNEXION()'}
              </button>
            </form>

            {/* Footer du panel */}
            <div style={{ borderTop: '1px solid var(--line)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--faint)', letterSpacing: '.1em' }}>
              <button
                type="button"
                onClick={() => setPhase('forgot-email')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: 10, color: 'var(--faint)', fontFamily: 'var(--font-mono)', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                Mot de passe oublié ?
              </button>
              <Link to="/signup" style={{ color: 'var(--lime)', textTransform: 'uppercase', letterSpacing: '.15em', fontSize: 10 }}>
                SIGNUP() →
              </Link>
            </div>
          </div>
        )}

        {/* Phase forgot-email */}
        {phase === 'forgot-email' && (
          <div style={{ border: '1px solid var(--line)', background: 'var(--panel)' }}>
            <div style={{ borderBottom: '1px solid var(--line)', padding: '14px 24px' }}>
              <span style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--lime)' }}>// AUTH.RESET_PASSWORD()</span>
            </div>
            <form onSubmit={handleForgotEmail} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <p style={{ fontSize: 12, color: 'var(--dim)', textTransform: 'uppercase', letterSpacing: '.05em' }}>
                Entrez votre email. Si le compte existe, un code de réinitialisation sera envoyé.
              </p>
              <div>
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 8 }}>
                  .Email
                </label>
                <input
                  type="email" value={forgotEmail} onChange={(e) => setForgotEmail(e.target.value)}
                  className="input" placeholder="votre@email.com" required style={{ width: '100%' }}
                />
              </div>
              <button type="submit" disabled={isLoading} className="btn" style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 8, opacity: isLoading ? 0.6 : 1 }}>
                {isLoading ? <><Loader2 size={14} className="animate-spin" /> Envoi...</> : 'ENVOYER_CODE()'}
              </button>
            </form>
            <div style={{ borderTop: '1px solid var(--line)', padding: '12px 24px' }}>
              <button onClick={() => setPhase('credentials')} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--faint)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                <ArrowLeft size={12} /> Retour
              </button>
            </div>
          </div>
        )}

        {/* Phase forgot-otp */}
        {phase === 'forgot-otp' && (
          <div style={{ border: '1px solid var(--line)', background: 'var(--panel)' }}>
            <div style={{ borderBottom: '1px solid var(--line)', padding: '14px 24px' }}>
              <span style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--lime)' }}>// MFA.VERIFY_RESET()</span>
            </div>
            <div style={{ padding: 24 }}>
              <p style={{ fontSize: 12, color: 'var(--dim)', marginBottom: 24, textTransform: 'uppercase', letterSpacing: '.05em' }}>
                Code envoyé à <span style={{ color: 'var(--text)' }}>{forgotEmail}</span>
              </p>
              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}>
                {resetOtpDigits.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => { resetOtpRefs.current[index] = el; }}
                    type="text" inputMode="numeric" maxLength={6}
                    value={digit}
                    onChange={(e) => handleResetOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleResetOtpKeyDown(index, e)}
                    disabled={isLoading}
                    style={{ width: 48, height: 56, textAlign: 'center', fontSize: 20, fontWeight: 700, background: 'var(--panel-hi)', border: `1px solid ${digit ? 'var(--lime)' : 'var(--line)'}`, color: 'var(--text)', fontFamily: 'var(--font-mono)', outline: 'none' }}
                  />
                ))}
              </div>
              {isLoading && <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: 'var(--faint)', fontSize: 12 }}><Loader2 size={14} className="animate-spin" /> Vérification...</div>}
            </div>
            <div style={{ borderTop: '1px solid var(--line)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button onClick={() => { setPhase('forgot-email'); setResetOtpDigits(['', '', '', '', '', '']); }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--faint)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                <ArrowLeft size={12} /> Retour
              </button>
              <span style={{ fontSize: 10, color: 'var(--faint)', letterSpacing: '.1em', textTransform: 'uppercase' }}>Expire dans 5min</span>
            </div>
          </div>
        )}

        {/* Phase forgot-new-password */}
        {phase === 'forgot-new-password' && (
          <div style={{ border: '1px solid var(--line)', background: 'var(--panel)' }}>
            <div style={{ borderBottom: '1px solid var(--line)', padding: '14px 24px' }}>
              <span style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--lime)' }}>// AUTH.SET_NEW_PASSWORD()</span>
            </div>
            <form onSubmit={handleNewPassword} style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
              <div>
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 8 }}>
                  .Nouveau mot de passe
                </label>
                <input
                  type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)}
                  className="input" placeholder="••••••••" required minLength={8} style={{ width: '100%' }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--faint)', marginBottom: 8 }}>
                  .Confirmer le mot de passe
                </label>
                <input
                  type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                  className="input" placeholder="••••••••" required minLength={8} style={{ width: '100%' }}
                />
              </div>
              <button type="submit" disabled={isLoading} className="btn" style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: 8, opacity: isLoading ? 0.6 : 1 }}>
                {isLoading ? <><Loader2 size={14} className="animate-spin" /> Réinitialisation...</> : 'RÉINITIALISER()'}
              </button>
            </form>
          </div>
        )}

        {/* Phase 2 : OTP */}
        {phase === 'otp' && (
          <div style={{ border: '1px solid var(--line)', background: 'var(--panel)' }}>
            <div style={{ borderBottom: '1px solid var(--line)', padding: '14px 24px' }}>
              <span style={{ fontSize: 10, letterSpacing: '.25em', textTransform: 'uppercase', color: 'var(--lime)' }}>// MFA.VERIFY()</span>
            </div>

            <div style={{ padding: 24 }}>
              <p style={{ fontSize: 12, color: 'var(--dim)', marginBottom: 24, textTransform: 'uppercase', letterSpacing: '.05em' }}>
                Code envoyé à <span style={{ color: 'var(--text)' }}>{email}</span>
              </p>

              <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}>
                {otpDigits.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => { otpRefs.current[index] = el; }}
                    type="text" inputMode="numeric" maxLength={6}
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(index, e)}
                    disabled={isLoading}
                    style={{
                      width: 48, height: 56, textAlign: 'center', fontSize: 20, fontWeight: 700,
                      background: 'var(--panel-hi)', border: `1px solid ${digit ? 'var(--lime)' : 'var(--line)'}`,
                      color: 'var(--text)', fontFamily: 'var(--font-mono)', outline: 'none',
                    }}
                  />
                ))}
              </div>

              {isLoading && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, color: 'var(--faint)', fontSize: 12, marginBottom: 16 }}>
                  <Loader2 size={14} className="animate-spin" /> Vérification...
                </div>
              )}
            </div>

            <div style={{ borderTop: '1px solid var(--line)', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button onClick={() => { setPhase('credentials'); setOtpDigits(['', '', '', '', '', '']); setMfaToken(''); }}
                style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--faint)', background: 'none', border: 'none', cursor: 'pointer', fontFamily: 'var(--font-mono)', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                <ArrowLeft size={12} /> Retour
              </button>
              <span style={{ fontSize: 10, color: 'var(--faint)', letterSpacing: '.1em', textTransform: 'uppercase' }}>Expire dans 5min</span>
            </div>
          </div>
        )}

        {/* ANSSI mention */}
        <div style={{ marginTop: 24, textAlign: 'center', fontSize: 10, letterSpacing: '.2em', textTransform: 'uppercase', color: 'var(--faint)' }}>
          // Conforme ANSSI-BP-028 · Données locales uniquement
        </div>
      </div>
    </div>
  );
}
