// Original SVG artwork (no third-party image): a stylised MRI slice with a Grad-CAM style heat blob.
const BRAIN =
  "M200 70 C140 60 80 100 75 165 C60 190 62 230 85 250 C80 290 120 325 165 320 C180 335 220 335 235 320 C280 325 320 290 315 250 C338 230 340 190 325 165 C320 100 260 60 200 70 Z";

export default function BrainIllustration({ className = "" }) {
  return (
    <svg className={className} viewBox="0 0 400 400" role="img" aria-label="Stylised brain MRI with Grad-CAM heatmap">
      <defs>
        <radialGradient id="ill-bg" cx="50%" cy="45%" r="65%">
          <stop offset="0" stopColor="#1e3a8a" />
          <stop offset="1" stopColor="#0b1437" />
        </radialGradient>
        <radialGradient id="ill-heat" cx="50%" cy="50%" r="50%">
          <stop offset="0" stopColor="#ef4444" stopOpacity=".95" />
          <stop offset=".5" stopColor="#f59e0b" stopOpacity=".55" />
          <stop offset="1" stopColor="#facc15" stopOpacity="0" />
        </radialGradient>
        <clipPath id="ill-clip"><path d={BRAIN} /></clipPath>
      </defs>
      <rect width="400" height="400" rx="28" fill="url(#ill-bg)" />
      <g stroke="#3b82f6" strokeOpacity=".18">
        {[60, 120, 180, 240, 300, 360].map((v) => (
          <g key={v}><line x1={v} y1="20" x2={v} y2="380" /><line x1="20" y1={v} x2="380" y2={v} /></g>
        ))}
      </g>
      <path d={BRAIN} fill="#60a5fa" fillOpacity=".16" stroke="#93c5fd" strokeWidth="3" />
      <g fill="none" stroke="#bfdbfe" strokeOpacity=".75" strokeWidth="2.5" strokeLinecap="round">
        <path d="M200 78 C192 130 210 190 198 250 C194 285 204 305 200 322" />
        <path d="M110 150 C130 125 160 135 160 160 C160 185 130 190 118 175" />
        <path d="M95 215 C120 200 150 215 148 240 C146 262 118 268 105 252" />
        <path d="M140 285 C160 265 185 280 180 305" />
        <path d="M135 105 C155 95 175 105 172 125" />
        <path d="M290 150 C270 125 240 135 240 160 C240 185 270 190 282 175" />
        <path d="M305 215 C280 200 250 215 252 240 C254 262 282 268 295 252" />
        <path d="M260 285 C240 265 215 280 220 305" />
        <path d="M265 105 C245 95 225 105 228 125" />
      </g>
      <g clipPath="url(#ill-clip)"><circle cx="250" cy="168" r="56" fill="url(#ill-heat)" /></g>
      <g stroke="#93c5fd" strokeWidth="3" fill="none" strokeLinecap="round">
        <path d="M34 62 V34 H62" /><path d="M338 34 H366 V62" /><path d="M34 338 V366 H62" /><path d="M338 366 H366 V338" />
      </g>
      <text x="200" y="372" textAnchor="middle" fill="#93c5fd" fontSize="13" fontFamily="monospace" letterSpacing="3">MRI · GRAD-CAM</text>
    </svg>
  );
}
