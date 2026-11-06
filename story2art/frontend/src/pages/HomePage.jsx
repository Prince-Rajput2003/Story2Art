import { ArrowRight, BookOpenText, CheckCircle2, ImagePlus, Sparkles, Wand2 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const featureList = [
  'Transform story ideas into cinematic visual prompts',
  'Choose from photorealistic, anime, fantasy, and more',
  'Save and revisit your AI-generated gallery',
];

const steps = [
  { title: 'Write your story', description: 'Describe the setting, emotion, mood, and key characters in rich detail.' },
  { title: 'Tune the style', description: 'Select the perfect image category and composition for your vision.' },
  { title: 'Generate and download', description: 'Create a polished image and save it to your gallery instantly.' },
];

function HomePage() {
  return (
    <div className="space-y-16 pb-10">
      <section className="relative overflow-hidden rounded-[32px] border border-violet-500/20 bg-slate-900/70 px-6 py-16 shadow-2xl shadow-violet-900/20 sm:px-10 lg:px-16">
        <div className="absolute inset-0 bg-hero-glow opacity-80" />
        <div className="relative grid items-center gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="space-y-8"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.25em] text-violet-200">
              <Sparkles className="h-3.5 w-3.5" />
              AI Visual Storytelling
            </div>

            <div className="space-y-4">
              <h1 className="max-w-xl text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl">
                Turn Your Stories Into AI Art
              </h1>
              <p className="max-w-lg text-lg text-slate-300">
                Create vivid images from your ideas, scenes, characters, and emotional narratives using elegant AI-powered generation.
              </p>
            </div>

            <div className="flex flex-wrap gap-4">
              <Link
                to="/generator"
                className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-6 py-3 font-semibold text-white shadow-lg shadow-violet-900/40 transition hover:brightness-110"
              >
                Generate Image
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                to="/gallery"
                className="rounded-full border border-white/10 bg-white/5 px-6 py-3 font-semibold text-slate-200 transition hover:border-violet-400/40 hover:text-white"
              >
                View Gallery
              </Link>
            </div>

            <div className="grid gap-4 pt-3 sm:grid-cols-3">
              {['100% Story-driven', 'Multiple art styles', 'Instant downloads'].map((stat) => (
                <div key={stat} className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-slate-200">
                  {stat}
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="relative"
          >
            <div className="glass-panel card-sheen overflow-hidden rounded-[28px] p-3">
              <img
                src="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=1200&q=80"
                alt="Story2Art sample artwork"
                className="h-[430px] w-full rounded-[22px] object-cover"
              />
              <div className="absolute inset-x-6 bottom-6 rounded-2xl border border-white/15 bg-slate-950/70 p-4 backdrop-blur-md">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <div>
                    <div className="font-semibold text-white">Moonlit Forest</div>
                    <div className="text-slate-300">Story prompt sample</div>
                  </div>
                  <div className="rounded-full bg-violet-500/20 px-2 py-1 text-xs font-semibold text-violet-200">Fantasy</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="space-y-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Features</p>
            <h2 className="text-3xl font-bold text-white">Built for storytellers who want cinematic visuals</h2>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-3">
          {featureList.map((item, idx) => (
            <motion.div
              key={item}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="gradient-border rounded-3xl p-6"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white">
                {idx === 0 ? <BookOpenText className="h-5 w-5" /> : idx === 1 ? <ImagePlus className="h-5 w-5" /> : <CheckCircle2 className="h-5 w-5" />}
              </div>
              <p className="text-lg font-semibold text-white">{item}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="rounded-[30px] border border-white/10 bg-slate-900/70 p-6 sm:p-8">
        <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">How it works</p>
        <div className="grid gap-6 md:grid-cols-3">
          {steps.map((step, index) => (
            <div key={step.title} className="rounded-3xl border border-white/10 bg-slate-950/60 p-5">
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 font-bold text-white">
                {index + 1}
              </div>
              <h3 className="mb-2 text-xl font-semibold text-white">{step.title}</h3>
              <p className="text-slate-300">{step.description}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

export default HomePage;
