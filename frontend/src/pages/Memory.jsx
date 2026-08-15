import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, X, Plus, Trash2 } from "lucide-react";
import { api, confidenceLabel } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

export default function Memory() {
  const [memories, setMemories] = useState([]);
  const [types, setTypes] = useState([]);
  const [filter, setFilter] = useState(null);
  const [q, setQ] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [editing, setEditing] = useState(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ type: "Insight", title: "", description: "" });

  const load = () => {
    api.memories({ type: filter || undefined, q: q || undefined }).then((d) => {
      setMemories(d.memories || []);
      setTypes(d.types || []);
    });
    api.pendingCandidates().then((d) => setCandidates(d.candidates || []));
  };
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filter, q]);

  const decide = async (c, keep) => {
    setCandidates((cs) => cs.filter((x) => x.id !== c.id));
    if (keep) await api.confirmCandidate(c.id);
    else await api.dismissCandidate(c.id);
    load();
  };

  const saveEdit = async () => {
    await api.updateMemory(editing.id, {
      title: editing.title, description: editing.description, type: editing.type,
    });
    setEditing(null);
    load();
  };

  const add = async () => {
    if (!form.title.trim()) return;
    await api.createMemory(form);
    setOpen(false);
    setForm({ type: "Insight", title: "", description: "" });
    load();
  };

  return (
    <div data-testid="memory-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">The foundation</span>
        <button onClick={() => setOpen(true)} data-testid="add-memory-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
          <Plus size={15} strokeWidth={1.5} /> Add
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-4">What Kukdi remembers</h1>
      <p className="text-[#8A8F8C] mb-10 max-w-xl">Everything here is yours to edit. Kukdi never keeps anything without your say.</p>

      {/* Candidates */}
      <AnimatePresence>
        {candidates.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="mb-12 space-y-3" data-testid="memory-candidates">
            <p className="text-xs tracking-[0.18em] uppercase text-[#9DB0A3]">Awaiting your confirmation</p>
            {candidates.map((c) => (
              <div key={c.id} className="bg-[#EFECE7] rounded-2xl px-5 py-4 flex items-start justify-between gap-4" data-testid={`memory-candidate-${c.id}`}>
                <div>
                  <span className="text-[10px] tracking-[0.15em] uppercase text-[#8A8F8C]">{c.type}</span>
                  <p className="text-[#2C2D2B] mt-1">{c.title}</p>
                  <p className="text-sm text-[#8A8F8C]">{c.description}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button onClick={() => decide(c, true)} data-testid={`memory-candidate-keep-${c.id}`} className="h-9 w-9 rounded-full bg-[#D4DDD7] flex items-center justify-center hover:bg-[#9DB0A3] transition-colors"><Check size={16} /></button>
                  <button onClick={() => decide(c, false)} data-testid={`memory-candidate-dismiss-${c.id}`} className="h-9 w-9 rounded-full bg-[#E6E2DC] text-[#8A8F8C] flex items-center justify-center hover:bg-[#E2DFD8] transition-colors"><X size={16} /></button>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2 mb-8" data-testid="memory-filters">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search…"
          data-testid="memory-search"
          className="bg-[#EFECE7] rounded-full px-4 py-1.5 text-sm outline-none focus:ring-1 focus:ring-[#9DB0A3] mr-2"
        />
        <button onClick={() => setFilter(null)} data-testid="memory-filter-all" className={`text-xs tracking-[0.12em] uppercase px-3 py-1.5 rounded-full transition-colors ${!filter ? "text-[#2C2D2B]" : "text-[#8A8F8C] hover:text-[#5C605A]"}`}>All</button>
        {types.map((t) => (
          <button key={t} onClick={() => setFilter(t)} data-testid={`memory-filter-${t}`} className={`text-xs tracking-[0.12em] uppercase px-3 py-1.5 rounded-full transition-colors ${filter === t ? "text-[#2C2D2B]" : "text-[#8A8F8C] hover:text-[#5C605A]"}`}>{t}</button>
        ))}
      </div>

      {/* Memories */}
      <div className="space-y-6" data-testid="memory-list">
        {memories.map((m) => (
          <div key={m.id} className="border-b border-[#E2DFD8] pb-6 group" data-testid={`memory-${m.id}`}>
            <div className="flex items-baseline justify-between mb-1">
              <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{m.type}</span>
              <span className="text-[10px] tracking-[0.15em] uppercase text-[#8A8F8C]">{confidenceLabel(m.confidence)} confidence</span>
            </div>
            <h3 className="text-xl text-[#2C2D2B]">{m.title}</h3>
            {m.description && <p className="text-[#5C605A] mt-1 leading-relaxed">{m.description}</p>}
            <div className="flex gap-4 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <button onClick={() => setEditing({ ...m })} data-testid={`memory-edit-${m.id}`} className="text-xs text-[#8A8F8C] hover:text-[#2C2D2B]">Edit</button>
              <button onClick={async () => { await api.confirmMemory(m.id); load(); }} data-testid={`memory-confirm-${m.id}`} className="text-xs text-[#8A8F8C] hover:text-[#2C2D2B]">Still true</button>
              <button onClick={async () => { await api.archiveMemory(m.id); load(); }} data-testid={`memory-archive-${m.id}`} className="text-xs text-[#8A8F8C] hover:text-[#a9564a] flex items-center gap-1"><Trash2 size={12} /> Forget</button>
            </div>
          </div>
        ))}
      </div>

      {/* Edit modal */}
      <Modal open={!!editing} onClose={() => setEditing(null)} title="Edit memory" testId="memory-edit-modal">
        {editing && (
          <>
            <Field label="Type">
              <select className={inputClass} value={editing.type} onChange={(e) => setEditing({ ...editing, type: e.target.value })} data-testid="memory-edit-type">
                {["Profile","Preference","Goal","Person","Routine","Habit","Academic","Career","Decision","Insight","Context","Event"].map((t) => <option key={t}>{t}</option>)}
              </select>
            </Field>
            <Field label="Title"><input className={inputClass} value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} data-testid="memory-edit-title" /></Field>
            <Field label="Description"><textarea className={inputClass} rows={3} value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} data-testid="memory-edit-description" /></Field>
            <PrimaryButton onClick={saveEdit} data-testid="memory-edit-save">Save</PrimaryButton>
          </>
        )}
      </Modal>

      {/* Add modal */}
      <Modal open={open} onClose={() => setOpen(false)} title="Add a memory" testId="memory-add-modal">
        <Field label="Type">
          <select className={inputClass} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} data-testid="memory-add-type">
            {["Profile","Preference","Goal","Person","Routine","Habit","Academic","Career","Decision","Insight","Context","Event"].map((t) => <option key={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="Title"><input className={inputClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="memory-add-title" /></Field>
        <Field label="Description"><textarea className={inputClass} rows={3} value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} data-testid="memory-add-description" /></Field>
        <PrimaryButton onClick={add} data-testid="memory-add-save">Add memory</PrimaryButton>
      </Modal>
    </div>
  );
}
