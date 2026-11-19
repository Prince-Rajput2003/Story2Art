import { Mail, MessageCircle, Phone, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

function Footer() {
  return (
    <footer className="border-t border-white/10 bg-slate-950/80">
      <section aria-labelledby="support-heading" className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          className="rounded-[30px] border border-violet-400/20 bg-gradient-to-br from-violet-950/50 via-slate-900/80 to-slate-950 p-6 shadow-2xl shadow-violet-950/20 sm:p-9"
        >
          <div className="mx-auto max-w-2xl text-center">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.24em] text-violet-300">Story2Art support</p>
            <h2 id="support-heading" className="text-2xl font-bold text-white sm:text-3xl">Need Help? Contact Support</h2>
            <p className="mt-3 text-sm leading-6 text-slate-300 sm:text-base">
              Have questions or facing an issue? Our support team is here to help.
            </p>
          </div>

          <div className="mx-auto mt-8 grid max-w-3xl gap-3 sm:grid-cols-2">
            <a
              href="tel:9369838180"
              className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 transition hover:border-violet-400/40 hover:bg-violet-500/[0.08]"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-violet-500/15 text-violet-200 transition group-hover:bg-violet-500/25">
                <Phone className="h-5 w-5" />
              </span>
              <span>
                <span className="block text-xs text-slate-400">Call our support team</span>
                <span className="mt-1 block font-semibold text-white">9369838180</span>
              </span>
            </a>
            <a
              href="mailto:princelodhi293@gmail.com"
              className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/[0.04] p-4 transition hover:border-violet-400/40 hover:bg-violet-500/[0.08]"
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-fuchsia-500/15 text-fuchsia-200 transition group-hover:bg-fuchsia-500/25">
                <Mail className="h-5 w-5" />
              </span>
              <span className="min-w-0">
                <span className="block text-xs text-slate-400">Email support</span>
                <span className="mt-1 block break-all font-semibold text-white">princelodhi293@gmail.com</span>
              </span>
            </a>
          </div>

          <div className="mt-5 flex flex-col justify-center gap-3 sm:flex-row">
            <a
              href="https://wa.me/919369838180"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-emerald-500 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-400"
            >
              <MessageCircle className="h-4 w-4" />
              WhatsApp Support
            </a>
            <a
              href="mailto:princelodhi293@gmail.com"
              className="inline-flex items-center justify-center gap-2 rounded-full border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition hover:border-violet-300/50 hover:bg-white/10"
            >
              <Mail className="h-4 w-4" />
              Email Support
            </a>
          </div>
        </motion.div>
      </section>

      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-8 text-sm text-slate-300 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500">
              <Sparkles className="h-4 w-4" />
            </div>
            <div>
              <div className="font-semibold text-white">Story2Art</div>
              <div className="text-xs text-slate-400">Turn stories into visual worlds.</div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6">
            <span>Privacy First</span>
            <span>Creative AI</span>
            <span>OpenAI Powered</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
