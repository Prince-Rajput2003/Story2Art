import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { UserPlus } from 'lucide-react';
import { normalizeApiError, registerUser } from '../services/api';
import { useAuth } from '../context/AuthContext';

function RegisterPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { data } = await registerUser(form);
      await login(data.token, data.user);
      navigate('/dashboard');
    } catch (err) {
      setError(normalizeApiError(err, 'Registration failed. Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-md py-10">
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8 shadow-2xl shadow-violet-900/20">
        <div className="mb-6 flex items-center gap-3 text-violet-200">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15">
            <UserPlus className="h-5 w-5" />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.22em] text-violet-300">New account</p>
            <h2 className="text-2xl font-bold text-white">Create account</h2>
          </div>
        </div>

        {error && <div className="mb-4 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-200">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-2 block text-sm text-slate-200">Full name</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white outline-none focus:border-violet-400"
              required
            />
          </div>
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
            <label className="mb-2 block text-sm text-slate-200">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white outline-none focus:border-violet-400"
              minLength={8}
              required
            />
          </div>

          <button type="submit" disabled={loading} className="w-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white disabled:opacity-60">
            {loading ? 'Creating account...' : 'Register'}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-slate-300">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-violet-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default RegisterPage;
