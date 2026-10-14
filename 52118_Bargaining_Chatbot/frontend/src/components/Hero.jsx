import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import { MessageCircle } from "lucide-react";

const STEPS = [
  { price: 2799, label: "Listed price", bubble: null },
  { price: 2799, label: "You ask", bubble: "2200 mein de do?" },
  { price: 2400, label: "Bazaaro bot", bubble: "₹2400 final, deal?" },
  { price: 2400, label: "Locked for you", bubble: "Done! Locked for 24 hours." },
];

export default function Hero() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setStep((s) => (s + 1) % STEPS.length), 2200);
    return () => clearInterval(t);
  }, []);

  const current = STEPS[step];
  const struck = step >= 2;

  return (
    <section className="max-w-6xl mx-auto px-6 pt-16 pb-24 grid md:grid-cols-2 gap-12 items-center">
      <div>
        <p className="text-rani font-semibold tracking-wide text-sm mb-4">Fashion that hears you out</p>
        <h1 className="font-display text-5xl md:text-6xl leading-[1.05] text-ink mb-6">
          The price is a starting point, not the end of it.
        </h1>
        <p className="text-ink-soft text-lg max-w-md mb-8 leading-relaxed">
          Every eligible piece on Bazaaro comes with a bargaining chat. Name your price,
          the seller's bot works within a fair range, and once you agree, it's locked
          for 24 hours — no rush, no auto-charge.
        </p>
        <motion.a
          href="#catalog"
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.98 }}
          className="inline-block bg-ink text-ivory px-8 py-4 rounded-full font-medium tracking-wide"
        >
          Start browsing
        </motion.a>
      </div>

      <div className="relative">
        <div className="bg-ink rounded-3xl p-10 text-ivory relative overflow-hidden">
          <motion.div
            className="absolute -top-10 -right-10 w-40 h-40 rounded-full bg-marigold/20"
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 18, ease: "linear" }}
          />
          <p className="text-ivory/50 text-sm mb-3 relative z-10">{current.label}</p>
          <div className="relative z-10 flex items-baseline gap-3 mb-6">
            <AnimatePresence mode="wait">
              <motion.span
                key={step === 1 ? "2799a" : String(current.price)}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={`font-display text-5xl ${struck && step < 3 ? "line-through decoration-rani decoration-2 text-ivory/40" : ""}`}
              >
                ₹{step === 1 ? "2,799" : current.price.toLocaleString("en-IN")}
              </motion.span>
            </AnimatePresence>
            {step >= 2 && (
              <motion.span
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                className="font-display text-3xl text-marigold"
              >
                {step === 2 ? "→ ₹2,400" : ""}
              </motion.span>
            )}
          </div>

          <div className="relative z-10 min-h-[52px]">
            <AnimatePresence mode="wait">
              {current.bubble && (
                <motion.div
                  key={current.bubble}
                  initial={{ opacity: 0, scale: 0.9, y: 8 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="inline-flex items-center gap-2 bg-ivory/10 rounded-2xl px-4 py-3"
                >
                  <MessageCircle className="w-4 h-4 text-marigold shrink-0" />
                  <span className="text-sm">{current.bubble}</span>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <div className="flex gap-1.5 mt-8 relative z-10">
            {STEPS.map((_, i) => (
              <span key={i} className={`h-1 rounded-full transition-all duration-300 ${i === step ? "w-8 bg-marigold" : "w-2 bg-ivory/20"}`} />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
