import { useEffect, useMemo, useState } from 'react';
import { Download, ImageIcon, Search, Trash2 } from 'lucide-react';
import { deleteImage, getGallery } from '../services/api';

function GalleryPage() {
  const [gallery, setGallery] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('All');
  const [page, setPage] = useState(1);
  const pageSize = 6;

  const fetchGallery = async () => {
    try {
      const { data } = await getGallery();
      setGallery(data);
      setError('');
    } catch (err) {
      setError('Unable to load the gallery at the moment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGallery();
  }, []);

  const filteredGallery = useMemo(() => {
    const lowerSearch = searchTerm.toLowerCase();
    return gallery.filter((item) => {
      const matchesText = !lowerSearch || item.original_story.toLowerCase().includes(lowerSearch) || item.enhanced_prompt.toLowerCase().includes(lowerSearch);
      const matchesStyle = selectedStyle === 'All' || item.image_style === selectedStyle;
      return matchesText && matchesStyle;
    });
  }, [gallery, searchTerm, selectedStyle]);

  const totalPages = Math.max(1, Math.ceil(filteredGallery.length / pageSize));
  const pageItems = filteredGallery.slice((page - 1) * pageSize, page * pageSize);

  useEffect(() => {
    setPage(1);
  }, [searchTerm, selectedStyle]);

  const handleDelete = async (imageId) => {
    try {
      await deleteImage(imageId);
      setGallery((prev) => prev.filter((item) => item.id !== imageId));
    } catch (err) {
      setError('Could not delete the selected image.');
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-lg text-slate-300">
        Loading gallery...
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-10">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.2em] text-violet-300">Gallery</p>
          <h1 className="text-3xl font-bold text-white">Your generated artwork</h1>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-slate-300">
          {filteredGallery.length} item{filteredGallery.length === 1 ? '' : 's'}
        </div>
      </div>

      <div className="rounded-[26px] border border-white/10 bg-slate-900/80 p-4">
        <div className="flex flex-col gap-4 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <input value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search stories or prompts" className="w-full rounded-full border border-white/10 bg-slate-950/80 py-2.5 pl-10 pr-4 text-sm text-white" />
          </div>
          <select value={selectedStyle} onChange={(e) => setSelectedStyle(e.target.value)} className="rounded-full border border-white/10 bg-slate-950/80 px-3 py-2.5 text-sm text-white">
            <option>All</option>
            {[...new Set(gallery.map((item) => item.image_style))].map((style) => (
              <option key={style}>{style}</option>
            ))}
          </select>
        </div>
      </div>

      {error && <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div>}

      {!filteredGallery.length ? (
        <div className="rounded-[30px] border border-dashed border-violet-500/30 bg-slate-900/70 p-8 text-center">
          <ImageIcon className="mx-auto mb-4 h-12 w-12 text-violet-300" />
          <h2 className="text-2xl font-semibold text-white">Your gallery is empty</h2>
          <p className="mt-2 text-slate-300">Generate your first image to start building a visual story library.</p>
        </div>
      ) : (
        <>
          <div className="image-grid">
            {pageItems.map((item) => (
              <div key={item.id} className="overflow-hidden rounded-[24px] border border-white/10 bg-slate-900/70 shadow-2xl shadow-slate-950/40">
                <img src={item.image_url} alt={item.original_story} className="h-64 w-full object-cover" />
                <div className="space-y-3 p-4">
                  <div className="flex items-center justify-between gap-3">
                    <span className="rounded-full bg-violet-500/15 px-2 py-1 text-xs font-medium text-violet-200">{item.image_style}</span>
                    <span className="text-xs text-slate-400">{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                  <h3 className="line-clamp-2 text-base font-semibold text-white">
                    {item.original_story.slice(0, 80)}{item.original_story.length > 80 ? '...' : ''}
                  </h3>
                  <div className="flex gap-2 pt-2">
                    <a href={item.image_url} target="_blank" rel="noreferrer" className="inline-flex flex-1 items-center justify-center gap-2 rounded-full bg-violet-500/15 px-3 py-2 text-sm font-medium text-violet-100">
                      <Download className="h-4 w-4" />
                      Download
                    </a>
                    <button type="button" onClick={() => handleDelete(item.id)} className="inline-flex items-center justify-center rounded-full border border-rose-500/30 bg-rose-500/10 p-2.5 text-rose-200 transition hover:bg-rose-500/20" aria-label="Delete image">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="flex justify-center gap-2">
            <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1} className="rounded-full border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-white disabled:opacity-40">Previous</button>
            <span className="rounded-full border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-slate-200">Page {page} / {totalPages}</span>
            <button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages} className="rounded-full border border-white/10 bg-slate-900/80 px-4 py-2 text-sm text-white disabled:opacity-40">Next</button>
          </div>
        </>
      )}
    </div>
  );
}

export default GalleryPage;
