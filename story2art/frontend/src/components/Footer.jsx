import { Sparkles } from 'lucide-react';

function Footer() {
  return (
    <footer className="border-t border-white/10 bg-slate-950/80">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-10 text-sm text-slate-300 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
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
    </footer>
  );
}

export default Footer;
