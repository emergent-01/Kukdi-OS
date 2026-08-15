import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowUpRight, Check, X } from "lucide-react";
import { api } from "../lib/api";

export default function Talk() {
  const [messages, setMessages] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [convId, setConvId] = useState(null);
  const [text, setText] = useState("");
  const [thinking, setThinking] = useState(false);
  const location = useLocation();
  const seededRef = useRef(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    api.messages().then((d) => {
      setMessages(d.messages || []);
      setConvId(d.conversation_id);
      const seed = location.state?.seed;
      if (seed && !seededRef.current) {
        seededRef.current = true;
        send(seed, d.conversation_id);
      }
    });
    api.pendingCandidates().then((d) => setCandidates(d.candidates || []));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const send = async (value, cid) => {
    const body = value.trim();
    if (!body) return;
    setText("");
    setMessages((m) => [...m, { id: `tmp-${Date.now()}`, role: "user", text: body }]);
    setThinking(true);
    try {
      const res = await api.sendMessage(body, cid ?? convId);
      setConvId(res.conversation_id);
      setMessages((m) => [...m, res.reply]);
      if (res.candidates?.length) setCandidates((c) => [...res.candidates, ...c]);
    } finally {
      setThinking(false);
    }
  };

  const decide = async (cand, keep) => {
    setCandidates((c) => c.filter((x) => x.id !== cand.id));
    if (keep) await api.confirmCandidate(cand.id);
    else await api.dismissCandidate(cand.id);
  };

  return (
    <div data-testid="talk-page" className="min-h-[70vh] flex flex-col">
      <h1 className="font-editorial text-4xl md:text-5xl text-[#2C2D2B] mb-2">Talk to Kukdi</h1>
      <p className="text-[#8A8F8C] mb-10">Say it the way you'd think it. Kukdi listens for what's worth keeping.</p>

      {/* Candidate confirmations */}
      <AnimatePresence>
        {candidates.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-10 space-y-3"
            data-testid="candidate-list"
          >
            <p className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Worth remembering?</p>
            {candidates.map((c) => (
              <div
                key={c.id}
                className="bg-[#EFECE7] rounded-2xl px-5 py-4 flex items-start justify-between gap-4"
                data-testid={`candidate-${c.id}`}
              >
                <div>
                  <span className="text-[10px] tracking-[0.15em] uppercase text-[#9DB0A3]">{c.type}</span>
                  <p className="text-[#2C2D2B] mt-1">{c.title}</p>
                  <p className="text-sm text-[#8A8F8C]">{c.description}</p>
                </div>
                <div className="flex gap-2 shrink-0">
                  <button
                    onClick={() => decide(c, true)}
                    data-testid={`candidate-keep-${c.id}`}
                    className="h-9 w-9 rounded-full bg-[#D4DDD7] text-[#2C2D2B] flex items-center justify-center hover:bg-[#9DB0A3] transition-colors"
                  >
                    <Check size={16} strokeWidth={2} />
                  </button>
                  <button
                    onClick={() => decide(c, false)}
                    data-testid={`candidate-dismiss-${c.id}`}
                    className="h-9 w-9 rounded-full bg-[#E6E2DC] text-[#8A8F8C] flex items-center justify-center hover:bg-[#E2DFD8] transition-colors"
                  >
                    <X size={16} strokeWidth={2} />
                  </button>
                </div>
              </div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Thread */}
      <div className="flex-1 space-y-6" data-testid="talk-thread">
        {messages.map((m) => (
          <motion.div
            key={m.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className={m.role === "user" ? "text-right" : ""}
          >
            {m.role === "kukdi" ? (
              <p className="font-editorial text-2xl md:text-[28px] leading-snug text-[#2C2D2B] max-w-2xl">
                {m.text}
              </p>
            ) : (
              <span className="inline-block bg-[#EFECE7] rounded-[1.6rem] px-5 py-3 text-[#2C2D2B] max-w-xl text-left">
                {m.text}
              </span>
            )}
          </motion.div>
        ))}
        {thinking && (
          <p className="text-[#8A8F8C] italic font-editorial text-xl" data-testid="talk-thinking">
            Kukdi is thinking…
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={(e) => { e.preventDefault(); send(text); }}
        className="sticky bottom-6 mt-10"
        data-testid="talk-form"
      >
        <div className="flex items-center gap-3 bg-[#EFECE7] rounded-[2rem] px-6 py-4 focus-within:ring-1 focus-within:ring-[#9DB0A3] transition-all">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Type naturally…"
            data-testid="talk-input"
            className="flex-1 bg-transparent outline-none text-[#2C2D2B] placeholder-[#8A8F8C] text-lg"
          />
          <button type="submit" data-testid="talk-submit" disabled={thinking} className="text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors disabled:opacity-40">
            <ArrowUpRight size={22} strokeWidth={1.5} />
          </button>
        </div>
      </form>
    </div>
  );
}
