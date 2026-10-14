import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Timer, PackageCheck } from "lucide-react";
import { useUser } from "../context/UserContext";
import { api } from "../lib/api";
import { loadRazorpayScript } from "../lib/razorpay";
import ProductImage from "../components/ProductImage";

function useCountdown(expiresAt) {
  const [remaining, setRemaining] = useState(expiresAt - Date.now());
  useEffect(() => {
    const t = setInterval(() => setRemaining(expiresAt - Date.now()), 1000);
    return () => clearInterval(t);
  }, [expiresAt]);
  return Math.max(0, remaining);
}

function formatDuration(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${seconds}s`;
  return `${seconds}s`;
}

function LockCard({ lock, onPay, paying }) {
  const remainingMs = useCountdown(lock.expiresAt);
  const expired = remainingMs <= 0 || lock.status === "expired";
  const purchased = lock.status === "purchased";
  const urgent = !expired && remainingMs < 60 * 60 * 1000; // under 1 hour left

  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex items-center gap-4 bg-white rounded-2xl p-4 shadow-sm">
      <ProductImage seed={String(lock.productId)} className="w-20 h-20 rounded-xl shrink-0" />
      <div className="flex-1">
        <p className="font-display text-lg text-ink">{lock.productName}</p>
        <p className="text-ink font-medium">₹{lock.price.toLocaleString("en-IN")}</p>
        {purchased ? (
          <p className="text-sage text-xs font-medium flex items-center gap-1 mt-1"><PackageCheck className="w-3.5 h-3.5" /> Order placed</p>
        ) : expired ? (
          <p className="text-ink-soft text-xs mt-1">Price lock expired</p>
        ) : (
          <p className={`text-xs font-medium flex items-center gap-1 mt-1 ${urgent ? "text-rani" : "text-sage"}`}>
            <Timer className="w-3.5 h-3.5" /> Expires in {formatDuration(remainingMs)}
          </p>
        )}
      </div>
      {!purchased && !expired && (
        <motion.button whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }} disabled={paying} onClick={() => onPay(lock.lockId)} className="bg-ink text-ivory text-sm px-5 py-2.5 rounded-full font-medium disabled:opacity-60">
          {paying ? "Processing..." : "Checkout"}
        </motion.button>
      )}
    </motion.div>
  );
}

export default function Deals() {
  const { isAuthenticated } = useUser();
  const navigate = useNavigate();
  const [locks, setLocks] = useState([]);
  const [confirmed, setConfirmed] = useState(null);
  const [payingId, setPayingId] = useState(null);
  const [error, setError] = useState(null);

  function refresh() {
    api.getLocks().then(setLocks).catch(() => {});
  }

  useEffect(() => {
    if (!isAuthenticated) { navigate("/login"); return; }
    refresh();
    const t = setInterval(refresh, 4000);
    return () => clearInterval(t);
  }, [isAuthenticated]);

  async function handleCheckout(lockId) {
    setError(null);
    setPayingId(lockId);
    try {
      const order = await api.createPaymentOrder(lockId);

      if (!order.live) {
        // Mock mode: no real payment keys configured — auto-confirm instantly.
        const res = await api.confirmCheckout({ lockId, orderId: order.orderId });
        setConfirmed(res);
        refresh();
        setPayingId(null);
        return;
      }

      // Live mode: open real Razorpay Checkout
      const loaded = await loadRazorpayScript();
      if (!loaded) throw new Error("Could not load payment gateway. Check your connection.");

      const rzp = new window.Razorpay({
        key: order.keyId,
        amount: order.amount * 100,
        currency: order.currency,
        order_id: order.orderId,
        name: "Bazaaro",
        description: "Negotiated price checkout",
        handler: async (response) => {
          const res = await api.confirmCheckout({
            lockId,
            orderId: response.razorpay_order_id,
            paymentId: response.razorpay_payment_id,
            signature: response.razorpay_signature,
          });
          setConfirmed(res);
          refresh();
        },
        modal: { ondismiss: () => setPayingId(null) },
      });
      rzp.open();
    } catch (e) {
      setError(e.message);
    } finally {
      setPayingId(null);
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="font-display text-3xl text-ink mb-2">My Deals</h1>
      <p className="text-ink-soft mb-8">Prices you've negotiated, locked and waiting for checkout.</p>

      {error && <p className="text-rani text-sm mb-4">{error}</p>}

      <AnimatePresence>
        {confirmed && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="bg-sage/10 border border-sage/30 rounded-2xl p-5 mb-6 overflow-hidden">
            <p className="text-sm text-ink font-medium">{confirmed.message}</p>
            <p className="text-xs text-ink-soft">Final price: ₹{confirmed.finalPrice.toLocaleString("en-IN")}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {locks.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-ink-soft mb-4">No active deals yet — go bargain for something you love.</p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <AnimatePresence>
            {locks.map((lock) => (
              <LockCard key={lock.lockId} lock={lock} onPay={handleCheckout} paying={payingId === lock.lockId} />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
