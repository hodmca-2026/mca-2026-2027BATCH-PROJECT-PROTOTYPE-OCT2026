import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";

export default function Modal({ open, onClose, icon: Icon, iconColor = "text-rani", title, children, actions }) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-ink/40 backdrop-blur-sm z-50 flex items-center justify-center px-6"
          onClick={onClose}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.92, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 300, damping: 25 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-ivory rounded-3xl p-8 max-w-sm w-full shadow-xl relative"
          >
            <button onClick={onClose} className="absolute top-4 right-4 text-ink-soft hover:text-ink">
              <X className="w-5 h-5" />
            </button>

            {Icon && (
              <div className={`w-12 h-12 rounded-full bg-white flex items-center justify-center mb-4 shadow-sm`}>
                <Icon className={`w-6 h-6 ${iconColor}`} />
              </div>
            )}

            {title && <h3 className="font-display text-xl text-ink mb-2">{title}</h3>}
            <div className="text-sm text-ink-soft leading-relaxed mb-6">{children}</div>

            {actions && <div className="flex gap-3">{actions}</div>}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
