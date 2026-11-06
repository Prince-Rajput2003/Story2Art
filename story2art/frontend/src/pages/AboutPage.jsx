import { Layers3, Palette, ShieldCheck, Sparkles } from 'lucide-react';

const stack = ['React.js', 'Vite', 'Tailwind CSS', 'Framer Motion', 'FastAPI', 'SQLAlchemy', 'OpenAI API', 'SQLite'];
const features = [
  'Prompt enhancement for richer image direction',
  'Multiple visual styles and aspect ratios',
  'Secure backend image serving and data validation',
  'Gallery management with downloads and deletions',
];

function AboutPage() {
  return (
    <div className="space-y-8 pb-10">
      <section className="rounded-[30px] border border-white/10 bg-slate-900/80 p-8">
        <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">About Story2Art</p>
        <h1 className="text-3xl font-bold text-white">A polished creative tool for turning stories into art.</h1>
        <p className="mt-4 max-w-3xl text-lg text-slate-300">
          Story2Art combines AI image generation, prompt enhancement, and a sleek gallery experience to help users transform written ideas into beautiful, shareable visuals.
        </p>
      </section>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500">
            <Layers3 className="h-5 w-5" />
          </div>
          <h2 className="mb-4 text-2xl font-bold text-white">Project features</h2>
          <ul className="space-y-3 text-slate-300">
            {features.map((feature) => (
              <li key={feature} className="flex items-start gap-3">
                <span className="mt-1 inline-block h-2 w-2 rounded-full bg-violet-400" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500">
            <Palette className="h-5 w-5" />
          </div>
          <h2 className="mb-4 text-2xl font-bold text-white">Technology stack</h2>
          <div className="flex flex-wrap gap-2">
            {stack.map((tech) => (
              <span key={tech} className="rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1.5 text-sm text-violet-100">
                {tech}
              </span>
            ))}
          </div>
        </div>
      </div>

      <section className="grid gap-6 md:grid-cols-3">
        {[
          { icon: Sparkles, title: 'AI-first workflow', text: 'Thoughtful storytelling and automatic prompt enhancement fuel more compelling visual output.' },
          { icon: ShieldCheck, title: 'Secure by default', text: 'Sensitive keys remain on the backend and generated files are validated before serving.' },
          { icon: Layers3, title: 'Production-ready structure', text: 'Modular FastAPI routes, SQLAlchemy models, and a polished Vite frontend support scalable growth.' },
        ].map(({ icon: Icon, title, text }) => (
          <div key={title} className="rounded-[26px] border border-white/10 bg-slate-900/80 p-6">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500">
              <Icon className="h-5 w-5" />
            </div>
            <h3 className="mb-2 text-xl font-semibold text-white">{title}</h3>
            <p className="text-slate-300">{text}</p>
          </div>
        ))}
      </section>
    </div>
  );
}

export default AboutPage;
