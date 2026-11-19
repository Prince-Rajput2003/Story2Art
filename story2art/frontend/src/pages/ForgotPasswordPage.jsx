import { useState } from 'react';
import { ArrowLeft, KeyRound, LoaderCircle, Mail } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useNavigate } from 'react-router-dom';
import { normalizeApiError, requestPasswordReset } from '../services/api';

function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      await requestPasswordReset({ email: email.trim() });
      navigate('/verify-otp', { state: { email: email.trim().toLowerCase() } });
    } catch (requestError) {
      setError(normalizeApiError(requestError, 'Unable to start password reset. Please try again.'));
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
            <KeyRound className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-violet-300">Account recovery</p>
            <h1 className="text-2xl font-bold text-white">Forgot Your Password?</h1>
          </div>
        </div>

        <p className="mb-6 text-sm leading-6 text-slate-300">
          Enter your registered email address to receive a verification code.
        </p>

        {error && <div role="alert" className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="reset-email" className="mb-2 block text-sm text-slate-200">Email address</label>
            <div className="relative">
              <Mail className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                id="reset-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-xl border border-white/10 bg-slate-950/80 py-3 pl-10 pr-3 text-white outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-500/20"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white shadow-lg shadow-violet-950/40 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <LoaderCircle className="h-5 w-5 animate-spin" /> : null}
            {loading ? 'Sending code...' : 'Send OTP'}
          </button>
        </form>

        <Link to="/login" className="mt-6 inline-flex items-center gap-2 text-sm font-medium text-violet-300 transition hover:text-violet-200">
          <ArrowLeft className="h-4 w-4" />
          Back to Login
        </Link>
      </div>
    </motion.div>
  );
}

export default ForgotPasswordPage;
