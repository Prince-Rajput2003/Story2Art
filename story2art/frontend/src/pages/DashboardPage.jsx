import { useEffect, useState } from 'react';
import { CreditCard, ImageIcon, Loader2, Sparkles } from 'lucide-react';
import { getCurrentUser, getGallery, getPaymentHistory } from '../services/api';

function DashboardPage() {
  const [user, setUser] = useState(null);
  const [gallery, setGallery] = useState([]);
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError('');

      try {
        const [userRes, galleryRes, paymentRes] = await Promise.all([
          getCurrentUser(),
          getGallery(),
          getPaymentHistory(),
        ]);

        setUser(userRes.data || null);
        setGallery(Array.isArray(galleryRes.data) ? galleryRes.data : []);
        setPayments(Array.isArray(paymentRes.data) ? paymentRes.data : []);
      } catch (error) {
        console.error('Dashboard load failed', error);
        setError('We could not load your dashboard. Please refresh the page or log in again.');
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center rounded-[30px] border border-white/10 bg-slate-900/80 p-8 text-slate-200">
        <div className="flex items-center gap-3">
          <Loader2 className="h-5 w-5 animate-spin text-violet-300" />
          <span>Loading dashboard...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[30px] border border-rose-500/30 bg-rose-500/10 p-8 text-rose-100">
        <h2 className="mb-2 text-xl font-semibold">Dashboard unavailable</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10">
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Dashboard</p>
        <h1 className="text-3xl font-bold text-white">Welcome back, {user?.name || 'creator'}</h1>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-[28px] border border-white/10 bg-slate-900/80 p-6">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15 text-violet-200"><Sparkles className="h-5 w-5" /></div>
          <div className="text-sm text-slate-400">Available credits</div>
          <div className="mt-2 text-3xl font-bold text-white">{user?.credits ?? 0}</div>
        </div>
        <div className="rounded-[28px] border border-white/10 bg-slate-900/80 p-6">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15 text-violet-200"><ImageIcon className="h-5 w-5" /></div>
          <div className="text-sm text-slate-400">Generated images</div>
          <div className="mt-2 text-3xl font-bold text-white">{gallery.length}</div>
        </div>
        <div className="rounded-[28px] border border-white/10 bg-slate-900/80 p-6">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-500/15 text-violet-200"><CreditCard className="h-5 w-5" /></div>
          <div className="text-sm text-slate-400">Payments</div>
          <div className="mt-2 text-3xl font-bold text-white">{payments.length}</div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-[28px] border border-white/10 bg-slate-900/80 p-6">
          <h2 className="mb-4 text-xl font-semibold text-white">Recent payment history</h2>
          {payments.length ? (
            <div className="space-y-3">
              {payments.slice(0, 5).map((payment) => (
                <div key={payment.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-slate-950/60 p-3">
                  <div>
                    <div className="font-medium text-white">₹{payment.amount}</div>
                    <div className="text-xs text-slate-400">{payment.status}</div>
                  </div>
                  <div className="text-xs text-slate-400">{new Date(payment.created_at).toLocaleDateString()}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400">No payment records yet.</div>
          )}
        </div>

        <div className="rounded-[28px] border border-white/10 bg-slate-900/80 p-6">
          <h2 className="mb-4 text-xl font-semibold text-white">Recent gallery items</h2>
          {gallery.length ? (
            <div className="space-y-3">
              {gallery.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-slate-950/60 p-3">
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-white">{item.image_style}</div>
                    <div className="text-xs text-slate-400">{new Date(item.created_at).toLocaleDateString()}</div>
                  </div>
                  <img src={item.image_url} alt={item.image_style} className="h-12 w-12 rounded-lg object-cover" />
                </div>
              ))}
            </div>
          ) : (
            <div className="text-slate-400">Your gallery is empty.</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DashboardPage;
