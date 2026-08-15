import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, RefreshCw } from "lucide-react";
import { api } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

const STAGES = ["researching", "networking", "applied", "interviewing", "offer", "closed"];
const CATEGORY_LABELS = {
  roadmap: "Learning roadmap",
  framework: "Frameworks",
  story: "Stories",
  case: "Case practice",
  resume: "Resume",
  networking: "Networking",
  daily: "Daily preparation",
};
const STATUS_NEXT = { todo: "doing", doing: "done", done: "todo" };
const STATUS_LABEL = { todo: "To do", doing: "In progress", done: "Done" };

export default function DreamOffer() {
  const [data, setData] = useState(null);
  const [companyModal, setCompanyModal] = useState(false);
  const [prepModal, setPrepModal] = useState(false);
  const [countdown, setCountdown] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [target, setTarget] = useState("");
  const [newCompany, setNewCompany] = useState({ name: "", tier: "target", role: "Product Manager", stage: "researching", next_action: "" });
  const [newPrep, setNewPrep] = useState({ category: "roadmap", title: "", content: "" });

  const load = () => api.dreamOverview().then(setData);
  const loadCountdown = () => api.countdown().then((d) => setCountdown(d.countdown));
  useEffect(() => { load(); loadCountdown(); }, []);

  const generateCountdown = async () => {
    setGenerating(true);
    try {
      const d = await api.generateCountdown(target ? { company_id: target } : {});
      setCountdown(d.countdown);
    } finally {
      setGenerating(false);
    }
  };

  const toggleTask = async (taskId, done) => {
    const d = await api.toggleCountdownTask(taskId, done);
    setCountdown(d.countdown);
  };

  const cycleStage = async (c) => {
    const idx = STAGES.indexOf(c.stage);
    const next = STAGES[(idx + 1) % STAGES.length];
    await api.updateCompany(c.id, { stage: next });
    load();
  };

  const cyclePrep = async (p) => {
    await api.updatePrep(p.id, { status: STATUS_NEXT[p.status] || "todo" });
    load();
  };

  const addCompany = async () => {
    if (!newCompany.name.trim()) return;
    await api.createCompany(newCompany);
    setCompanyModal(false);
    setNewCompany({ name: "", tier: "target", role: "Product Manager", stage: "researching", next_action: "" });
    load();
  };

  const addPrep = async () => {
    if (!newPrep.title.trim()) return;
    await api.createPrep({ ...newPrep, status: "todo" });
    setPrepModal(false);
    setNewPrep({ category: "roadmap", title: "", content: "" });
    load();
  };

  if (!data) return <div className="text-[#8A8F8C] text-sm">Loading…</div>;

  return (
    <div data-testid="dream-offer-page">
      <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">The flagship</span>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mt-2 mb-6">Dream Offer</h1>

      {/* Progress — quiet, editorial */}
      <div className="mb-16 max-w-md" data-testid="dream-progress">
        <div className="flex items-baseline justify-between mb-3">
          <span className="text-sm text-[#5C605A]">Preparation</span>
          <span className="font-editorial text-3xl text-[#2C2D2B]">{data.progress}%</span>
        </div>
        <div className="h-[3px] bg-[#E2DFD8] rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-[#9DB0A3]"
            initial={{ width: 0 }}
            animate={{ width: `${data.progress}%` }}
            transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
          />
        </div>
      </div>

      {/* Interview Countdown */}
      <section className="mb-20" data-testid="countdown-section">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Interview countdown</h2>
          {countdown && (
            <button onClick={generateCountdown} data-testid="countdown-regenerate" disabled={generating} className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors disabled:opacity-40">
              <RefreshCw size={14} strokeWidth={1.5} className={generating ? "animate-spin" : ""} /> Reshape plan
            </button>
          )}
        </div>

        {!countdown && !generating && (
          <div data-testid="countdown-empty">
            <p className="font-editorial text-2xl md:text-3xl text-[#2C2D2B] max-w-xl leading-snug mb-6">
              Turn your next round into a calm, day-by-day plan that adapts as you practise.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <select value={target} onChange={(e) => setTarget(e.target.value)} data-testid="countdown-target-select" className="bg-[#EFECE7] rounded-full px-5 py-2.5 text-sm outline-none focus:ring-1 focus:ring-[#9DB0A3]">
                <option value="">Next scheduled round</option>
                {data.companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
              <PrimaryButton onClick={generateCountdown} data-testid="countdown-generate">Build my countdown</PrimaryButton>
            </div>
          </div>
        )}

        {generating && !countdown && (
          <p className="font-editorial text-2xl italic text-[#8A8F8C]" data-testid="countdown-loading">Kukdi is shaping your plan…</p>
        )}

        {countdown && (
          <div data-testid="countdown-plan">
            <div className="flex items-baseline justify-between mb-6">
              <div className="flex items-baseline gap-3">
                <h3 className="font-editorial text-3xl text-[#2C2D2B]">{countdown.company}</h3>
                <span className="text-sm text-[#8A8F8C]">{countdown.role}</span>
              </div>
              <span className="font-editorial text-4xl text-[#9DB0A3]" data-testid="countdown-days">
                {countdown.days_remaining}<span className="text-sm text-[#8A8F8C] ml-1.5">days out</span>
              </span>
            </div>
            <div className="h-[3px] bg-[#E2DFD8] rounded-full overflow-hidden mb-10 max-w-md">
              <motion.div className="h-full bg-[#9DB0A3]" initial={{ width: 0 }} animate={{ width: `${countdown.progress}%` }} transition={{ duration: 1 }} />
            </div>
            <div className="space-y-8">
              {countdown.days.map((d, i) => (
                <div key={d.id} className="flex gap-6" data-testid={`countdown-day-${i}`}>
                  <div className="w-16 shrink-0 text-right">
                    <div className="font-editorial text-2xl text-[#2C2D2B]">{i + 1}</div>
                    <div className="text-[10px] tracking-[0.1em] uppercase text-[#8A8F8C]">{new Date(d.date).toLocaleDateString([], { weekday: "short" })}</div>
                  </div>
                  <div className="flex-1 border-b border-[#E2DFD8] pb-6">
                    <h4 className="text-lg text-[#2C2D2B] mb-3">{d.focus}</h4>
                    <div className="space-y-2.5">
                      {d.tasks.map((t) => (
                        <button
                          key={t.id}
                          onClick={() => toggleTask(t.id, !t.done)}
                          data-testid={`countdown-task-${t.id}`}
                          className="flex items-start gap-3 text-left group w-full"
                        >
                          <span className={`mt-1 h-3.5 w-3.5 rounded-full shrink-0 transition-colors ${t.done ? "bg-[#9DB0A3]" : "bg-[#E2DFD8] group-hover:bg-[#D4DDD7]"}`} />
                          <span className={`text-[15px] ${t.done ? "text-[#8A8F8C] line-through decoration-[#D4DDD7]" : "text-[#5C605A]"}`}>{t.text}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Companies */}
      <section className="mb-20">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Companies</h2>
          <button onClick={() => setCompanyModal(true)} data-testid="add-company-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
            <Plus size={15} strokeWidth={1.5} /> Add
          </button>
        </div>
        <div className="space-y-6">
          {data.companies.map((c) => (
            <div key={c.id} className="border-b border-[#E2DFD8] pb-6 group" data-testid={`company-${c.id}`}>
              <div className="flex items-baseline justify-between">
                <div className="flex items-baseline gap-3">
                  <h3 className="font-editorial text-3xl text-[#2C2D2B]">{c.name}</h3>
                  {c.tier === "dream" && <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">Dream</span>}
                </div>
                <button
                  onClick={() => cycleStage(c)}
                  data-testid={`company-stage-${c.id}`}
                  className="text-xs tracking-[0.15em] uppercase text-[#5C605A] hover:text-[#2C2D2B] transition-colors"
                >
                  {c.stage}
                </button>
              </div>
              <p className="text-sm text-[#8A8F8C] mt-1">{c.role}{c.location ? ` · ${c.location}` : ""}</p>
              {c.next_action && <p className="text-[#5C605A] mt-3">Next · {c.next_action}</p>}
              <button
                onClick={async () => { await api.deleteCompany(c.id); load(); }}
                data-testid={`company-delete-${c.id}`}
                className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a] mt-3 flex items-center gap-1 text-xs"
              >
                <Trash2 size={13} strokeWidth={1.5} /> Remove
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* Prep by category */}
      <section>
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Preparation</h2>
          <button onClick={() => setPrepModal(true)} data-testid="add-prep-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
            <Plus size={15} strokeWidth={1.5} /> Add
          </button>
        </div>
        <div className="space-y-12">
          {Object.entries(data.prep_by_category).map(([cat, items]) => (
            <div key={cat} data-testid={`prep-category-${cat}`}>
              <h3 className="font-editorial text-2xl text-[#2C2D2B] mb-4">{CATEGORY_LABELS[cat] || cat}</h3>
              <div className="space-y-2">
                {items.map((p) => (
                  <div key={p.id} className="flex items-start gap-4 py-1.5 group" data-testid={`prep-${p.id}`}>
                    <button
                      onClick={() => cyclePrep(p)}
                      data-testid={`prep-status-${p.id}`}
                      className={`mt-1.5 h-3.5 w-3.5 rounded-full shrink-0 transition-colors ${
                        p.status === "done" ? "bg-[#9DB0A3]" : p.status === "doing" ? "bg-[#D4DDD7]" : "bg-[#E2DFD8]"
                      }`}
                      title={STATUS_LABEL[p.status]}
                    />
                    <div className="flex-1">
                      <p className={`text-lg ${p.status === "done" ? "text-[#8A8F8C] line-through decoration-[#D4DDD7]" : "text-[#2C2D2B]"}`}>
                        {p.title}
                      </p>
                      {p.content && <p className="text-sm text-[#8A8F8C]">{p.content}</p>}
                    </div>
                    <button
                      onClick={async () => { await api.deletePrep(p.id); load(); }}
                      data-testid={`prep-delete-${p.id}`}
                      className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a] mt-1"
                    >
                      <Trash2 size={14} strokeWidth={1.5} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Modal open={companyModal} onClose={() => setCompanyModal(false)} title="Add a company" testId="company-modal">
        <Field label="Name">
          <input className={inputClass} value={newCompany.name} onChange={(e) => setNewCompany({ ...newCompany, name: e.target.value })} data-testid="company-name-input" />
        </Field>
        <Field label="Role">
          <input className={inputClass} value={newCompany.role} onChange={(e) => setNewCompany({ ...newCompany, role: e.target.value })} data-testid="company-role-input" />
        </Field>
        <Field label="Tier">
          <select className={inputClass} value={newCompany.tier} onChange={(e) => setNewCompany({ ...newCompany, tier: e.target.value })} data-testid="company-tier-input">
            <option value="dream">Dream</option>
            <option value="target">Target</option>
            <option value="safe">Safe</option>
          </select>
        </Field>
        <Field label="Next action">
          <input className={inputClass} value={newCompany.next_action} onChange={(e) => setNewCompany({ ...newCompany, next_action: e.target.value })} data-testid="company-next-input" />
        </Field>
        <PrimaryButton onClick={addCompany} data-testid="company-save-btn">Add company</PrimaryButton>
      </Modal>

      <Modal open={prepModal} onClose={() => setPrepModal(false)} title="Add preparation" testId="prep-modal">
        <Field label="Category">
          <select className={inputClass} value={newPrep.category} onChange={(e) => setNewPrep({ ...newPrep, category: e.target.value })} data-testid="prep-category-input">
            {Object.entries(CATEGORY_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
        <Field label="Title">
          <input className={inputClass} value={newPrep.title} onChange={(e) => setNewPrep({ ...newPrep, title: e.target.value })} data-testid="prep-title-input" />
        </Field>
        <Field label="Notes">
          <input className={inputClass} value={newPrep.content} onChange={(e) => setNewPrep({ ...newPrep, content: e.target.value })} data-testid="prep-content-input" />
        </Field>
        <PrimaryButton onClick={addPrep} data-testid="prep-save-btn">Add</PrimaryButton>
      </Modal>
    </div>
  );
}
