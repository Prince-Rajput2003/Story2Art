import { useEffect, useState } from 'react';
import { getAdminDashboard, getAdminUsers, toggleUserStatus, changeUserRole, adjustCredits, normalizeApiError } from '../services/api';

function AdminPage() {
  const [stats, setStats] = useState({ summary: {} });
  const [users, setUsers] = useState([]);
  const [message, setMessage] = useState('');

  const load = async () => {
    try {
      const [dashboardRes, usersRes] = await Promise.all([getAdminDashboard(), getAdminUsers()]);
      setStats(dashboardRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      setMessage(normalizeApiError(error, 'Admin access unavailable.'));
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleToggleStatus = async (userId) => {
    try {
      await toggleUserStatus(userId);
      setMessage('User status updated.');
      load();
    } catch (error) {
      setMessage(normalizeApiError(error, 'Failed to update user status.'));
    }
  };

  const handleChangeRole = async (userId, role) => {
    try {
      await changeUserRole(userId, role);
      setMessage('Role updated.');
      load();
    } catch (error) {
      setMessage(normalizeApiError(error, 'Failed to update role.'));
    }
  };

  const handleAdjustCredits = async (userId, amount) => {
    try {
      await adjustCredits(userId, amount);
      setMessage('Credits adjusted.');
      load();
    } catch (error) {
      setMessage(normalizeApiError(error, 'Failed to adjust credits.'));
    }
  };

  return (
    <div className="space-y-8 pb-10">
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Admin</p>
        <h1 className="text-3xl font-bold text-white">Admin dashboard</h1>
      </div>

      {message && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-3 text-sm text-violet-100">{message}</div>}

      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
          <div className="text-sm text-slate-400">Total users</div>
          <div className="mt-2 text-3xl font-bold text-white">{stats.summary.total_users ?? 0}</div>
        </div>
        <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
          <div className="text-sm text-slate-400">Total images</div>
          <div className="mt-2 text-3xl font-bold text-white">{stats.summary.total_images ?? 0}</div>
        </div>
        <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
          <div className="text-sm text-slate-400">Revenue</div>
          <div className="mt-2 text-3xl font-bold text-white">₹{stats.summary.total_revenue ?? 0}</div>
        </div>
      </div>

      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-6">
        <h2 className="mb-4 text-xl font-semibold text-white">User management</h2>
        <div className="space-y-3">
          {users.map((user) => (
            <div key={user.id} className="flex flex-col gap-3 rounded-2xl border border-white/10 bg-slate-950/60 p-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="font-semibold text-white">{user.name}</div>
                <div className="text-sm text-slate-400">{user.email}</div>
              </div>
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => handleToggleStatus(user.id)} className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-slate-200">{user.is_active ? 'Disable' : 'Enable'}</button>
                <button type="button" onClick={() => handleChangeRole(user.id, user.role === 'admin' ? 'user' : 'admin')} className="rounded-full border border-white/10 px-3 py-1.5 text-sm text-slate-200">{user.role === 'admin' ? 'Demote' : 'Promote'}</button>
                <button type="button" onClick={() => handleAdjustCredits(user.id, 25)} className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-sm text-emerald-200">+25</button>
                <button type="button" onClick={() => handleAdjustCredits(user.id, -10)} className="rounded-full border border-rose-500/30 bg-rose-500/10 px-3 py-1.5 text-sm text-rose-200">-10</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AdminPage;
