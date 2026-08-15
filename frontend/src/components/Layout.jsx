import { NavLink, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { Home, Target, Users, MoreHorizontal, MessageCircle } from "lucide-react";

const NAV = [
  { to: "/", label: "Home", icon: Home, testId: "nav-home", end: true },
  { to: "/dream-offer", label: "Dream Offer", icon: Target, testId: "nav-dream" },
  { to: "/people", label: "People", icon: Users, testId: "nav-people" },
  { to: "/more", label: "More", icon: MoreHorizontal, testId: "nav-more" },
];

function RailLink({ to, label, end, testId }) {
  return (
    <NavLink to={to} end={end} data-testid={testId} className="group block">
      {({ isActive }) => (
        <div className="relative flex items-center py-2.5">
          <span
            className={`absolute -left-4 h-1.5 w-1.5 rounded-full bg-[#9DB0A3] transition-all duration-500 ${
              isActive ? "opacity-100 scale-100" : "opacity-0 scale-50"
            }`}
          />
          <span
            className={`text-[15px] tracking-tight transition-colors duration-300 ${
              isActive ? "text-[#2C2D2B]" : "text-[#8A8F8C] group-hover:text-[#5C605A]"
            }`}
          >
            {label}
          </span>
        </div>
      )}
    </NavLink>
  );
}

export default function Layout({ children }) {
  const location = useLocation();

  return (
    <div className="App min-h-screen bg-[#F7F6F2] text-[#2C2D2B]">
      {/* Desktop left rail */}
      <aside className="hidden md:flex fixed top-0 left-0 h-screen w-[260px] flex-col justify-between px-10 py-12 bg-[#F7F6F2]">
        <div>
          <div className="mb-16">
            <div className="font-editorial text-3xl leading-none text-[#2C2D2B]">Kukdi</div>
            <div className="text-xs tracking-[0.15em] uppercase text-[#8A8F8C] mt-2">
              A Personal OS
            </div>
          </div>
          <nav className="space-y-1 pl-4" data-testid="desktop-nav">
            {NAV.map((n) => (
              <RailLink key={n.to} {...n} />
            ))}
          </nav>
        </div>

        <div className="pl-4">
          <NavLink to="/talk" data-testid="nav-talk" className="group flex items-center gap-2.5">
            <MessageCircle size={16} strokeWidth={1.5} className="text-[#9DB0A3]" />
            <span className="text-sm text-[#8A8F8C] group-hover:text-[#2C2D2B] transition-colors">
              Talk to Kukdi
            </span>
          </NavLink>
          <div className="mt-6 text-xs text-[#8A8F8C] leading-relaxed">
            For Little Miss
            <br />
            ISB Mohali
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="md:ml-[260px] min-h-screen">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="px-6 py-10 md:px-16 lg:px-24 md:py-20 pb-32 md:pb-24 max-w-4xl"
        >
          {children}
        </motion.div>
      </main>

      {/* Mobile bottom nav */}
      <nav
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#EFECE7] border-t border-[#E2DFD8] flex justify-around items-center py-3 px-2"
        data-testid="mobile-nav"
      >
        {NAV.map((n) => {
          const Icon = n.icon;
          const active =
            n.end ? location.pathname === "/" : location.pathname.startsWith(n.to);
          return (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              data-testid={`${n.testId}-mobile`}
              className="flex flex-col items-center gap-1"
            >
              <Icon
                size={20}
                strokeWidth={1.5}
                className={active ? "text-[#2C2D2B]" : "text-[#8A8F8C]"}
              />
              <span
                className={`text-[10px] tracking-wide ${
                  active ? "text-[#2C2D2B]" : "text-[#8A8F8C]"
                }`}
              >
                {n.label}
              </span>
            </NavLink>
          );
        })}
      </nav>
    </div>
  );
}
