import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import { SearchX } from "lucide-react";
import Hero from "../components/Hero";
import ProductCard from "../components/ProductCard";
import { api } from "../lib/api";

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const gender = searchParams.get("gender") || "";
  const query = searchParams.get("q") || "";
  const [allProducts, setAllProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getProducts(gender ? { gender } : {}).then((data) => {
      setAllProducts(data);
      setLoading(false);
    });
  }, [gender]);

  const products = query
    ? allProducts.filter((p) =>
        `${p.name} ${p.category} ${p.fabric}`.toLowerCase().includes(query.toLowerCase())
      )
    : allProducts;

  return (
    <div>
      {!query && <Hero />}

      <section id="catalog" className="max-w-6xl mx-auto px-6 pb-24 pt-8">
        <div className="flex items-center justify-between mb-10 flex-wrap gap-4">
          <h2 className="font-display text-2xl font-bold text-ink">
            {query
              ? `Results for "${query}"`
              : gender
              ? `${gender[0].toUpperCase()}${gender.slice(1)}'s Edit`
              : "The Full Edit"}
          </h2>
          <div className="flex gap-2">
            {["", "men", "women"].map((g) => (
              <motion.button
                key={g || "all"}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSearchParams(g ? { gender: g } : {})}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  gender === g && !query ? "bg-ink text-ivory" : "bg-white text-ink-soft hover:bg-ink/5"
                }`}
              >
                {g ? `${g[0].toUpperCase()}${g.slice(1)}` : "All"}
              </motion.button>
            ))}
          </div>
        </div>

        {loading ? (
          <p className="text-ink-soft">Loading the edit...</p>
        ) : products.length === 0 ? (
          <div className="text-center py-20 bg-white rounded-2xl">
            <SearchX className="w-10 h-10 text-ink-soft/40 mx-auto mb-4" />
            <p className="text-ink-soft">No products found{query ? ` for "${query}"` : ""}.</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-x-4 gap-y-8">
            {products.map((p, i) => (
              <ProductCard key={p.id} product={p} index={i} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
