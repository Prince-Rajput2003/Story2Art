import { LogOut, Sparkles, Wand2 } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const navItems = [
  { to: '/', label: 'Home' },
  { to: '/generator', label: 'Generator' },
  { to: '/gallery', label: 'Gallery' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/about', label: 'About' },
  { to: '/profile', label: 'Profile' },
];

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <NavLink to="/" className="flex items-center gap-3 text-white">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 shadow-glow">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="text-lg font-extrabold tracking-tight">Story2Art</div>
            <div className="text-[10px] uppercase tracking-[0.2em] text-violet-200/80">AI Story Studio</div>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-4 rounded-full border border-violet-400/20 bg-white/5 px-3 py-2 md:flex">
          {navItems.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `rounded-full px-3 py-2 text-sm font-medium transition ${
                  isActive ? 'bg-violet-500 text-white shadow-glow' : 'text-slate-300 hover:text-white'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
          {user?.role === 'admin' && (
            <NavLink to="/admin" className={({ isActive }) => `rounded-full px-3 py-2 text-sm font-medium ${isActive ? 'bg-violet-500 text-white' : 'text-slate-300 hover:text-white'}`}>
              Admin
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <div className="hidden rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-slate-200 sm:block">
                {user.credits ?? 0} credits
              </div>
              <button type="button" onClick={handleLogout} className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-slate-200">
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </>
          ) : (
            <NavLink
              to="/login"
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-violet-900/40 transition hover:brightness-110"
            >
              <Wand2 className="h-4 w-4" />
              Login
            </NavLink>
          )}
        </div>
      </div>
    </header>
  );
}

export default Navbar;
