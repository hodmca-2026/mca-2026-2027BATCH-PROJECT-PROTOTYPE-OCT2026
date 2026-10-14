import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Tag, Heart, Star } from "lucide-react";
import ProductImage from "./ProductImage";
import { useWishlist } from "../context/WishlistContext";
import { useUser } from "../context/UserContext";

export default function ProductCard({ product, index = 0 }) {
  const { ids, toggle } = useWishlist();
  const { isAuthenticated } = useUser();
  const navigate = useNavigate();
  const isWishlisted = ids?.has(product.id);

  function handleWishlist(e) {
    e.preventDefault();
    if (!isAuthenticated) { navigate("/login"); return; }
    toggle(product.id);
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.4, delay: (index % 4) * 0.05 }}
    >
      <Link to={`/product/${product.id}`} className="group block bg-white rounded-lg overflow-hidden border border-ink/5 hover:shadow-md transition-shadow">
        <div className="relative overflow-hidden aspect-[4/5]">
          <motion.div className="w-full h-full" whileHover={{ scale: 1.06 }} transition={{ duration: 0.4 }}>
            <ProductImage seed={product.id} className="w-full h-full" />
          </motion.div>

          {product.bargainingEnabled && (
            <div className="absolute top-2 left-2 flex items-center gap-1 bg-rani text-white text-[10px] font-semibold px-2 py-1 rounded">
              <Tag className="w-3 h-3" />
              Bargain
            </div>
          )}

          <motion.button
            whileTap={{ scale: 0.8 }}
            onClick={handleWishlist}
            className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/95 flex items-center justify-center shadow-sm"
          >
            <Heart className={`w-4 h-4 transition-colors ${isWishlisted ? "fill-rani text-rani" : "text-ink"}`} />
          </motion.button>
        </div>

        <div className="p-3">
          <p className="text-[11px] uppercase tracking-wide text-ink-soft/60 mb-0.5">{product.category}</p>
          <h3 className="text-sm font-medium text-ink mb-1 truncate group-hover:text-rani transition-colors">{product.name}</h3>

          {product.avgRating != null && (
            <div className="flex items-center gap-1 mb-1">
              <span className="flex items-center gap-0.5 bg-sage text-white text-[10px] font-semibold px-1.5 py-0.5 rounded">
                {product.avgRating} <Star className="w-2.5 h-2.5 fill-white" />
              </span>
              <span className="text-[11px] text-ink-soft/60">({product.reviewCount})</span>
            </div>
          )}

          <p className="font-semibold text-ink">₹{product.listedPrice.toLocaleString("en-IN")}</p>
        </div>
      </Link>
    </motion.div>
  );
}
