import { Sparkles, Mail, Phone, Share2, ShieldCheck, Truck, RotateCcw, CreditCard } from "lucide-react";

const COLUMNS = [
  {
    title: "About",
    links: ["About Bazaaro", "Careers", "Press", "Bazaaro Stories"],
  },
  {
    title: "Help",
    links: ["Payments", "Shipping", "Cancellation & Returns", "FAQ", "Report a Product"],
  },
  {
    title: "Policy",
    links: ["Return Policy", "Terms of Use", "Security", "Privacy", "Sitemap"],
  },
  {
    title: "Sell on Bazaaro",
    links: ["Seller Sign Up", "Seller Dashboard", "Fulfilment", "Advertise"],
  },
];

export default function Footer() {
  return (
    <footer className="bg-ink text-ivory/80 mt-20">
      <div className="max-w-6xl mx-auto px-6 pt-14 pb-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-10">
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-marigold flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-ink" />
              </div>
              <span className="font-display font-bold text-lg text-ivory">Bazaaro</span>
            </div>
            <p className="text-xs text-ivory/50 leading-relaxed">
              Fashion that hears you out — negotiate a fair price on every eligible piece.
            </p>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="text-sm font-semibold text-ivory mb-3">{col.title}</h4>
              <ul className="flex flex-col gap-2">
                {col.links.map((link) => (
                  <li key={link}>
                    <a href="#" className="text-xs text-ivory/60 hover:text-marigold transition-colors">{link}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 py-6 border-y border-ivory/10">
          <TrustBadge icon={ShieldCheck} label="Secure Payments" />
          <TrustBadge icon={Truck} label="Free Shipping ₹999+" />
          <TrustBadge icon={RotateCcw} label="7-Day Returns" />
          <TrustBadge icon={CreditCard} label="Cash on Delivery" />
        </div>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6">
          <p className="text-xs text-ivory/40">© {new Date().getFullYear()} Bazaaro Fashion Pvt. Ltd. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <a href="mailto:hello@bazaaro.com" aria-label="Email" className="text-ivory/50 hover:text-marigold transition-colors"><Mail className="w-4 h-4" /></a>
            <a href="tel:+911234567890" aria-label="Phone" className="text-ivory/50 hover:text-marigold transition-colors"><Phone className="w-4 h-4" /></a>
            <a href="#" aria-label="Share" className="text-ivory/50 hover:text-marigold transition-colors"><Share2 className="w-4 h-4" /></a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function TrustBadge({ icon: Icon, label }) {
  return (
    <div className="flex items-center gap-2 justify-center md:justify-start">
      <Icon className="w-4 h-4 text-marigold shrink-0" />
      <span className="text-xs text-ivory/70">{label}</span>
    </div>
  );
}
