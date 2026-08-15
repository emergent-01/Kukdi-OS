import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

const SECTIONS = [
  { to: "/memory", title: "Memory", desc: "Everything Kukdi remembers about you — fully editable.", testId: "more-memory" },
  { to: "/calendar", title: "Calendar", desc: "Timetable, deadlines, exams and placements. Ask it anything.", testId: "more-calendar" },
  { to: "/knowledge", title: "Knowledge", desc: "Documents, books, notes and the frameworks you're learning.", testId: "more-knowledge" },
  { to: "/talk", title: "Talk to Kukdi", desc: "The primary way in. Say it the way you'd think it.", testId: "more-talk" },
];

export default function More() {
  return (
    <div data-testid="more-page">
      <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">More</span>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mt-2 mb-14">The rest of Kukdi</h1>

      <div className="space-y-10">
        {SECTIONS.map((s) => (
          <Link key={s.to} to={s.to} data-testid={s.testId} className="group block border-b border-[#E2DFD8] pb-10">
            <div className="flex items-baseline justify-between">
              <h2 className="font-editorial text-4xl text-[#2C2D2B] group-hover:text-[#5C605A] transition-colors">{s.title}</h2>
              <ArrowUpRight size={22} strokeWidth={1.5} className="text-[#8A8F8C] group-hover:text-[#2C2D2B] transition-colors" />
            </div>
            <p className="text-[#5C605A] mt-2 max-w-lg">{s.desc}</p>
          </Link>
        ))}
      </div>

      <p className="font-editorial text-xl italic text-[#8A8F8C] mt-20">Kukdi · A Personal Operating System, for Little Miss.</p>
    </div>
  );
}
