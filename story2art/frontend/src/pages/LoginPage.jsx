import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn } from 'lucide-react';
import { motion } from 'framer-motion';
import { loginUser, normalizeApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const notice = location.state?.notice || location.state?.success || '';

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { data } = await loginUser(form);
      await login(data.token, data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(normalizeApiError(err, 'Login failed. Please check your credentials.'));
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
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-violet-900/20">
        <div className="mb-6 flex items-center gap-3 text-violet-200">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15">
            <LogIn className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-violet-300">Welcome back</p>
            <h2 className="text-2xl font-bold text-white">Sign in</h2>
          </div>
        </div>

        {notice && <div role="status" className="mb-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-sm text-emerald-200">{notice}</div>}
        {error && <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-slate-200">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white outline-none focus:border-violet-400"
              required
            />
          </div>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <label htmlFor="login-password" className="text-sm text-slate-200">Password</label>
              <Link to="/forgot-password" className="text-sm font-medium text-violet-300 transition hover:text-violet-200">
                Forgot Password?
              </Link>
            </div>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 pr-12 text-white outline-none focus:border-violet-400"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                className="absolute inset-y-0 right-3 text-slate-400 transition hover:text-white"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <button type="submit" disabled={loading} className="w-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white disabled:opacity-60">
            {loading ? 'Signing in...' : 'Login'}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-300">
          Don’t have an account?{' '}
          <Link to="/register" className="font-semibold text-violet-300">
            Create one
          </Link>
        </p>
      </div>
    </motion.div>
  );
}

export default LoginPage;
