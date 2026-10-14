import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { useUser } from "../context/UserContext";
import ProductImage from "../components/ProductImage";

export default function Wishlist() {
  const { isAuthenticated } = useUser();
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return; }
    api.getWishlist().then(setItems).catch(() => {}).finally(() => setLoading(false));
  }, [isAuthenticated]);

  async function remove(productId) {
    setItems((prev) => prev.filter((i) => i.productId !== productId));
    await api.removeFromWishlist(productId);
  }

  if (!isAuthenticated) {
    return (
      <div className="max-w-xl mx-auto px-6 py-24 text-center">
        <Heart className="w-10 h-10 text-ink-soft mx-auto mb-4" />
        <p className="text-ink-soft mb-4">Log in to see your wishlist.</p>
        <button onClick={() => navigate("/login")} className="bg-ink text-ivory px-6 py-3 rounded-full text-sm font-medium">Log In</button>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl font-bold text-ink mb-6">My Wishlist</h1>

      {loading ? (
        <p className="text-ink-soft">Loading...</p>
      ) : items.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-2xl">
          <Heart className="w-10 h-10 text-ink-soft/40 mx-auto mb-4" />
          <p className="text-ink-soft mb-4">Nothing saved yet.</p>
          <Link to="/" className="text-rani text-sm font-medium">Browse products →</Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <AnimatePresence>
            {items.map((item) => (
              <motion.div
                key={item.productId}
                layout
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                className="bg-white rounded-xl overflow-hidden relative group"
              >
                <button
                  onClick={() => remove(item.productId)}
                  className="absolute top-2 right-2 z-10 w-8 h-8 rounded-full bg-white/90 flex items-center justify-center"
                >
                  <Trash2 className="w-3.5 h-3.5 text-rani" />
                </button>
                <Link to={`/product/${item.productId}`}>
                  <ProductImage seed={String(item.productId)} className="w-full aspect-square" />
                  <div className="p-3">
                    <p className="text-sm font-medium text-ink truncate">{item.name}</p>
                    <p className="text-xs text-ink-soft mb-1">{item.category}</p>
                    <p className="font-semibold text-ink text-sm">₹{item.price.toLocaleString("en-IN")}</p>
                  </div>
                </Link>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
