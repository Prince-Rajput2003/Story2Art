import { useEffect, useState } from 'react';
import { Check, Crown } from 'lucide-react';
import { getPlans, normalizeApiError, startCheckout, verifyPayment } from '../services/api';
import { useAuth } from '../context/AuthContext';

const billingOptions = ['monthly', 'yearly'];

function PricingPage() {
  const { user } = useAuth();
  const [plans, setPlans] = useState([]);
  const [billing, setBilling] = useState('monthly');
  const [processing, setProcessing] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const { data } = await getPlans();
        setPlans(data);
      } catch (error) {
        setMessage('Unable to load subscription plans right now.');
      }
    };

    fetchPlans();
  }, []);

  const handleCheckout = async (plan) => {
    if (!user) {
      setMessage('Please log in before selecting a plan.');
      return;
    }

    setProcessing(plan.id);
    try {
      const { data } = await startCheckout({ plan_id: plan.id, billing_cycle: billing });
      const signed = {
        payment_id: `${data.gateway || 'test'}_${Date.now()}`,
        order_id: data.order_id,
        signature: 'backend-test-signature',
        plan_id: plan.id,
        test_mode: true,
      };
      await verifyPayment(signed);
      setMessage(`Your ${plan.name} plan is active in backend test mode.`);
    } catch (error) {
      setMessage(normalizeApiError(error, 'Payment verification failed.'));
    } finally {
      setProcessing('');
    }
  };

  return (
    <div className="space-y-8 pb-10">
      <div className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Pricing</p>
        <h1 className="text-3xl font-bold text-white">Flexible plans for creators and teams</h1>
        <div className="mt-6 inline-flex rounded-full border border-white/10 bg-slate-950/80 p-1">
          {billingOptions.map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setBilling(option)}
              className={`rounded-full px-4 py-2 text-sm font-medium ${billing === option ? 'bg-violet-500 text-white' : 'text-slate-300'}`}
            >
              {option === 'monthly' ? 'Monthly' : 'Yearly'}
            </button>
          ))}
        </div>
      </div>

      {message && <div className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-3 text-sm text-violet-100">{message}</div>}

      <div className="grid gap-6 lg:grid-cols-4">
        {plans.map((plan) => (
          <div key={plan.id} className={`rounded-[28px] border p-6 ${plan.slug === 'pro' ? 'border-violet-400 bg-violet-500/10' : 'border-white/10 bg-slate-900/80'}`}>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-2xl font-bold text-white">{plan.name}</h2>
              {plan.slug === 'pro' ? <Crown className="h-5 w-5 text-violet-200" /> : null}
            </div>
            <div className="mb-6 flex items-end gap-2">
              <span className="text-4xl font-black text-white">₹{billing === 'monthly' ? plan.price_monthly : plan.price_yearly}</span>
              <span className="pb-1 text-sm text-slate-400">/{billing === 'monthly' ? 'mo' : 'yr'}</span>
            </div>
            <ul className="space-y-3 text-sm text-slate-200">
              {(plan.features || []).map((feature) => (
                <li key={feature} className="flex items-start gap-2">
                  <Check className="mt-0.5 h-4 w-4 text-emerald-400" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
            <div className="mt-6 text-sm text-slate-300">{billing === 'monthly' ? plan.monthly_credits : plan.yearly_credits} monthly credits</div>
            <button
              type="button"
              onClick={() => handleCheckout(plan)}
              disabled={processing === plan.id}
              className="mt-5 w-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-3 font-semibold text-white disabled:opacity-60"
            >
              {processing === plan.id ? 'Processing...' : user ? 'Select plan' : 'Login to continue'}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

export default PricingPage;
