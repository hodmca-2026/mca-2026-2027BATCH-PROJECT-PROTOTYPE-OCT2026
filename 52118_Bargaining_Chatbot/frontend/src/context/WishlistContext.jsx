import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api } from "../lib/api";
import { useUser } from "./UserContext";

const WishlistContext = createContext(null);

export function WishlistProvider({ children }) {
  const { isAuthenticated, user } = useUser();
  const [ids, setIds] = useState(new Set());

  const refresh = useCallback(() => {
    if (!isAuthenticated || user?.role !== "customer") { setIds(new Set()); return; }
    api.getWishlist().then((items) => setIds(new Set(items.map((i) => i.productId)))).catch(() => {});
  }, [isAuthenticated, user]);

  useEffect(() => { refresh(); }, [refresh]);

  async function toggle(productId) {
    if (!isAuthenticated) return false;
    const has = ids.has(productId);
    setIds((prev) => {
      const next = new Set(prev);
      has ? next.delete(productId) : next.add(productId);
      return next;
    });
    try {
      if (has) await api.removeFromWishlist(productId);
      else await api.addToWishlist(productId);
      return true;
    } catch {
      refresh(); // revert optimistic update on failure
      return false;
    }
  }

  return (
    <WishlistContext.Provider value={{ ids, toggle, refresh }}>
      {children}
    </WishlistContext.Provider>
  );
}

export function useWishlist() {
  return useContext(WishlistContext);
}
