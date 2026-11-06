import { useState } from 'react';
import { Download, Loader2, RefreshCcw, Sparkles, Wand2 } from 'lucide-react';
import { motion } from 'framer-motion';
import { enhanceStory, generateStoryImage, getCurrentUser, normalizeApiError } from '../services/api';
import { useAuth } from '../context/AuthContext';

const styleOptions = ['Realistic Photography', 'Cinematic', 'Anime', '3D Render', 'Digital Art', 'Fantasy', 'Oil Painting', 'Watercolor', 'Cartoon', 'Cyberpunk', 'Minimalist', 'Portrait Photography', 'Architecture', 'Landscape'];
const aspectOptions = ['1:1', '16:9', '9:16', '4:3', '3:4'];
const qualityOptions = ['low', 'medium', 'high'];

const starterStory = `A young explorer wanders through a glowing forest at sunrise, carrying a lantern while mysterious creatures watch from the trees. The air feels magical, the light is soft golden, and the atmosphere is full of wonder and adventure.`;

function GeneratorPage() {
  const [story, setStory] = useState(starterStory);
  const [style, setStyle] = useState('Cinematic');
  const [aspectRatio, setAspectRatio] = useState('1:1');
  const [quality, setQuality] = useState('medium');
  const [negativePrompt, setNegativePrompt] = useState('');
  const [enhanceEnabled, setEnhanceEnabled] = useState(true);
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [status, setStatus] = useState({ type: '', message: '' });
  const { user, setUser } = useAuth();

  const characterCount = story.length;

  const handleEnhanceStory = async () => {
    if (!story.trim()) {
      setStatus({ type: 'error', message: 'Please add a story before enhancing it.' });
      return;
    }

    try {
      setIsEnhancing(true);
      const { data } = await enhanceStory(story);
      setStory(data.enhanced_prompt);
      setStatus({ type: 'success', message: 'Your story has been enhanced for visual generation.' });
    } catch (error) {
      const message = normalizeApiError(error, 'Unable to enhance the story right now.');
      setStatus({ type: 'error', message });
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleGenerate = async () => {
    if (!story.trim()) {
      setStatus({ type: 'error', message: 'The story field is empty. Add a story before generating an image.' });
      return;
    }

    setIsLoading(true);
    setStatus({ type: '', message: '' });

    try {
      const { data } = await generateStoryImage({
        story,
        image_style: style,
        aspect_ratio: aspectRatio,
        quality,
        enhance_story: enhanceEnabled,
        negative_prompt: negativePrompt,
      });

      if (!data?.image || !data.image.image_url) {
        throw new Error('The image response from the backend was missing a valid URL.');
      }

      setGeneratedImage(data.image);
      const { data: userData } = await getCurrentUser();
      setUser(userData);
      setStatus({ type: 'success', message: 'Image generated successfully. Your artwork is ready to download.' });
    } catch (error) {
      const message = normalizeApiError(error, 'Image generation failed. Please verify your API configuration.');
      setStatus({ type: 'error', message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-8 pb-10">
      <div className="rounded-[30px] border border-violet-500/20 bg-slate-900/80 p-6 shadow-2xl shadow-violet-900/10 sm:p-8">
        <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="mb-2 text-sm font-semibold uppercase tracking-[0.25em] text-violet-300">Story to image</p>
            <h1 className="text-3xl font-bold text-white">Creative generator</h1>
          </div>
          <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-300">
            {characterCount} characters
          </div>
        </div>

        <div className="space-y-5">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">Your story</span>
            <textarea
              value={story}
              onChange={(e) => setStory(e.target.value)}
              rows={10}
              maxLength={2500}
              placeholder="Write the story you want to turn into an image..."
              className="w-full rounded-2xl border border-violet-400/20 bg-slate-950/80 p-4 text-base text-slate-100 outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-500/20"
            />
          </label>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={handleEnhanceStory}
              disabled={isEnhancing}
              className="inline-flex items-center gap-2 rounded-full border border-violet-400/40 bg-violet-500/10 px-4 py-2.5 text-sm font-semibold text-violet-100 transition hover:border-violet-400/60 hover:bg-violet-500/20 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isEnhancing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
              {isEnhancing ? 'Enhancing...' : 'Enhance Story'}
            </button>

            <button
              type="button"
              onClick={handleGenerate}
              disabled={isLoading}
              className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-900/40 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Wand2 className="h-4 w-4" />}
              {isLoading ? 'Generating...' : 'Generate Image'}
            </button>
          </div>

          <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-slate-300">
            <input
              id="enhance-toggle"
              type="checkbox"
              checked={enhanceEnabled}
              onChange={(e) => setEnhanceEnabled(e.target.checked)}
              className="h-4 w-4 rounded border-violet-500 bg-slate-900 text-violet-500"
            />
            <label htmlFor="enhance-toggle">Enhance story prompt before image generation</label>
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-200">Negative prompt</label>
            <textarea
              value={negativePrompt}
              onChange={(e) => setNegativePrompt(e.target.value)}
              rows={3}
              placeholder="Example: blurry face, distorted hands, low detail, text artifacts"
              className="w-full rounded-2xl border border-violet-400/20 bg-slate-950/80 p-4 text-base text-slate-100 outline-none transition focus:border-violet-400/60 focus:ring-2 focus:ring-violet-500/20"
            />
          </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
        <section className="rounded-[30px] border border-white/10 bg-slate-900/80 p-6">
          <div className="space-y-5">
            <div className="flex items-center justify-between text-sm text-slate-300">
              <span>Available credits</span>
              <span className="rounded-full border border-violet-500/30 bg-violet-500/10 px-3 py-1 text-violet-100">{user?.credits ?? 0}</span>
            </div>

            <div>
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Style</p>
              <div className="flex flex-wrap gap-2">
                {styleOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setStyle(option)}
                    className={`rounded-full border px-3 py-2 text-sm transition ${
                      style === option
                        ? 'border-violet-400 bg-violet-500/20 text-violet-100'
                        : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-violet-400/40'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Aspect ratio</p>
              <div className="flex gap-2">
                {aspectOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setAspectRatio(option)}
                    className={`rounded-full border px-4 py-2 text-sm transition ${
                      aspectRatio === option
                        ? 'border-violet-400 bg-violet-500/20 text-violet-100'
                        : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-violet-400/40'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Quality</p>
              <div className="flex gap-2">
                {qualityOptions.map((option) => (
                  <button
                    key={option}
                    type="button"
                    onClick={() => setQuality(option)}
                    className={`rounded-full border px-4 py-2 text-sm capitalize transition ${
                      quality === option
                        ? 'border-violet-400 bg-violet-500/20 text-violet-100'
                        : 'border-white/10 bg-slate-950/60 text-slate-300 hover:border-violet-400/40'
                    }`}
                  >
                    {option}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="rounded-[30px] border border-white/10 bg-slate-900/80 p-6">
          {status.message && (
            <div
              className={`mb-5 rounded-2xl border px-4 py-3 text-sm ${
                status.type === 'success'
                  ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-200'
                  : 'border-rose-500/30 bg-rose-500/10 text-rose-200'
              }`}
            >
              {status.message}
            </div>
          )}

          {generatedImage ? (
            <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="space-y-4">
              <img
                src={generatedImage.image_url}
                alt="Generated Story2Art preview"
                className="h-[420px] w-full rounded-[24px] object-cover shadow-2xl shadow-violet-950/50"
              />
              <div className="flex flex-wrap gap-3">
                <a
                  href={generatedImage.image_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500 px-4 py-2.5 text-sm font-semibold text-white"
                >
                  <Download className="h-4 w-4" />
                  Download Image
                </a>

                <button
                  type="button"
                  onClick={handleGenerate}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-slate-950/70 px-4 py-2.5 text-sm font-semibold text-slate-200"
                >
                  <RefreshCcw className="h-4 w-4" />
                  Regenerate Image
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="flex h-[420px] items-center justify-center rounded-[24px] border border-dashed border-violet-500/30 bg-slate-950/50 p-6 text-center text-slate-300">
              <div>
                <Wand2 className="mx-auto mb-4 h-12 w-12 text-violet-300" />
                <p className="text-lg font-semibold text-white">Your generated art will appear here.</p>
                <p className="mt-2 text-sm text-slate-400">Add a great story and click generate to create an AI illustration.</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

export default GeneratorPage;
