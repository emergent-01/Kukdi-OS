import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { RefreshCw } from "lucide-react";
import { api } from "../lib/api";

export default function Reflection() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => { api.weeklyReflection().then(setData); }, []);

  const refresh = async () => {
    setLoading(true);
    try { setData(await api.weeklyReflection(true)); }
    finally { setLoading(false); }
  };

  const stats = data?.stats || {};

  return (
    <div data-testid="reflection-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Sunday reflection</span>
        <button onClick={refresh} data-testid="reflection-refresh" className="flex items-center gap-1.5 text-sm text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors">
          <RefreshCw size={14} strokeWidth={1.5} className={loading ? "animate-spin" : ""} /> Refresh
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-12">Your week, gently</h1>

      <motion.p
        key={data?.reflection || "loading"}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="font-editorial text-3xl md:text-[34px] leading-snug text-[#2C2D2B] max-w-3xl"
        data-testid="reflection-text"
      >
        {data ? data.reflection : "Kukdi is looking back over your week…"}
      </motion.p>

      {(stats.attended_this_week?.length > 0 || stats.coming_up?.length > 0) && (
        <div className="mt-20 grid md:grid-cols-2 gap-16 max-w-3xl" data-testid="reflection-stats">
          <div>
            <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-4">Behind you</h2>
            <div className="space-y-2">
              {(stats.attended_this_week || []).map((t, i) => (
                <p key={i} className="text-[#5C605A]">{t}</p>
              ))}
              <p className="text-[#8A8F8C] text-sm mt-3">{stats.prep_done} prep milestones done</p>
            </div>
          </div>
          <div>
            <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-4">Just ahead</h2>
            <div className="space-y-2">
              {(stats.coming_up || []).map((t, i) => (
                <p key={i} className="text-[#5C605A]">{t}</p>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
