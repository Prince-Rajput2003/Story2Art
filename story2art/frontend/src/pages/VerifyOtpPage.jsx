import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, KeyRound, LoaderCircle, RotateCw, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  normalizeApiError,
  resendPasswordResetOtp,
  verifyPasswordResetOtp,
} from '../services/api';

function formatTime(seconds) {
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;
}

function VerifyOtpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';
  const [otp, setOtp] = useState(Array(6).fill(''));
  const [secondsLeft, setSecondsLeft] = useState(300);
  const [resendSeconds, setResendSeconds] = useState(60);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const inputs = useRef([]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setSecondsLeft((remaining) => Math.max(0, remaining - 1));
      setResendSeconds((remaining) => Math.max(0, remaining - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, []);

  if (!email) {
    return <NavigateToForgotPassword />;
  }

  const updateDigit = (index, value) => {
    const digit = value.replace(/\D/g, '').slice(-1);
    setOtp((current) => current.map((item, itemIndex) => (itemIndex === index ? digit : item)));
    if (digit && index < 5) inputs.current[index + 1]?.focus();
    setError('');
  };

  const handlePaste = (event) => {
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;
    event.preventDefault();
    setOtp(Array.from({ length: 6 }, (_, index) => pasted[index] || ''));
    inputs.current[Math.min(pasted.length, 6) - 1]?.focus();
    setError('');
  };

  const handleVerify = async (event) => {
    event.preventDefault();
    const code = otp.join('');
    if (code.length !== 6) {
      setError('Enter all six digits to continue.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const { data } = await verifyPasswordResetOtp({ email, otp: code });
      navigate('/reset-password', { state: { resetToken: data.reset_token } });
    } catch (verificationError) {
      setError(normalizeApiError(verificationError, 'That code is invalid or has expired.'));
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResending(true);
    setError('');
    setMessage('');
    try {
      const { data } = await resendPasswordResetOtp({ email });
      setMessage(data.message);
      setOtp(Array(6).fill(''));
      setSecondsLeft(300);
      setResendSeconds(60);
      inputs.current[0]?.focus();
    } catch (resendError) {
      setError(normalizeApiError(resendError, 'Unable to resend the code. Please try again.'));
    } finally {
      setResending(false);
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
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-violet-300">Email verification</p>
            <h1 className="text-2xl font-bold text-white">Verify Your Email</h1>
          </div>
        </div>
        <p className="mb-2 text-sm leading-6 text-slate-300">
          We have sent a 6-digit verification code to your registered email.
        </p>
        <p className="mb-6 break-all text-sm text-violet-200">{email}</p>

        {error && <div role="alert" className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}
        {message && <div role="status" className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">{message}</div>}

        <form onSubmit={handleVerify} className="space-y-6">
          <fieldset>
            <legend className="mb-3 text-sm text-slate-200">6-digit verification code</legend>
            <div className="flex justify-between gap-2" onPaste={handlePaste}>
              {otp.map((digit, index) => (
                <input
                  key={index}
                  ref={(element) => { inputs.current[index] = element; }}
                  type="text"
                  inputMode="numeric"
                  autoComplete={index === 0 ? 'one-time-code' : 'off'}
                  aria-label={`Verification digit ${index + 1}`}
                  value={digit}
                  onChange={(event) => updateDigit(index, event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Backspace' && !digit && index > 0) inputs.current[index - 1]?.focus();
                  }}
                  className="h-11 min-w-0 w-full max-w-12 flex-1 rounded-xl border border-white/10 bg-slate-950/80 text-center text-xl font-bold text-white outline-none transition focus:border-violet-400 focus:ring-2 focus:ring-violet-500/20 sm:h-14 sm:max-w-14"
                  maxLength={1}
                  required
                />
              ))}
            </div>
          </fieldset>

          <div className="flex items-center justify-center gap-2 text-sm text-slate-400" aria-live="polite">
            <KeyRound className="h-4 w-4 text-violet-300" />
            {secondsLeft > 0 ? `Code expires in ${formatTime(secondsLeft)}` : 'This code has expired.'}
          </div>

          <button
            type="submit"
            disabled={loading || secondsLeft === 0}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white shadow-lg shadow-violet-950/40 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? <LoaderCircle className="h-5 w-5 animate-spin" /> : null}
            {loading ? 'Verifying...' : 'Verify OTP'}
          </button>
        </form>

        <button
          type="button"
          onClick={handleResend}
          disabled={resending || resendSeconds > 0}
          className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-3 text-sm font-semibold text-slate-200 transition hover:border-violet-400/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {resending ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RotateCw className="h-4 w-4" />}
          {resending ? 'Sending...' : resendSeconds > 0 ? `Resend code in ${formatTime(resendSeconds)}` : 'Resend OTP'}
        </button>

        <Link to="/forgot-password" className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-violet-300 transition hover:text-violet-200">
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
      </div>
    </motion.div>
  );
}

function NavigateToForgotPassword() {
  const navigate = useNavigate();
  useEffect(() => {
    navigate('/forgot-password', { replace: true });
  }, [navigate]);
  return null;
}

export default VerifyOtpPage;
