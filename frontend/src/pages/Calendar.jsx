import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, ArrowUpRight } from "lucide-react";
import { api, formatTime, formatDay } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

const TYPE_LABEL = { class: "Class", deadline: "Deadline", exam: "Exam", event: "Event", task: "Task", placement: "Placement" };

export default function Calendar() {
  const [data, setData] = useState(null);
  const [q, setQ] = useState("");
  const [answer, setAnswer] = useState("");
  const [asking, setAsking] = useState(false);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ type: "event", title: "", start: "", location: "" });

  const load = () => api.events().then(setData);
  useEffect(() => { load(); }, []);

  const ask = async (e) => {
    e.preventDefault();
    if (!q.trim()) return;
    setAsking(true);
    setAnswer("");
    try {
      const r = await api.askCalendar(q);
      setAnswer(r.answer);
    } finally {
      setAsking(false);
    }
  };

  const add = async () => {
    if (!form.title.trim() || !form.start) return;
    await api.createEvent({ ...form, start: new Date(form.start).toISOString() });
    setOpen(false);
    setForm({ type: "event", title: "", start: "", location: "" });
    load();
  };

  if (!data) return <div className="text-[#8A8F8C] text-sm">Loading…</div>;

  const grouped = {};
  data.upcoming.forEach((e) => {
    const key = formatDay(e.start);
    (grouped[key] ||= []).push(e);
  });

  return (
    <div data-testid="calendar-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Calendar</span>
        <button onClick={() => setOpen(true)} data-testid="add-event-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
          <Plus size={15} strokeWidth={1.5} /> Add
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-10">What's ahead</h1>

      {/* Ask Kukdi */}
      <form onSubmit={ask} className="mb-4" data-testid="calendar-ask-form">
        <div className="flex items-center gap-3 bg-[#EFECE7] rounded-[2rem] px-6 py-4 focus-within:ring-1 focus-within:ring-[#9DB0A3] transition-all max-w-2xl">
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="What class do I have next?" data-testid="calendar-ask-input" className="flex-1 bg-transparent outline-none text-[#2C2D2B] placeholder-[#8A8F8C]" />
          <button type="submit" data-testid="calendar-ask-submit" className="text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors"><ArrowUpRight size={20} strokeWidth={1.5} /></button>
        </div>
      </form>
      {(asking || answer) && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="font-editorial text-2xl text-[#2C2D2B] max-w-2xl mb-14 leading-snug" data-testid="calendar-answer">
          {asking ? "Kukdi is checking…" : answer}
        </motion.p>
      )}

      {/* Schedule */}
      <div className="space-y-10 mt-8" data-testid="calendar-list">
        {Object.entries(grouped).map(([day, events]) => (
          <div key={day}>
            <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-4">{day}</h2>
            <div className="space-y-1">
              {events.map((e) => (
                <div key={e.id} className="flex items-baseline gap-6 py-2.5 group" data-testid={`event-${e.id}`}>
                  <span className="text-sm text-[#8A8F8C] w-20 shrink-0">{formatTime(e.start)}</span>
                  <div className="flex-1">
                    <span className="text-lg text-[#2C2D2B]">{e.title}</span>
                    <span className="text-xs tracking-[0.12em] uppercase text-[#9DB0A3] ml-3">{TYPE_LABEL[e.type]}</span>
                    {e.location && <span className="text-sm text-[#8A8F8C] ml-2">· {e.location}</span>}
                  </div>
                  <button onClick={async () => { await api.deleteEvent(e.id); load(); }} data-testid={`event-delete-${e.id}`} className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#a9564a]"><Trash2 size={14} /></button>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <Modal open={open} onClose={() => setOpen(false)} title="Add to calendar" testId="event-modal">
        <Field label="Type">
          <select className={inputClass} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} data-testid="event-type-input">
            {Object.entries(TYPE_LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
        </Field>
        <Field label="Title"><input className={inputClass} value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid="event-title-input" /></Field>
        <Field label="When"><input type="datetime-local" className={inputClass} value={form.start} onChange={(e) => setForm({ ...form, start: e.target.value })} data-testid="event-start-input" /></Field>
        <Field label="Location"><input className={inputClass} value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} data-testid="event-location-input" /></Field>
        <PrimaryButton onClick={add} data-testid="event-save-btn">Add</PrimaryButton>
      </Modal>
    </div>
  );
}
