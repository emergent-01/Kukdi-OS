import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Sparkles } from "lucide-react";
import { api } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

const EMPTY = { title: "", situation: "", task: "", action: "", result: "", themes: [], tags: ["star"] };
const STAR = [
  ["situation", "Situation"],
  ["task", "Task"],
  ["action", "Action"],
  ["result", "Result"],
];

export default function Stories() {
  const [stories, setStories] = useState([]);
  const [active, setActive] = useState(null);
  const [addOpen, setAddOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [polishing, setPolishing] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => api.stories().then((d) => setStories(d.stories || []));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!form.title.trim()) return;
    const themes = typeof form.themes === "string"
      ? form.themes.split(",").map((t) => t.trim()).filter(Boolean)
      : form.themes;
    await api.createStory({ ...form, themes });
    setAddOpen(false);
    setForm(EMPTY);
    load();
  };

  const saveActive = async () => {
    setSaving(true);
    try {
      await api.updateStory(active.id, {
        title: active.title, situation: active.situation, task: active.task,
        action: active.action, result: active.result,
      });
      load();
    } finally {
      setSaving(false);
    }
  };

  const polish = async () => {
    setPolishing(true);
    try {
      const updated = await api.polishStory(active.id);
      setActive(updated);
      load();
    } finally {
      setPolishing(false);
    }
  };

  return (
    <div data-testid="stories-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Story bank</span>
        <button onClick={() => setAddOpen(true)} data-testid="add-story-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
          <Plus size={15} strokeWidth={1.5} /> Add
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-3">Your stories, ready</h1>
      <p className="text-[#8A8F8C] mb-12 max-w-xl">Shape a STAR story once and let Kukdi polish it — then reuse it across every company.</p>

      <div className="space-y-10">
        {stories.map((s) => (
          <div key={s.id} className="border-b border-[#E2DFD8] pb-10 group" data-testid={`story-${s.id}`}>
            <div className="flex items-baseline justify-between">
              <button onClick={() => setActive(s)} data-testid={`story-open-${s.id}`} className="font-editorial text-3xl text-[#2C2D2B] text-left hover:text-[#5C605A] transition-colors">{s.title}</button>
              <div className="flex items-center gap-4">
                <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{s.status}</span>
                <button onClick={async () => { await api.deleteStory(s.id); load(); }} data-testid={`story-delete-${s.id}`} className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a]"><Trash2 size={15} /></button>
              </div>
            </div>
            <p className="text-[#5C605A] mt-2 max-w-2xl leading-relaxed line-clamp-2">{s.situation}</p>
            <div className="flex flex-wrap gap-2 mt-4">
              {(s.themes || []).map((t) => (
                <span key={t} className="text-xs text-[#5C605A] bg-[#EFECE7] rounded-full px-3 py-1 capitalize">{t}</span>
              ))}
              {(s.companies_used || []).length > 0 && (
                <span className="text-xs text-[#8A8F8C] px-2 py-1">Used at {s.companies_used.join(", ")}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Story editor / polisher */}
      <Modal open={!!active} onClose={() => setActive(null)} title={active?.title || "Story"} testId="story-modal">
        {active && (
          <>
            <Field label="Title"><input className={inputClass} value={active.title} onChange={(e) => setActive({ ...active, title: e.target.value })} data-testid="story-title" /></Field>
            {STAR.map(([key, label]) => (
              <Field key={key} label={label}>
                <textarea className={inputClass} rows={3} value={active[key] || ""} onChange={(e) => setActive({ ...active, [key]: e.target.value })} data-testid={`story-${key}`} />
              </Field>
            ))}

            {active.feedback && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="bg-[#EFECE7] rounded-2xl px-5 py-4 mb-6" data-testid="story-feedback">
                <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">Kukdi's note</span>
                <p className="text-[#5C605A] mt-1 italic font-editorial text-lg leading-snug">{active.feedback}</p>
              </motion.div>
            )}

            <div className="flex items-center gap-3">
              <button
                onClick={polish}
                data-testid="story-polish"
                disabled={polishing}
                className="flex items-center gap-2 bg-[#D4DDD7] text-[#2C2D2B] rounded-full px-6 py-3 text-sm hover:bg-[#9DB0A3] transition-colors disabled:opacity-40"
              >
                <Sparkles size={15} strokeWidth={1.5} className={polishing ? "animate-pulse" : ""} />
                {polishing ? "Polishing…" : "Polish with Kukdi"}
              </button>
              <PrimaryButton onClick={saveActive} data-testid="story-save" disabled={saving}>{saving ? "Saving…" : "Save"}</PrimaryButton>
            </div>
          </>
        )}
      </Modal>

      {/* Add story */}
      <Modal open={addOpen} onClose={() => setAddOpen(false)} title="New story" testId="story-add-modal">
        <Field label="Title"><input className={inputClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="story-add-title" /></Field>
        <Field label="Situation"><textarea className={inputClass} rows={2} value={form.situation} onChange={(e) => setForm({ ...form, situation: e.target.value })} data-testid="story-add-situation" /></Field>
        <Field label="Task"><textarea className={inputClass} rows={2} value={form.task} onChange={(e) => setForm({ ...form, task: e.target.value })} data-testid="story-add-task" /></Field>
        <Field label="Action"><textarea className={inputClass} rows={2} value={form.action} onChange={(e) => setForm({ ...form, action: e.target.value })} data-testid="story-add-action" /></Field>
        <Field label="Result"><textarea className={inputClass} rows={2} value={form.result} onChange={(e) => setForm({ ...form, result: e.target.value })} data-testid="story-add-result" /></Field>
        <Field label="Themes (comma separated)"><input className={inputClass} value={Array.isArray(form.themes) ? form.themes.join(", ") : form.themes} onChange={(e) => setForm({ ...form, themes: e.target.value })} data-testid="story-add-themes" placeholder="leadership, conflict, impact" /></Field>
        <PrimaryButton onClick={add} data-testid="story-add-save">Add story</PrimaryButton>
      </Modal>
    </div>
  );
}
