import { useEffect, useState } from 'react';
import { getCurrentUser, normalizeApiError, updateProfile } from '../services/api';

function ProfilePage() {
  const [profile, setProfile] = useState({ name: '', bio: '', country: 'IN', timezone: 'UTC' });
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const { data } = await getCurrentUser();
        setProfile({
          name: data.name,
          bio: data.profile?.bio || '',
          country: data.profile?.country || 'IN',
          timezone: data.profile?.timezone || 'UTC',
        });
      } catch (error) {
        console.error(error);
      }
    };

    loadProfile();
  }, []);

  const handleSave = async () => {
    setLoading(true);
    try {
      await updateProfile({
        name: profile.name,
        bio: profile.bio,
        country: profile.country,
        timezone: profile.timezone,
      });
      setMessage('Profile updated successfully.');
    } catch (error) {
      setMessage(normalizeApiError(error, 'Profile update failed.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl pb-10">
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Profile</p>
        <h1 className="text-3xl font-bold text-white">Account settings</h1>

        {message && <div className="mt-4 rounded-xl border border-violet-500/30 bg-violet-500/10 p-3 text-sm text-violet-100">{message}</div>}

        <div className="mt-6 space-y-4">
          <div>
            <label className="mb-2 block text-sm text-slate-200">Name</label>
            <input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white" />
          </div>
          <div>
            <label className="mb-2 block text-sm text-slate-200">Bio</label>
            <textarea value={profile.bio} onChange={(e) => setProfile({ ...profile, bio: e.target.value })} rows={5} className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white" />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-2 block text-sm text-slate-200">Country</label>
              <input value={profile.country} onChange={(e) => setProfile({ ...profile, country: e.target.value })} className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white" />
            </div>
            <div>
              <label className="mb-2 block text-sm text-slate-200">Timezone</label>
              <input value={profile.timezone} onChange={(e) => setProfile({ ...profile, timezone: e.target.value })} className="w-full rounded-xl border border-white/10 bg-slate-950/80 px-3 py-3 text-white" />
            </div>
          </div>

          <button type="button" disabled={loading} onClick={handleSave} className="rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-5 py-3 font-semibold text-white disabled:opacity-60">
            {loading ? 'Saving...' : 'Save profile'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;
