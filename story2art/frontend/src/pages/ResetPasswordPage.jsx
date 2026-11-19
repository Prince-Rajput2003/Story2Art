import { useEffect, useMemo, useState } from 'react';
import { CheckCircle2, Eye, EyeOff, KeyRound, LoaderCircle, LockKeyhole } from 'lucide-react';
import { motion } from 'framer-motion';
import { useLocation, useNavigate } from 'react-router-dom';
import { normalizeApiError, resetPassword } from '../services/api';

function MissingResetAuthorization() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate('/forgot-password', { replace: true });
  }, [navigate]);
  return null;
}

function ResetPasswordPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const resetToken = location.state?.resetToken || '';
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const requirements = useMemo(() => [
    { label: 'At least 8 characters', passed: password.length >= 8 },
    { label: 'An uppercase letter', passed: /\p{Lu}/u.test(password) },
    { label: 'A lowercase letter', passed: /\p{Ll}/u.test(password) },
    { label: 'A number', passed: /\p{Nd}/u.test(password) },
    { label: 'A special character', passed: /[^\p{L}\p{N}\s]/u.test(password) },
  ], [password]);
  const strength = requirements.filter((requirement) => requirement.passed).length;
  const strengthLabel = ['Very weak', 'Very weak', 'Weak', 'Fair', 'Good', 'Strong'][strength];

  if (!resetToken) return <MissingResetAuthorization />;

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    if (password !== confirmPassword) {
      setError('Your passwords do not match.');
      return;
    }
    if (strength !== requirements.length) {
      setError('Please meet all password requirements before continuing.');
      return;
    }

    setLoading(true);
    try {
      await resetPassword({
        reset_token: resetToken,
        new_password: password,
        confirm_password: confirmPassword,
      });
      setSuccess(true);
      window.setTimeout(() => {
        navigate('/login', {
          replace: true,
          state: { success: 'Your password has been reset. Sign in with your new password.' },
        });
      }, 1200);
    } catch (resetError) {
      setError(normalizeApiError(resetError, 'Unable to reset your password. Please restart password recovery.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-md py-10"
    >
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-violet-950/30 sm:p-9">
        <div className="mb-7 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15 text-violet-200">
            <LockKeyhole className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-violet-300">Secure your account</p>
            <h1 className="text-2xl font-bold text-white">Reset Password</h1>
          </div>
        </div>

        {error && <div role="alert" className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="new-password" className="mb-2 block text-sm text-slate-200">New Password</label>
            <div className="relative">
              <input
                id="new-password"
                type={showPasswords ? 'text' : 'password'}
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 pr-12 text-white outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-500/20"
                required
              />
              <button
                type="button"
                onClick={() => setShowPasswords(!showPasswords)}
                aria-label={showPasswords ? 'Hide passwords' : 'Show passwords'}
                className="absolute inset-y-0 right-3 text-slate-400 transition hover:text-white"
              >
                {showPasswords ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <div>
            <label htmlFor="confirm-password" className="mb-2 block text-sm text-slate-200">Confirm New Password</label>
            <input
              id="confirm-password"
              type={showPasswords ? 'text' : 'password'}
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-500/20"
              required
            />
            {confirmPassword && password !== confirmPassword && (
              <p className="mt-2 text-xs text-rose-300" role="status">Your passwords do not match.</p>
            )}
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-950/50 p-4">
            <div className="mb-3 flex items-center justify-between text-sm">
              <span className="font-medium text-slate-200">Password strength</span>
              <span className={strength === 5 ? 'text-emerald-300' : 'text-slate-400'}>{strengthLabel}</span>
            </div>
            <div className="mb-4 flex gap-1.5" aria-label={`${strength} of 5 password requirements met`}>
              {requirements.map((requirement) => (
                <span
                  key={requirement.label}
                  className={`h-1.5 flex-1 rounded-full transition-colors ${requirement.passed ? 'bg-violet-400' : 'bg-white/10'}`}
                />
              ))}
            </div>
            <ul className="grid gap-2 text-xs text-slate-400 sm:grid-cols-2">
              {requirements.map((requirement) => (
                <li key={requirement.label} className={`flex items-center gap-2 ${requirement.passed ? 'text-emerald-300' : ''}`}>
                  <CheckCircle2 className={`h-3.5 w-3.5 shrink-0 ${requirement.passed ? '' : 'text-slate-600'}`} />
                  {requirement.label}
                </li>
              ))}
            </ul>
          </div>

          <button
            type="submit"
            disabled={loading || success || strength !== requirements.length || password !== confirmPassword}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white shadow-lg shadow-violet-950/40 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <LoaderCircle className="h-5 w-5 animate-spin" /> : <KeyRound className="h-4 w-4" />}
            {loading ? 'Updating password...' : 'Reset Password'}
          </button>
        </form>

        {success && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            role="status"
            className="fixed bottom-6 left-1/2 z-[60] flex -translate-x-1/2 items-center gap-3 rounded-2xl border border-emerald-400/30 bg-slate-900 px-5 py-4 text-sm text-emerald-200 shadow-2xl shadow-black/40"
          >
            <CheckCircle2 className="h-5 w-5 shrink-0" />
            Password reset successfully. Redirecting to login...
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

export default ResetPasswordPage;
