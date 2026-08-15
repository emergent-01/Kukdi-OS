import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

export function Modal({ open, onClose, title, children, testId = "modal" }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-[100] flex items-end md:items-center justify-center p-0 md:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          data-testid={`${testId}-overlay`}
        >
          <div className="absolute inset-0 bg-[#2C2D2B]/20" onClick={onClose} />
          <motion.div
            className="relative w-full md:max-w-lg bg-[#F7F6F2] rounded-t-3xl md:rounded-3xl border border-[#E2DFD8] p-8 md:p-10 max-h-[88vh] overflow-y-auto"
            initial={{ y: 40, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            exit={{ y: 30, opacity: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            data-testid={testId}
          >
            <div className="flex items-start justify-between mb-6">
              <h3 className="font-editorial text-3xl text-[#2C2D2B] leading-none">{title}</h3>
              <button
                onClick={onClose}
                className="text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors"
                data-testid={`${testId}-close`}
              >
                <X size={20} strokeWidth={1.5} />
              </button>
            </div>
            {children}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export function Field({ label, children }) {
  return (
    <label className="block mb-5">
      <span className="block text-xs tracking-[0.15em] uppercase text-[#8A8F8C] mb-2">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "w-full bg-[#EFECE7] rounded-2xl px-5 py-3 text-[#2C2D2B] placeholder-[#8A8F8C] outline-none focus:ring-1 focus:ring-[#9DB0A3] transition-all";

export function PrimaryButton({ children, className = "", ...props }) {
  return (
    <button
      className={`bg-[#2C2D2B] text-[#F7F6F2] rounded-full px-7 py-3 text-sm tracking-wide hover:bg-[#3d3f3c] transition-colors disabled:opacity-40 ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}
