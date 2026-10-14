import { Shirt, Sparkles } from "lucide-react";

// Deterministic gradient per product so the same item always looks the same,
// without depending on external image assets.
const GRADIENTS = [
  ["#E9A23B", "#B8305C"],
  ["#3F6B5E", "#1B1A2E"],
  ["#B8305C", "#1B1A2E"],
  ["#C97F1F", "#3F6B5E"],
  ["#8F2148", "#E9A23B"],
];

function hashToIndex(str, mod) {
  const s = String(str);
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) % 9973;
  return h % mod;
}

export default function ProductImage({ seed = "x", className = "" }) {
  const [c1, c2] = GRADIENTS[hashToIndex(seed, GRADIENTS.length)];
  return (
    <div
      className={`relative overflow-hidden flex items-center justify-center ${className}`}
      style={{ background: `linear-gradient(135deg, ${c1}, ${c2})` }}
    >
      <Shirt className="w-16 h-16 text-white/25" strokeWidth={1} />
      <Sparkles className="w-5 h-5 text-white/40 absolute top-4 right-4" strokeWidth={1.5} />
    </div>
  );
}
