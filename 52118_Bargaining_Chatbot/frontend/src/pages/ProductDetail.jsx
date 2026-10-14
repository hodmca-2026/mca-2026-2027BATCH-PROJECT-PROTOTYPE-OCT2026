import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Tag, ShieldCheck, RotateCcw, Truck, Heart, Star, ShoppingCart, Check, MapPin } from "lucide-react";
import ProductImage from "../components/ProductImage";
import { api } from "../lib/api";
import { useUser } from "../context/UserContext";
import { useWishlist } from "../context/WishlistContext";

export default function ProductDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useUser();
  const { ids: wishlistIds, toggle: toggleWishlist } = useWishlist();

  const [product, setProduct] = useState(null);
  const [variantId, setVariantId] = useState(null);
  const [similar, setSimilar] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addedToCart, setAddedToCart] = useState(false);
  const [cartError, setCartError] = useState(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]);

  useEffect(() => {
    api.getProduct(id).then((p) => {
      setProduct(p);
      setVariantId(p.variants[0]?.id);
    });
    api.getSimilarProducts(id).then(setSimilar).catch(() => setSimilar([]));
    api.getReviews(id).then(setReviews).catch(() => setReviews([]));
    setAddedToCart(false);
  }, [id]);

  if (!product) return <div className="max-w-6xl mx-auto px-6 py-24 text-ink-soft">Loading...</div>;

  const variant = product.variants.find((v) => v.id === variantId);
  const available = variant ? variant.stock - variant.reserved : 0;
  const isWishlisted = wishlistIds?.has(product.id);
  // Illustrative MRP-style strike-through, like Meesho/Amazon listings — a plausible
  // "before discount" price derived from the listed price (not a stored DB value).
  const mrp = Math.round(product.listedPrice * 1.35 / 10) * 10;
  const discountPct = Math.round((1 - product.listedPrice / mrp) * 100);

  async function handleAddToCart() {
    if (!isAuthenticated) { navigate("/login"); return; }
    setAddingToCart(true);
    setCartError(null);
    try {
      await api.addToCart(variantId, 1);
      setAddedToCart(true);
    } catch (e) {
      setCartError(e.message);
    } finally {
      setAddingToCart(false);
    }
  }

  function handleWishlist() {
    if (!isAuthenticated) { navigate("/login"); return; }
    toggleWishlist(product.id);
  }

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <div className="grid md:grid-cols-2 gap-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-lg overflow-hidden aspect-[4/5] relative bg-white border border-ink/5"
        >
          <ProductImage seed={product.id} className="w-full h-full" />
          <motion.button
            whileTap={{ scale: 0.85 }}
            onClick={handleWishlist}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center"
          >
            <Heart className={`w-5 h-5 transition-colors ${isWishlisted ? "fill-rani text-rani" : "text-ink"}`} />
          </motion.button>
        </motion.div>

        <div>
          <p className="text-xs uppercase tracking-wide text-ink-soft/70 mb-1">{product.category} · {product.fabric}</p>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-ink mb-2">{product.name}</h1>

          {product.avgRating != null && (
            <div className="flex items-center gap-2 mb-3">
              <span className="flex items-center gap-1 bg-sage text-white text-xs font-semibold px-2 py-0.5 rounded">
                {product.avgRating} <Star className="w-3 h-3 fill-white" />
              </span>
              <span className="text-xs text-ink-soft">{product.reviewCount} ratings</span>
            </div>
          )}

          <div className="flex items-baseline gap-2 mb-1">
            <p className="font-display text-3xl font-bold text-ink">₹{product.listedPrice.toLocaleString("en-IN")}</p>
            <p className="text-sm text-ink-soft/60 line-through">₹{mrp.toLocaleString("en-IN")}</p>
            <p className="text-sm text-sage font-semibold">{discountPct}% off</p>
          </div>
          <p className="text-xs text-ink-soft mb-6">Inclusive of all taxes</p>

          <p className="text-ink-soft leading-relaxed mb-6 text-sm">{product.description}</p>

          <div className="mb-6">
            <p className="text-sm font-semibold text-ink mb-2">Select Size / Variant</p>
            <div className="flex flex-wrap gap-2">
              {product.variants.map((v) => (
                <motion.button
                  key={v.id}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => { setVariantId(v.id); setAddedToCart(false); }}
                  disabled={v.stock - v.reserved <= 0}
                  className={`px-4 py-2 rounded-md text-sm border transition-colors ${
                    variantId === v.id ? "bg-ink text-ivory border-ink" : "border-ink/15 text-ink-soft hover:border-ink/40"
                  } ${v.stock - v.reserved <= 0 ? "opacity-30 cursor-not-allowed" : ""}`}
                >
                  {v.size} · {v.color}
                </motion.button>
              ))}
            </div>
            {available > 0 && available <= 3 && (
              <p className="text-rani text-xs mt-2 font-medium">Only {available} left in this size — order soon</p>
            )}
          </div>

          <div className="flex items-center gap-2 mb-6 text-xs text-ink-soft">
            <MapPin className="w-4 h-4" />
            Delivery available across India · usually 4-6 days
          </div>

          {cartError && <p className="text-rani text-sm mb-3">{cartError}</p>}

          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              onClick={handleAddToCart}
              disabled={addingToCart || available <= 0}
              className="flex-1 bg-ink text-ivory py-3.5 rounded-full font-medium flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {addedToCart ? (
                <><Check className="w-4 h-4" /> Added to Cart</>
              ) : (
                <><ShoppingCart className="w-4 h-4" /> {addingToCart ? "Adding..." : "Add to Cart"}</>
              )}
            </motion.button>

            {product.bargainingEnabled ? (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => navigate(`/bargain/${product.id}/${variantId}`)}
                className="flex-1 bg-rani text-white py-3.5 rounded-full font-medium flex items-center justify-center gap-2"
              >
                <Tag className="w-4 h-4" />
                Bargain for this
              </motion.button>
            ) : (
              <div className="flex-1 border border-ink/10 text-ink-soft/60 py-3.5 rounded-full font-medium text-center text-sm flex items-center justify-center">
                Bargaining unavailable — high demand item
              </div>
            )}
          </div>

          <div className="grid grid-cols-3 gap-4 pt-6 border-t border-ink/10 mb-2">
            <Feature icon={ShieldCheck} label="Fair price lock" />
            <Feature icon={RotateCcw} label="7-day returns" />
            <Feature icon={Truck} label="Free shipping ₹999+" />
          </div>
        </div>
      </div>

      {/* Product specifications — Meesho/Amazon-style detail table */}
      <div className="mt-12 pt-10 border-t border-ink/10">
        <h2 className="font-display text-xl font-bold text-ink mb-4">Product Details</h2>
        <div className="bg-white rounded-lg border border-ink/5 overflow-hidden max-w-2xl">
          {[
            ["Fabric", product.fabric],
            ["Category", product.category],
            ["Gender", product.gender === "men" ? "Men" : "Women"],
            ["Care Instructions", "Machine wash cold, do not bleach"],
            ["Country of Origin", "India"],
          ].map(([label, value], i) => (
            <div key={label} className={`flex px-4 py-3 text-sm ${i % 2 === 0 ? "bg-ivory-dim" : "bg-white"}`}>
              <span className="w-40 text-ink-soft shrink-0">{label}</span>
              <span className="text-ink font-medium">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Reviews */}
      <div className="mt-12 pt-10 border-t border-ink/10">
        <h2 className="font-display text-xl font-bold text-ink mb-6">Ratings & Reviews</h2>
        {reviews.length === 0 ? (
          <p className="text-ink-soft text-sm">No reviews yet for this product.</p>
        ) : (
          <div className="flex flex-col gap-4 max-w-2xl">
            {reviews.map((r, i) => (
              <div key={i} className="bg-white rounded-lg border border-ink/5 p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="flex items-center gap-1 bg-sage text-white text-xs font-semibold px-2 py-0.5 rounded">
                    {r.rating} <Star className="w-3 h-3 fill-white" />
                  </span>
                  <span className="text-sm font-medium text-ink">{r.reviewer_name}</span>
                  {r.verified_purchase && (
                    <span className="text-xs text-sage flex items-center gap-0.5"><Check className="w-3 h-3" /> Verified Purchase</span>
                  )}
                </div>
                <p className="text-sm text-ink-soft">{r.comment}</p>
              </div>
            ))}
          </div>
        )}
      </div>

      {similar.length > 0 && (
        <div className="mt-12 pt-10 border-t border-ink/10">
          <h2 className="font-display text-xl font-bold text-ink mb-6">You may also like</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {similar.map((p) => (
              <motion.button
                key={p.id}
                whileHover={{ y: -4 }}
                onClick={() => navigate(`/product/${p.id}`)}
                className="text-left"
              >
                <div className="rounded-lg overflow-hidden aspect-[4/5] mb-2 bg-white border border-ink/5">
                  <ProductImage seed={String(p.id)} className="w-full h-full" />
                </div>
                <p className="text-sm font-medium text-ink truncate">{p.name}</p>
                <p className="text-xs text-ink-soft">₹{p.listedPrice?.toLocaleString("en-IN")}</p>
              </motion.button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Feature({ icon: Icon, label }) {
  return (
    <div className="flex flex-col items-center text-center gap-2">
      <Icon className="w-5 h-5 text-sage" strokeWidth={1.5} />
      <p className="text-xs text-ink-soft">{label}</p>
    </div>
  );
}
