import { useEffect, useRef, useState } from "react";
import { Plus, Trash2, Upload } from "lucide-react";
import { api, BACKEND } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

const KIND_LABEL = { note: "Note", book: "Book", framework: "Framework", case: "Case", document: "Document" };

export default function Knowledge() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [form, setForm] = useState({ kind: "note", title: "", summary: "", body: "" });
  const [mode, setMode] = useState("contains");
  const [semanticResults, setSemanticResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const fileRef = useRef(null);

  const load = () => api.knowledge(mode === "contains" ? (q || undefined) : undefined).then((d) => setItems(d.items || []));
  useEffect(() => { if (mode === "contains") load(); /* eslint-disable-next-line */ }, [q, mode]);

  const runSemantic = async (e) => {
    e?.preventDefault();
    if (mode !== "meaning" || !q.trim()) return;
    setSearching(true);
    setSemanticResults(null);
    try {
      const d = await api.searchKnowledge(q.trim());
      setSemanticResults(d.results || []);
    } finally {
      setSearching(false);
    }
  };

  const add = async () => {
    if (!form.title.trim()) return;
    await api.createKnowledge(form);
    setOpen(false);
    setForm({ kind: "note", title: "", summary: "", body: "" });
    load();
  };

  const onFile = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.uploadKnowledge(fd);
      load();
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <div data-testid="knowledge-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Knowledge · Notes Inbox</span>
        <div className="flex items-center gap-5">
          <button onClick={() => fileRef.current?.click()} data-testid="upload-knowledge-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
            <Upload size={15} strokeWidth={1.5} /> {uploading ? "Uploading…" : "Upload"}
          </button>
          <button onClick={() => setOpen(true)} data-testid="add-knowledge-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
            <Plus size={15} strokeWidth={1.5} /> Add
          </button>
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.txt,.md,.csv,.png,.jpg,.jpeg" onChange={onFile} className="hidden" data-testid="knowledge-file-input" />
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-3">Everything worth keeping</h1>
      <p className="text-[#8A8F8C] mb-8 max-w-xl">Drop notes and PDFs straight from your iPad — Kukdi reads them so you can find them later.</p>

      <div className="flex items-center gap-2 mb-8" data-testid="knowledge-search-modes">
        <div className="flex bg-[#EFECE7] rounded-full p-1">
          <button
            onClick={() => { setMode("contains"); setSemanticResults(null); }}
            data-testid="knowledge-mode-contains"
            className={`text-xs tracking-[0.1em] uppercase px-4 py-1.5 rounded-full transition-colors ${mode === "contains" ? "bg-[#F7F6F2] text-[#2C2D2B]" : "text-[#8A8F8C]"}`}
          >Contains</button>
          <button
            onClick={() => setMode("meaning")}
            data-testid="knowledge-mode-meaning"
            className={`text-xs tracking-[0.1em] uppercase px-4 py-1.5 rounded-full transition-colors ${mode === "meaning" ? "bg-[#F7F6F2] text-[#2C2D2B]" : "text-[#8A8F8C]"}`}
          >By meaning</button>
        </div>
        <form onSubmit={runSemantic} className="flex-1 max-w-md">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={mode === "meaning" ? "Ask by meaning, then press Enter…" : "Search knowledge…"}
            data-testid="knowledge-search"
            className="w-full bg-[#EFECE7] rounded-full px-5 py-2 text-sm outline-none focus:ring-1 focus:ring-[#9DB0A3]"
          />
        </form>
      </div>

      {mode === "meaning" && (searching || semanticResults !== null) ? (
        <div className="space-y-6" data-testid="knowledge-semantic-results">
          {searching && <p className="font-editorial text-xl italic text-[#8A8F8C]">Kukdi is searching by meaning…</p>}
          {!searching && semanticResults?.length === 0 && <p className="text-[#8A8F8C]">Nothing here matches that yet.</p>}
          {!searching && semanticResults?.map((it) => (
            <div key={it.id} className="border-b border-[#E2DFD8] pb-6 group" data-testid={`knowledge-${it.id}`}>
              <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{KIND_LABEL[it.kind]}{it.file_url ? " · File" : ""}</span>
              <button onClick={() => setActive(it)} data-testid={`knowledge-open-${it.id}`} className="block font-editorial text-2xl text-[#2C2D2B] text-left hover:text-[#5C605A] transition-colors">{it.title}</button>
              {it.reason && <p className="text-sm text-[#9DB0A3] italic mt-1">Why · {it.reason}</p>}
              {it.summary && <p className="text-[#5C605A] mt-1">{it.summary}</p>}
            </div>
          ))}
        </div>
      ) : (
      <div className="space-y-6" data-testid="knowledge-list">
        {items.map((it) => (
          <div key={it.id} className="border-b border-[#E2DFD8] pb-6 group" data-testid={`knowledge-${it.id}`}>
            <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{KIND_LABEL[it.kind]}{it.file_url ? " · File" : ""}</span>
            <div className="flex items-baseline justify-between">
              <button onClick={() => setActive(it)} data-testid={`knowledge-open-${it.id}`} className="font-editorial text-2xl text-[#2C2D2B] text-left hover:text-[#5C605A] transition-colors">{it.title}</button>
              <button onClick={async () => { await api.deleteKnowledge(it.id); load(); }} data-testid={`knowledge-delete-${it.id}`} className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a]"><Trash2 size={14} /></button>
            </div>
            {it.summary && <p className="text-[#5C605A] mt-1">{it.summary}</p>}
          </div>
        ))}
      </div>
      )}

      <Modal open={!!active} onClose={() => setActive(null)} title={active?.title || ""} testId="knowledge-view-modal">
        {active && (
          <div>
            <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{KIND_LABEL[active.kind]}</span>
            {active.file_url && (
              <a href={`${BACKEND}${active.file_url}`} target="_blank" rel="noreferrer" data-testid="knowledge-file-link" className="block mt-3 text-sm text-[#5C605A] underline hover:text-[#2C2D2B]">
                Open {active.original_filename || "file"}
              </a>
            )}
            <p className="text-[#5C605A] mt-4 leading-relaxed whitespace-pre-wrap">{active.body || active.summary}</p>
          </div>
        )}
      </Modal>

      <Modal open={open} onClose={() => setOpen(false)} title="Add knowledge" testId="knowledge-modal">
        <Field label="Kind">
          <select className={inputClass} value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })} data-testid="knowledge-kind-input">
            {Object.entries(KIND_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
        <Field label="Title"><input className={inputClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="knowledge-title-input" /></Field>
        <Field label="Summary"><input className={inputClass} value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} data-testid="knowledge-summary-input" /></Field>
        <Field label="Body"><textarea className={inputClass} rows={4} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} data-testid="knowledge-body-input" /></Field>
        <PrimaryButton onClick={add} data-testid="knowledge-save-btn">Add</PrimaryButton>
      </Modal>
    </div>
  );
}
