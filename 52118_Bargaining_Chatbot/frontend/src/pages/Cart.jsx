import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { Minus, Plus, Trash2, ShoppingBag } from "lucide-react";
import { api } from "../lib/api";
import { loadRazorpayScript } from "../lib/razorpay";
import { useUser } from "../context/UserContext";
import ProductImage from "../components/ProductImage";

export default function Cart() {
  const { isAuthenticated } = useUser();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirmed, setConfirmed] = useState(null);
  const [payingId, setPayingId] = useState(null);

  function refresh() {
    api.getCartItems().then(setItems).catch(() => {}).finally(() => setLoading(false));
  }

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    refresh();
  }, [isAuthenticated]);

  async function updateQty(item, delta) {
    const newQty = item.quantity + delta;
    if (newQty < 1) return;
    setItems((prev) => prev.map((i) => (i.cartItemId === item.cartItemId ? { ...i, quantity: newQty } : i)));
    await api.updateCartItem(item.cartItemId, newQty);
  }

  async function remove(cartItemId) {
    setItems((prev) => prev.filter((i) => i.cartItemId !== cartItemId));
    await api.removeCartItem(cartItemId);
  }

  async function checkout(item) {
    setPayingId(item.cartItemId);
    try {
      const order = await api.createCartItemOrder(item.cartItemId);
      if (order.live) {
        const loaded = await loadRazorpayScript();
        if (!loaded) throw new Error("Could not load payment gateway. Check your connection.");
        const rzp = new window.Razorpay({
          key: order.keyId,
          amount: order.amount * 100,
          currency: order.currency,
          order_id: order.orderId,
          name: "Bazaaro",
          description: item.name,
          handler: async (response) => {
            const res = await api.confirmCartItemOrder(item.cartItemId, {
              orderId: order.orderId,
              paymentId: response.razorpay_payment_id,
              signature: response.razorpay_signature,
            });
            setConfirmed(res);
            refresh();
          },
        });
        rzp.open();
      } else {
        // mock mode — confirm immediately
        const res = await api.confirmCartItemOrder(item.cartItemId, { orderId: order.orderId });
        setConfirmed(res);
        refresh();
      }
    } catch (e) {
      alert(e.message);
    } finally {
      setPayingId(null);
    }
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        <ShoppingBag className="w-10 h-10 text-ink-soft mx-auto mb-4" />
        <p className="text-ink-soft mb-4">Log in to see your cart.</p>
        <button onClick={() => navigate("/login")} className="bg-ink text-ivory px-6 py-3 rounded-full text-sm font-medium">Log In</button>
      </div>
    );
  }

  const total = items.reduce((sum, i) => sum + i.price * i.quantity, 0);

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl font-bold text-ink mb-6">My Cart</h1>

      <AnimatePresence>
        {confirmed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-sage/10 border border-sage/30 rounded-xl p-4 mb-6 overflow-hidden"
          >
            <p className="text-sm text-ink font-medium">{confirmed.message}</p>
            <p className="text-xs text-ink-soft">Final price: ₹{confirmed.finalPrice?.toLocaleString("en-IN")}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {loading ? (
        <p className="text-ink-soft">Loading...</p>
      ) : items.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl">
          <ShoppingBag className="w-10 h-10 text-ink-soft/40 mx-auto mb-4" />
          <p className="text-ink-soft mb-4">Your cart is empty.</p>
          <Link to="/" className="text-rani text-sm font-medium">Continue shopping →</Link>
        </div>
      ) : (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 flex flex-col gap-3">
            <AnimatePresence>
              {items.map((item) => (
                <motion.div
                  key={item.cartItemId}
                  layout
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="bg-white rounded-xl p-4 flex gap-4"
                >
                  <ProductImage seed={String(item.productId)} className="w-20 h-20 rounded-lg shrink-0" />
                  <div className="flex-1">
                    <p className="font-medium text-ink text-sm">{item.name}</p>
                    <p className="text-xs text-ink-soft mb-2">{item.size} · {item.color}</p>
                    <p className="font-semibold text-ink">₹{item.price.toLocaleString("en-IN")}</p>
                    {!item.inStock && <p className="text-xs text-rani mt-1">Out of stock</p>}
                  </div>
                  <div className="flex flex-col items-end justify-between">
                    <button onClick={() => remove(item.cartItemId)} className="text-ink-soft/50 hover:text-rani">
                      <Trash2 className="w-4 h-4" />
                    </button>
                    <div className="flex items-center gap-2 bg-ivory-dim rounded-full px-2 py-1">
                      <button onClick={() => updateQty(item, -1)} className="w-6 h-6 flex items-center justify-center"><Minus className="w-3 h-3" /></button>
                      <span className="text-sm w-4 text-center">{item.quantity}</span>
                      <button onClick={() => updateQty(item, 1)} className="w-6 h-6 flex items-center justify-center"><Plus className="w-3 h-3" /></button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <div className="bg-white rounded-xl p-5 h-fit sticky top-24">
            <h3 className="font-semibold text-ink mb-4">Order Summary</h3>
            <div className="flex justify-between text-sm text-ink-soft mb-2">
              <span>Subtotal ({items.length} items)</span>
              <span>₹{total.toLocaleString("en-IN")}</span>
            </div>
            <div className="flex justify-between text-sm text-sage mb-4">
              <span>Shipping</span>
              <span>{total >= 999 ? "Free" : "₹49"}</span>
            </div>
            <div className="flex justify-between font-semibold text-ink border-t border-ink/10 pt-3 mb-4">
              <span>Total</span>
              <span>₹{(total >= 999 ? total : total + 49).toLocaleString("en-IN")}</span>
            </div>
            {items.filter((i) => i.inStock).map((item) => (
              <motion.button
                key={item.cartItemId}
                whileTap={{ scale: 0.97 }}
                onClick={() => checkout(item)}
                disabled={payingId === item.cartItemId}
                className="w-full bg-marigold text-ink text-sm font-semibold py-2.5 rounded-full mb-2 disabled:opacity-50"
              >
                {payingId === item.cartItemId ? "Processing..." : `Buy "${item.name}"`}
              </motion.button>
            ))}
            <p className="text-[11px] text-ink-soft/60 text-center mt-2">Each item checks out individually (no single combined cart payment yet).</p>
          </div>
        </div>
      )}
    </div>
  );
}
