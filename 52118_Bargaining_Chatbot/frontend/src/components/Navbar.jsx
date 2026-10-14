import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { ShoppingBag, Sparkles, LogOut, Store, ShieldCheck, User, Search, Heart, MapPin } from "lucide-react";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { useUser } from "../context/UserContext";
import { useWishlist } from "../context/WishlistContext";
import { api } from "../lib/api";

export default function Navbar() {
  const { isAuthenticated, user, logout } = useUser();
  const { ids: wishlistIds } = useWishlist();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [lockCount, setLockCount] = useState(0);
  const [cartCount, setCartCount] = useState(0);
  const [query, setQuery] = useState(searchParams.get("q") || "");
  const wishlistCount = wishlistIds?.size || 0;

  useEffect(() => {
    if (!isAuthenticated || user?.role !== "customer") { setLockCount(0); setCartCount(0); return; }
    let mounted = true;
    const poll = () => {
      api.getLocks().then((locks) => { if (mounted) setLockCount(locks.filter((l) => l.status === "active").length); }).catch(() => {});
      api.getCartItems().then((items) => { if (mounted) setCartCount(items.reduce((s, i) => s + i.quantity, 0)); }).catch(() => {});
    };
    poll();
    const t = setInterval(poll, 4000);
    return () => { mounted = false; clearInterval(t); };
  }, [isAuthenticated, user]);

  function handleSearch(e) {
    e.preventDefault();
    navigate(query.trim() ? `/?q=${encodeURIComponent(query.trim())}` : "/");
  }

  return (
    <header className="sticky top-0 z-50">
      {/* Top bar: logo, search, location, account, wishlist, cart */}
      <div className="bg-ink">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 rounded-md bg-marigold flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-ink" />
            </div>
            <span className="font-display font-extrabold text-xl text-ivory tracking-tight hidden sm:block">bazaaro</span>
          </Link>

          <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
            <div className="flex items-center bg-ivory rounded-md overflow-hidden">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search for shirts, kurtas, dresses and more"
                className="flex-1 px-3 py-2 text-sm text-ink outline-none"
              />
              <button type="submit" className="bg-marigold px-4 py-2.5 flex items-center justify-center">
                <Search className="w-4 h-4 text-ink" />
              </button>
            </div>
          </form>

          <div className="hidden lg:flex items-center gap-1 text-ivory/80 text-xs shrink-0">
            <MapPin className="w-4 h-4" />
            <div className="leading-tight">
              <p className="text-ivory/50">Deliver to</p>
              <p className="font-medium text-ivory">India</p>
            </div>
          </div>

          <div className="flex items-center gap-1 sm:gap-3 shrink-0">
            {isAuthenticated ? (
              <div className="flex items-center gap-1 sm:gap-3">
                <span className="hidden md:flex items-center gap-1 text-xs text-ivory/80">
                  <User className="w-4 h-4" />{user?.name?.split(" ")[0]}
                </span>
                <motion.button whileTap={{ scale: 0.9 }} onClick={() => { logout(); navigate("/"); }} className="p-2 rounded-md hover:bg-ivory/10" title="Log out">
                  <LogOut className="w-5 h-5 text-ivory/80" strokeWidth={1.5} />
                </motion.button>
              </div>
            ) : (
              <Link to="/login" className="bg-marigold text-ink text-xs sm:text-sm px-3 sm:px-4 py-2 rounded-md font-semibold whitespace-nowrap">Log In</Link>
            )}

            {isAuthenticated && user?.role === "customer" && (
              <>
                <Link to="/wishlist" className="relative p-2 rounded-md hover:bg-ivory/10">
                  <Heart className="w-5 h-5 text-ivory/80" strokeWidth={1.5} />
                  {wishlistCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-rani text-white text-[10px] flex items-center justify-center font-semibold">{wishlistCount}</span>
                  )}
                </Link>
                <Link to="/cart" className="relative p-2 rounded-md hover:bg-ivory/10">
                  <ShoppingBag className="w-5 h-5 text-ivory/80" strokeWidth={1.5} />
                  {cartCount > 0 && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-marigold text-ink text-[10px] flex items-center justify-center font-semibold">{cartCount}</span>
                  )}
                </Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Second bar: category links */}
      <div className="bg-ink/95 border-b border-ivory/10">
        <div className="max-w-7xl mx-auto px-4 h-11 flex items-center gap-6 overflow-x-auto">
          <Link to="/?gender=men" className="text-xs sm:text-sm text-ivory/90 hover:text-marigold whitespace-nowrap transition-colors">Men</Link>
          <Link to="/?gender=women" className="text-xs sm:text-sm text-ivory/90 hover:text-marigold whitespace-nowrap transition-colors">Women</Link>
          {isAuthenticated && user?.role === "customer" && (
            <Link to="/deals" className="relative text-xs sm:text-sm text-ivory/90 hover:text-marigold whitespace-nowrap transition-colors font-medium">
              My Deals
              {lockCount > 0 && <span className="ml-1 inline-flex w-4 h-4 rounded-full bg-rani text-white text-[10px] items-center justify-center align-middle">{lockCount}</span>}
            </Link>
          )}
          {isAuthenticated && user?.role === "seller" && (
            <Link to="/seller" className="text-xs sm:text-sm text-ivory/90 hover:text-marigold whitespace-nowrap flex items-center gap-1"><Store className="w-3.5 h-3.5" /> Seller Dashboard</Link>
          )}
          {isAuthenticated && user?.role === "admin" && (
            <Link to="/admin" className="text-xs sm:text-sm text-ivory/90 hover:text-marigold whitespace-nowrap flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5" /> Admin</Link>
          )}
        </div>
      </div>
    </header>
  );
}
