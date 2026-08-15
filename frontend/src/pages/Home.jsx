import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUpRight, ChevronDown, RefreshCw, Gift, Clock, Clock3, X } from "lucide-react";
import { api, formatTime } from "../lib/api";

const STATES = [
  "quiet", "normal", "busy", "placement", "interview", "exam", "weekend", "overwhelmed",
];

const fade = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.8, ease: [0.22, 1, 0.36, 1] },
};

export default function Home() {
  const [data, setData] = useState(null);
  const [text, setText] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [brief, setBrief] = useState(null);
  const [briefLoading, setBriefLoading] = useState(false);
  const [reminders, setReminders] = useState([]);
  const navigate = useNavigate();

  const load = () => api.home().then(setData).catch(() => {});
  useEffect(() => {
    load();
    api.brief().then((d) => setBrief(d.brief)).catch(() => {});
    api.reminders().then((d) => setReminders(d.reminders || [])).catch(() => {});
  }, []);

  const dismissReminder = async (id) => {
    setReminders((r) => r.filter((x) => x.id !== id));
    await api.dismissReminder(id);
  };

  const snoozeReminder = async (id) => {
    setReminders((r) => r.filter((x) => x.id !== id));
    await api.snoozeReminder(id);
  };

  const refreshBrief = async () => {
    setBriefLoading(true);
    try {
      const d = await api.refreshBrief();
      setBrief(d.brief);
    } finally {
      setBriefLoading(false);
    }
  };

  const setState = async (s) => {
    setMenuOpen(false);
    await api.setState(s);
    load();
  };

  const submit = (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    navigate("/talk", { state: { seed: text.trim() } });
  };

  if (!data) {
    return <div className="text-[#8A8F8C] text-sm" data-testid="home-loading">Kukdi is waking up…</div>;
  }

  return (
    <div data-testid="home-page">
      {/* State control */}
      <div className="flex items-center justify-between mb-10">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">
          {new Date(data.date).toLocaleDateString([], { weekday: "long", day: "numeric", month: "long" })}
        </span>
        <div className="relative">
          <button
            onClick={() => setMenuOpen((v) => !v)}
            data-testid="state-switcher"
            className="flex items-center gap-2 text-xs tracking-[0.15em] uppercase text-[#5C605A] hover:text-[#2C2D2B] transition-colors"
          >
            <span className="h-1.5 w-1.5 rounded-full bg-[#9DB0A3]" />
            {data.state}
            <ChevronDown size={13} strokeWidth={1.5} />
          </button>
          <AnimatePresence>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.25 }}
                className="absolute right-0 mt-3 w-44 bg-[#EFECE7] border border-[#E2DFD8] rounded-2xl p-2 z-40"
                data-testid="state-menu"
              >
                {STATES.map((s) => (
                  <button
                    key={s}
                    onClick={() => setState(s)}
                    data-testid={`state-option-${s}`}
                    className={`w-full text-left px-4 py-2 rounded-xl text-sm capitalize transition-colors hover:bg-[#E6E2DC] ${
                      data.state === s ? "text-[#2C2D2B]" : "text-[#8A8F8C]"
                    }`}
                  >
                    {s}
                  </button>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>

      {/* Greeting — the editorial heart */}
      <AnimatePresence mode="wait">
        <motion.div key={data.state} {...fade}>
          <p className="text-[#8A8F8C] text-lg mb-3">{data.greeting}</p>
          <h1 className="font-editorial text-5xl md:text-6xl lg:text-7xl leading-[0.95] text-[#2C2D2B] tracking-tight">
            {data.heading}
          </h1>
          <p className="mt-6 text-lg md:text-xl text-[#5C605A] max-w-xl leading-relaxed">
            {data.subtext}
          </p>
        </motion.div>
      </AnimatePresence>

      {/* Daily brief — Kukdi reading the day */}
      {(brief || briefLoading) && (
        <motion.section {...fade} className="mt-12 max-w-2xl group" data-testid="home-brief">
          <div className="flex items-center gap-3 mb-3">
            <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Today's brief</h2>
            <button
              onClick={refreshBrief}
              data-testid="brief-refresh"
              className="opacity-0 group-hover:opacity-100 transition-opacity text-[#8A8F8C] hover:text-[#2C2D2B]"
            >
              <RefreshCw size={13} strokeWidth={1.5} className={briefLoading ? "animate-spin" : ""} />
            </button>
          </div>
          <p className="font-editorial text-2xl md:text-[26px] italic text-[#5C605A] leading-snug" data-testid="brief-text">
            {briefLoading && !brief ? "Kukdi is reading your day…" : brief}
          </p>
        </motion.section>
      )}

      {/* Smart reminders — gentle, dismissable nudges */}
      {reminders.length > 0 && (
        <motion.section {...fade} className="mt-16" data-testid="home-reminders">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-5">A gentle nudge</h2>
          <div className="space-y-2">
            {reminders.slice(0, 4).map((r) => (
              <div
                key={r.id}
                className="flex items-center gap-4 bg-[#EFECE7] rounded-2xl px-5 py-3.5 group"
                data-testid={`reminder-${r.id}`}
              >
                {r.kind === "birthday" ? (
                  <Gift size={17} strokeWidth={1.5} className="text-[#9DB0A3] shrink-0" />
                ) : r.kind === "next-step" ? (
                  <ArrowUpRight size={17} strokeWidth={1.5} className="text-[#9DB0A3] shrink-0" />
                ) : (
                  <Clock size={17} strokeWidth={1.5} className="text-[#9DB0A3] shrink-0" />
                )}
                <span className="flex-1 text-[#2C2D2B]">{r.title}</span>
                <span className="text-sm text-[#8A8F8C] whitespace-nowrap">{r.detail}</span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => snoozeReminder(r.id)}
                    data-testid={`reminder-snooze-${r.id}`}
                    className="text-[#8A8F8C] hover:text-[#2C2D2B] p-1"
                    title="Snooze until tomorrow"
                  >
                    <Clock3 size={15} strokeWidth={1.5} />
                  </button>
                  <button
                    onClick={() => dismissReminder(r.id)}
                    data-testid={`reminder-dismiss-${r.id}`}
                    className="text-[#8A8F8C] hover:text-[#2C2D2B] p-1"
                    title="Dismiss"
                  >
                    <X size={15} strokeWidth={1.5} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Focus */}
      {data.focus?.length > 0 && (
        <motion.section {...fade} className="mt-16" data-testid="home-focus">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-5">What matters</h2>
          <div className="space-y-4">
            {data.focus.map((f, i) => (
              <div key={i} className="flex items-baseline justify-between border-b border-[#E2DFD8] pb-4">
                <span className="text-xl text-[#2C2D2B]">{f.title}</span>
                <span className="text-sm text-[#8A8F8C] whitespace-nowrap ml-6">{f.detail}</span>
              </div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Today */}
      {data.today?.length > 0 && (
        <motion.section {...fade} className="mt-16" data-testid="home-today">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-5">Today</h2>
          <div className="space-y-1">
            {data.today.map((e) => (
              <div key={e.id} className="flex items-baseline gap-6 py-2.5">
                <span className="text-sm text-[#8A8F8C] w-20 shrink-0">{formatTime(e.start)}</span>
                <span className="text-lg text-[#2C2D2B]">{e.title}</span>
                {e.location && <span className="text-sm text-[#8A8F8C]">· {e.location}</span>}
              </div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Surfaced memory */}
      {data.surfaced_memories?.length > 0 && (
        <motion.section {...fade} className="mt-16" data-testid="home-surfaced">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-5">On your mind</h2>
          <div className="space-y-6">
            {data.surfaced_memories.map((m) => (
              <blockquote key={m.id} className="font-editorial text-2xl md:text-3xl italic text-[#5C605A] border-l border-[#9DB0A3] pl-6 leading-snug">
                {m.description}
              </blockquote>
            ))}
          </div>
        </motion.section>
      )}

      {/* Pending nudge */}
      {data.pending_candidates > 0 && (
        <motion.button
          {...fade}
          onClick={() => navigate("/memory")}
          data-testid="home-pending-nudge"
          className="mt-16 flex items-center gap-2 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors"
        >
          Kukdi noticed {data.pending_candidates} thing{data.pending_candidates > 1 ? "s" : ""} worth remembering
          <ArrowUpRight size={15} strokeWidth={1.5} />
        </motion.button>
      )}

      {/* Conversation pill */}
      <motion.form
        {...fade}
        onSubmit={submit}
        className="mt-20 max-w-2xl"
        data-testid="home-conversation-form"
      >
        <div className="flex items-center gap-3 bg-[#EFECE7] rounded-[2rem] px-6 py-4 focus-within:ring-1 focus-within:ring-[#9DB0A3] transition-all">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tell Kukdi anything…"
            data-testid="home-conversation-input"
            className="flex-1 bg-transparent outline-none text-[#2C2D2B] placeholder-[#8A8F8C] text-lg"
          />
          <button type="submit" data-testid="home-conversation-submit" className="text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors">
            <ArrowUpRight size={22} strokeWidth={1.5} />
          </button>
        </div>
      </motion.form>
    </div>
  );
}
